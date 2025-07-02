import logging
import re
from pathlib import Path
from typing import List
from math import ceil
import os  # For os.cpu_count()

from pydantic import BaseModel
from tqdm import tqdm

from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator
from pqdm.processes import pqdm  # Using pqdm instead of p_tqdm

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


def process_notice(notice_path: str, paired_xpaths: list, output_dir: str, logger):
    from pathlib import Path
    from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator

    notice_text = Path(notice_path).read_text()
    xpath_validator = XPATHValidator(xml_content=notice_text, logger=None)

    for xpath1, xpath2 in paired_xpaths:
        if is_xpath_exists_in_notice(xpath1, xpath_validator) and not is_xpath_exists_in_notice(xpath2,
                                                                                                xpath_validator):
            logger.info(f"The XPath: {xpath1} was found in {Path(notice_path).name}")
            (Path(output_dir) / Path(notice_path).name).write_text(notice_text)
            #break

    del xpath_validator


def process_chunk(args):
    """
    Process a chunk of notices with a progress bar

    Args:
        args: Tuple containing (chunk, paired_xpaths, output_dir, chunk_id)
    """
    chunk, paired_xpaths, output_dir, chunk_id = args
    results = []
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    for notice_path in tqdm(chunk, desc=f"Chunk {chunk_id}", position=chunk_id, leave=True):
        process_notice(notice_path, paired_xpaths, output_dir, logger)
        results.append(True)  # Just to track completion
    return results


def split_into_chunks(items: List, num_chunks: int) -> List[List]:
    """Split a list into a specified number of chunks of approximately equal size"""
    chunk_size = ceil(len(items) / num_chunks)
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


if __name__ == "__main__":


    OUTPUT_PATH.mkdir(exist_ok=True, parents=True)
    OUTPUT_NOTICES_PATH.mkdir(exist_ok=True, parents=True)
    OUTPUT_LOG_PATH.touch()

    # only eforms
    pattern = re.compile(r"^\d{8}_\d{4}\.xml$")

    all_notice_folder_paths: List[str] = [str(notice_path) for notice_path in INPUT_PATH_NOTICES.rglob("*.xml")]
    eform_notice_folder_paths: List[str] = [str(notice_path) for notice_path in INPUT_PATH_NOTICES.rglob("*.xml") if
                                      pattern.match(notice_path.name)]

    paired_xpaths: List[PairXPathQuery] = get_pair_xpaths(XPATHS_PATH)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


    logger.info(f"Total number of found notices: {len(all_notice_folder_paths)}")
    logger.info(f"Querying {len(eform_notice_folder_paths)} eForms notices")
    logger.info(f"Number of xpaths pairs: {len(paired_xpaths)}")

    # Convert to plain dicts or tuples
    paired_xpaths_plain = [(px.xpath1, px.xpath2) for px in paired_xpaths]

    # Determine number of chunks based on available CPUs
    num_processes = min(4, os.cpu_count() or 1)  # Use at most 4 processes or the number of CPUs available
    logger.info(f"Using {num_processes} parallel processes")

    # Split notices into chunks
    chunks = split_into_chunks(eform_notice_folder_paths, num_processes)
    logger.info(f"Split notices into {len(chunks)} chunks")

    # Prepare arguments for each chunk processor
    process_args = [
        (chunk, paired_xpaths_plain, str(OUTPUT_NOTICES_PATH), i)
        for i, chunk in enumerate(chunks)
    ]

    # Process each chunk in parallel with pqdm
    # This will display a progress bar for the overall processing
    results = pqdm(process_args, process_chunk, n_jobs=num_processes, desc="Overall Progress")

    logger.info("Processing completed")