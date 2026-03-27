import argparse
import sys
from datetime import datetime
from logging import Logger
from pathlib import Path

from ted_data_sampler import STANDARD_TIME_FORMAT
from ted_data_sampler.core.services.load_notices import load_notices_to_mongodb
from ted_data_sampler.core.services.logger import setup_logger


class LoadNoticesCLIException(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(description="Load XML notices from folder to MongoDB.")
    parser.add_argument("-i", "--input", required=True, help="Path to input folder with XML files.")
    parser.add_argument("-o", "--output", required=False, default=None,
                        help="Path to output folder for logs. Defaults to current working directory.")

    args = parser.parse_args()
    input_folder_path = Path(args.input)

    if not input_folder_path.is_dir():
        raise LoadNoticesCLIException(f"Input folder does not exist: {input_folder_path}")

    output_folder_path = Path(args.output) if args.output else Path.cwd()
    run_path = output_folder_path / f"load_notices_run_{datetime.now().strftime(STANDARD_TIME_FORMAT)}"
    run_path.mkdir(parents=True, exist_ok=True)

    log_file_path = run_path / "logs.log"
    log_file_io = log_file_path.open(mode="w", encoding="utf-8")
    logger: Logger = setup_logger([sys.stdout, log_file_io])

    try:
        load_notices_to_mongodb(input_folder=input_folder_path, logger=logger)
    except Exception as e:
        logger.error(e)
        raise LoadNoticesCLIException(e)
    finally:
        log_file_io.close()


if __name__ == "__main__":
    main()