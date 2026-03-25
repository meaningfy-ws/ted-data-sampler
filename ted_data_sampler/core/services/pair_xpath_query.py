import gc
import logging
import multiprocessing
import os
import re
import time
from math import ceil
from pathlib import Path
from typing import List, Tuple

import psutil
from pydantic import BaseModel
from tqdm import tqdm

from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator

PROJECT_PATH: Path = Path("--PATH--")
INPUT_PATH_NOTICES: Path = Path("--PATH--")

OUTPUT_PATH: Path = PROJECT_PATH / "output" / "pair_xpaths"
OUTPUT_LOG_PATH: Path = OUTPUT_PATH / "logs.txt"
OUTPUT_NOTICES_PATH: Path = OUTPUT_PATH / "notices"

XPATHS_PATH: Path = PROJECT_PATH / "input" / "pair_xpaths.txt"

# Memory configuration
MEMORY_LIMIT_MB = 4000  # Adjust based on your system
BATCH_SIZE = 1000  # Number of notices to process before forced cleanup

# Multiprocessing configuration
NUM_PROCESSES = 8  # Number of processes per pool
MAJOR_CHUNKS = 8  # Number of sequential batches to process

# File handler
file_handler = logging.FileHandler(str(OUTPUT_LOG_PATH))
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)


class PairXPathQuery(BaseModel):
    xpath1: str
    xpath2: str


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_optimal_process_count() -> int:
    """Calculate optimal process count based on system memory."""
    total_memory_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)
    # Allocate ~2GB per process
    optimal_count = max(1, int(total_memory_gb / 2))
    # Still respect CPU count
    return min(optimal_count, os.cpu_count() or 1)


def get_pair_xpaths(pair_xpaths_file_path: Path) -> List[PairXPathQuery]:
    """Read XPath pairs from file."""
    result_pair_xpath: List[PairXPathQuery] = []

    for line in pair_xpaths_file_path.read_text().splitlines():
        splited_xpaths = line.split("\t")
        if len(splited_xpaths) >= 2:
            result_pair_xpath.append(PairXPathQuery(xpath1=splited_xpaths[0], xpath2=splited_xpaths[1]))

    return result_pair_xpath


def is_xpath_exists_in_notice(xpath: str, xpath_validator: XPATHValidator) -> bool:
    """Check if an XPath exists in a notice."""
    try:
        result: list = xpath_validator.validate(xpath)
    except Exception:
        return False
    return True if len(result) > 0 else False


def process_notice(notice_path: str, xpath_validator: XPATHValidator,
                   paired_xpaths: List[Tuple[str, str]],
                   output_dir: str, logger: logging.Logger) -> bool:
    """Process a single notice."""
    try:
        # Read notice
        with open(notice_path, 'r') as f:
            notice_text = f.read()

        # Reset validator with new content
        xpath_validator.reset_with_new_content(notice_text)

        # Check XPaths
        for xpath1, xpath2 in paired_xpaths:
            if is_xpath_exists_in_notice(xpath1, xpath_validator) and not is_xpath_exists_in_notice(xpath2,
                                                                                                    xpath_validator):
                logger.info(f"The XPath: {xpath1} was found in {Path(notice_path).name}")
                with open(str(Path(output_dir) / Path(notice_path).name), 'w') as f:
                    f.write(notice_text)
                return True

        return False
    except Exception as e:
        logger.error(f"Error processing {notice_path}: {str(e)}")
        return False


def safe_close_validator(validator, logger):
    """Safely close the validator object, handling any attribute errors."""
    try:
        validator.close()
    except AttributeError as e:
        logger.warning(f"Could not close validator properly: {str(e)}")
    except Exception as e:
        logger.error(f"Error closing validator: {str(e)}")


