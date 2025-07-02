import logging
import re
import time
import os
import gc
import psutil
from pathlib import Path
from typing import List, Tuple
from math import ceil
import multiprocessing
from pydantic import BaseModel
from tqdm import tqdm

from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator

PROJECT_PATH: Path = Path("/home/duprijil/work/ted-data-sampler")
INPUT_PATH_NOTICES: Path = Path("/home/duprijil/Downloads/test_notices")

OUTPUT_PATH: Path = PROJECT_PATH / "output" / "pair_xpaths"
OUTPUT_LOG_PATH: Path = OUTPUT_PATH / "logs.txt"
OUTPUT_NOTICES_PATH: Path = OUTPUT_PATH / "notices"

XPATHS_PATH: Path = PROJECT_PATH / "input" / "pair_xpaths.txt"

# Memory configuration
MEMORY_LIMIT_MB = 4000  # Adjust based on your system
BATCH_SIZE = 1000  # Number of notices to process before forced cleanup

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
                    #time.sleep(1)  # Give OS time to reclaim memory

                    # If still too high, skip some notices
                    # if get_memory_usage_mb() > MEMORY_LIMIT_MB * 1.2:
                    #     skip_count = min(BATCH_SIZE * 2, len(chunk) - pbar.n)
                    #     logger.warning(f"Memory still too high. Skipping {skip_count} notices.")
                    #     pbar.update(skip_count)
                    #     i += skip_count
                    #     continue

                # Get current batch
                sub_chunk = chunk[i:i + BATCH_SIZE]

                # Process each notice in the batch
                for notice_path in sub_chunk:
                    process_notice(notice_path, xpath_validator, paired_xpaths, output_dir, logger)
                    pbar.update(1)

                # Force cleanup after each batch
                gc.collect()

                # Log memory usage periodically
                # if i % (BATCH_SIZE * 5) == 0:
                #     logger.info(f"Memory usage after {pbar.n}/{len(chunk)} notices: {get_memory_usage_mb():.2f} MB")
    except Exception as e:
        logger.error(f"Error in chunk {chunk_id}: {str(e)}")
    finally:
        # Clean up validator
        logger.info(f"Cleaning up validator for chunk {chunk_id}")
        xpath_validator.close()
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


if __name__ == "__main__":
    # Fix import path
    import sys

    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    # Create output directories
    OUTPUT_PATH.mkdir(exist_ok=True, parents=True)
    OUTPUT_NOTICES_PATH.mkdir(exist_ok=True, parents=True)
    OUTPUT_LOG_PATH.touch()

    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

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

    # Determine parallelism based on available memory
    num_processes = 8 #get_optimal_process_count()
    logger.info(f"Using {num_processes} parallel processes based on available memory")

    # Split notices into chunks
    chunks = split_into_chunks(eform_notice_folder_paths, num_processes)
    logger.info(f"Split notices into {len(chunks)} chunks")

    # Prepare chunk data
    chunk_data = [
        (i, chunk, paired_xpaths_plain, str(OUTPUT_NOTICES_PATH))
        for i, chunk in enumerate(chunks)
    ]

    logger.info("Starting parallel processing")

    # Create process pool and run
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(process_chunk, chunk_data)

    # Final memory usage check
    logger.info(f"Final memory usage: {get_memory_usage_mb():.2f} MB")
    logger.info("All processes have finished. Processing completed")