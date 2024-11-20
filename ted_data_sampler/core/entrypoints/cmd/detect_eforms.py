import argparse
from logging import Logger
from pathlib import Path

from future.moves import sys

from ted_data_sampler.core.services.detect_eforms import detect_and_save_eforms_notices_path
from ted_data_sampler.core.services.logger import setup_logger


class EformDetectorException(Exception):
    """"""

def main():
    parser = argparse.ArgumentParser(description="Detect eforms from folder of notices.")
    parser.add_argument("-o", "--output_file", required=True, help="Path to the output file.")
    parser.add_argument("-d", "--notices_folder", required=True, help="Path to all notices (recursive)")

    args = parser.parse_args()
    output_file_path = Path(args.output_file)
    notices_folder_path = Path(args.notices_folder)

    if not output_file_path.is_dir():
        raise EformDetectorException(f"Folder {output_file_path} does not exist")

    if not notices_folder_path.is_file():
        raise EformDetectorException(f"File {notices_folder_path} does not exist")


    logger: Logger = setup_logger([sys.stdout])

    try:
        detect_and_save_eforms_notices_path(notices_folder_path, output_file_path)
    except Exception as e:
        logger.error(e)
        raise EformDetectorException(e)


if __name__ == "__main__":
    main()
