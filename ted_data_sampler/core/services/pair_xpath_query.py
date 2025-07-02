import logging
import re
from pathlib import Path
from typing import List
from math import ceil
import os
import multiprocessing
import gc

from pydantic import BaseModel
from tqdm import tqdm

from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator

PROJECT_PATH: Path = Path("/home/duprijil/work/ted-data-sampler")
INPUT_PATH_NOTICES: Path = Path("/home/duprijil/Downloads/test_notices")

OUTPUT_PATH: Path = PROJECT_PATH / "output" / "pair_xpaths"
OUTPUT_LOG_PATH: Path = OUTPUT_PATH / "logs.txt"
OUTPUT_NOTICES_PATH: Path = OUTPUT_PATH / "notices"

XPATHS_PATH: Path = PROJECT_PATH / "input" / "pair_xpaths.txt"

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


def get_pair_xpaths(pair_xpaths_file_path: Path) -> List[PairXPathQuery]:
    result_pair_xpath: List[PairXPathQuery] = []

    for line in pair_xpaths_file_path.read_text().splitlines():
        splited_xpaths = line.split("\t")
        result_pair_xpath.append(PairXPathQuery(xpath1=splited_xpaths[0], xpath2=splited_xpaths[1]))

    return result_pair_xpath


def is_xpath_exists_in_notice(xpath: str, xpath_validator: XPATHValidator) -> bool:
    try:
        result: list = xpath_validator.validate(xpath)
    except Exception:
        return False
    return True if len(result) > 0 else False


def process_chunk(chunk_data):
    """
    Process a chunk of notices with a progress bar

    Args:
        chunk_data: Tuple containing (chunk_id, chunk, paired_xpaths, output_dir)
    """
    chunk_id, chunk, paired_xpaths, output_dir = chunk_data

    # Set up logger
    logger = logging.getLogger(f"chunk_{chunk_id}")
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Create progress bar
    with tqdm(total=len(chunk), desc=f"Chunk {chunk_id}", position=chunk_id, leave=True) as pbar:
        for notice_path in chunk:
            try:
                # Read notice
                notice_text = Path(notice_path).read_text()

                # Create validator
                xpath_validator = XPATHValidator(xml_content=notice_text, logger=None)

                # Check XPaths
                for xpath1, xpath2 in paired_xpaths:
                    if is_xpath_exists_in_notice(xpath1, xpath_validator) and not is_xpath_exists_in_notice(xpath2,
                                                                                                            xpath_validator):
                        logger.info(f"The XPath: {xpath1} was found in {Path(notice_path).name}")
                        (Path(output_dir) / Path(notice_path).name).write_text(notice_text)
                        break

                # Clean up
                del xpath_validator
                del notice_text

                # Update progress
                pbar.update(1)

                # Garbage collect periodically
                if pbar.n % 100 == 0:
                    gc.collect()

            except Exception as e:
                logger.error(f"Error processing {notice_path}: {str(e)}")

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

    # Determine parallelism
    num_processes = min(4, os.cpu_count() or 1)
    logger.info(f"Using {num_processes} parallel processes")

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

    logger.info("All processes have finished. Processing completed")