def process_chunk(chunk_data):
    """
    Process a chunk of notices with memory management

    Args:
        chunk_data: Tuple containing (chunk_id, chunk, paired_xpaths, output_dir)
    """
    chunk_id, chunk, paired_xpaths, output_dir = chunk_data

    # Set up logger
    logger = logging.getLogger(f"chunk_{chunk_id}")
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Create a single validator instance for reuse
    xpath_validator = XPATHValidator(xml_content="<root/>", logger=logger)

    # Track memory usage
    initial_memory = get_memory_usage_mb()
    logger.info(f"Chunk {chunk_id} starting with {initial_memory:.2f} MB memory usage")

    try:
        # Create progress bar
        with tqdm(total=len(chunk), desc=f"Chunk {chunk_id}", position=chunk_id, leave=True) as pbar:
            # Process in smaller batches
            for i in range(0, len(chunk), BATCH_SIZE):
                # Check memory before processing batch
                current_memory = get_memory_usage_mb()
                if current_memory > MEMORY_LIMIT_MB:
                    logger.warning(f"High memory usage ({current_memory:.2f} MB). Forcing cleanup.")
                    gc.collect()

                # Get current batch
                sub_chunk = chunk[i:i + BATCH_SIZE]

                # Process each notice in the batch
                for notice_path in sub_chunk:
                    process_notice(notice_path, xpath_validator, paired_xpaths, output_dir, logger)
                    pbar.update(1)

                # Force cleanup after each batch
                gc.collect()
    except Exception as e:
        logger.error(f"Error in chunk {chunk_id}: {str(e)}")
    finally:
        # Clean up validator - safely close it
        # logger.info(f"Cleaning up validator for chunk {chunk_id}")
        safe_close_validator(xpath_validator, logger)
        del xpath_validator
        gc.collect()

        # Log final memory usage
        final_memory = get_memory_usage_mb()
        logger.info(
            f"Chunk {chunk_id} finished with {final_memory:.2f} MB memory usage (change: {final_memory - initial_memory:.2f} MB)")

    return True


def split_into_chunks(items: List, num_chunks: int) -> List[List]:
    """Split a list into a specified number of chunks of approximately equal size"""
    chunk_size = ceil(len(items) / num_chunks)
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def process_in_batches(notices: List[str], paired_xpaths: List[Tuple[str, str]],
                       output_dir: str, logger: logging.Logger):
    """
    Process notices in sequential batches of multiprocessing pools
    to manage memory more effectively.

    Args:
        notices: List of notice file paths
        paired_xpaths: List of XPath pairs to check
        output_dir: Directory to save matching notices
        logger: Logger instance
    """
    # Split all notices into major chunks that will be processed sequentially
    major_chunks = split_into_chunks(notices, MAJOR_CHUNKS)
    logger.info(f"Split all notices into {len(major_chunks)} major chunks for sequential processing")

    for major_idx, major_chunk in enumerate(major_chunks):
        logger.info(f"Processing major chunk {major_idx + 1}/{len(major_chunks)} with {len(major_chunk)} notices")
        logger.info(f"Memory before processing: {get_memory_usage_mb():.2f} MB")

        # For each major chunk, create a separate multiprocessing pool
        # Split the major chunk into smaller chunks for parallel processing
        sub_chunks = split_into_chunks(major_chunk, NUM_PROCESSES)

        # Prepare chunk data
        chunk_data = [
            (i, chunk, paired_xpaths, output_dir)
            for i, chunk in enumerate(sub_chunks)
        ]

        # Create process pool and run for this major chunk
        with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
            try:
                results = pool.map(process_chunk, chunk_data)
            except Exception as e:
                logger.error(f"Error in pool.map: {str(e)}")
                # Force pool termination in case of error
                pool.terminate()
                # Wait a moment before continuing
                time.sleep(2)
                continue

        # Explicitly close and join the pool
        pool.close()
        pool.join()

        # Force cleanup after processing this major chunk
        gc.collect()

        # Log memory usage after this major chunk
        # logger.info(f"Major chunk {major_idx + 1} completed. Memory after processing: {get_memory_usage_mb():.2f} MB")

        # Additional memory cleanup
        time.sleep(1)  # Give OS a moment to reclaim memory
        gc.collect()


def process_notices(logger: logging.Logger):
    """Main function to process notices"""
    logger.info("Starting notice collection...")
    logger.info(f"Initial memory usage: {get_memory_usage_mb():.2f} MB")

    # Find notices
    eform_pattern = re.compile(r"^\d{8}_\d{4}\.xml$")
    all_notice_count = 0
    eform_notice_folder_paths = []

    for notice_path in INPUT_PATH_NOTICES.rglob("*.xml"):
        all_notice_count += 1
        if eform_pattern.match(notice_path.name):
            eform_notice_folder_paths.append(str(notice_path))

    # Get XPath pairs
    paired_xpaths = get_pair_xpaths(XPATHS_PATH)
    paired_xpaths_plain = [(px.xpath1, px.xpath2) for px in paired_xpaths]

    logger.info(f"Total number of found notices: {all_notice_count}")
    logger.info(f"Querying {len(eform_notice_folder_paths)} eForms notices")
    logger.info(f"Number of xpaths pairs: {len(paired_xpaths)}")

    # Process notices in batches with hierarchical multiprocessing
    process_in_batches(
        notices=eform_notice_folder_paths,
        paired_xpaths=paired_xpaths_plain,
        output_dir=str(OUTPUT_NOTICES_PATH),
        logger=logger
    )

    # Final memory usage check
    logger.info(f"Final memory usage: {get_memory_usage_mb():.2f} MB")
    logger.info("All processes have finished. Processing completed")
