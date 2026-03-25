import argparse
import sys
from pathlib import Path

from ted_data_sampler.core.services.download_notices import download_notices_range, parse_year_month_range
from ted_data_sampler.core.services.logger import setup_logger


class DownloadNoticesCLIException(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(description="Download TED notices from ted.europa.eu packages.")
    parser.add_argument("-o", "--output", required=True, help="Path to output folder.")
    parser.add_argument("-r", "--range", required=True, help="Year-month range (e.g., 2024:1-2025:6).")

    args = parser.parse_args()
    output_folder = Path(args.output)
    
    if output_folder.exists() and not output_folder.is_dir():
        raise DownloadNoticesCLIException(f"Output path exists but is not a folder: {output_folder}")

    try:
        parse_year_month_range(args.range)
    except Exception as e:
        raise DownloadNoticesCLIException(f"Invalid year-month range format: {e}")

    logger = setup_logger([sys.stdout])
    
    try:
        download_notices_range(
            output_folder=output_folder,
            year_month_range=args.range,
            logger=logger
        )
    except Exception as e:
        logger.error(e)
        raise DownloadNoticesCLIException(e)


if __name__ == "__main__":
    main()