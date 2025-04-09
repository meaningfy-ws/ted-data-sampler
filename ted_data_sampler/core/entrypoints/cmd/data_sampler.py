import argparse
import sys
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import List

from ted_sws.core.model.notice import Notice

from ted_data_sampler import STANDARD_TIME_FORMAT
from ted_data_sampler.core.services.logger import setup_logger
from ted_data_sampler.core.services.sample_data import sample_data_by_notice_source, store_eform_notices_by_sdk_version, \
    store_eform_notices_by_sdk_version_type_subtype


class DataSamplerException(Exception):
    """

    """


def main():
    parser = argparse.ArgumentParser(description="Data sampler generator based on MongoDB data.")
    parser.add_argument("-o", "--output", required=True, help="Path to the output folder.")
    parser.add_argument("-d", "--dot_env_file", required=True, help="Path to .env file")
    parser.add_argument("-n", "--notice_source", default="eforms", help="eforms or standard_forms")

    args = parser.parse_args()
    output_file_path = Path(args.output)
    dot_env_file_path = Path(args.dot_env_file)
    notice_source = args.notice_source

    if not output_file_path.is_dir():
        raise DataSamplerException(f"File {output_file_path} does not exist")

    if not dot_env_file_path.is_file():
        raise DataSamplerException(f"File {dot_env_file_path} does not exist")

    run_path = output_file_path / f"data_sampler_run_{datetime.now().strftime(STANDARD_TIME_FORMAT)}"
    run_path.mkdir(parents=True, exist_ok=True)

    log_file_path = run_path / "logs.log"
    log_file_io = log_file_path.open(mode="w", encoding="utf-8")
    logger: Logger = setup_logger([sys.stdout, log_file_io])

    try:
        result_notices: List[Notice] = sample_data_by_notice_source(notice_source=notice_source, logger=logger)
        store_eform_notices_by_sdk_version_type_subtype(output_path=run_path, notices=result_notices, logger=logger)
    except Exception as e:
        logger.error(e)
        raise DataSamplerException(e)
    finally:
        log_file_io.close()


if __name__ == "__main__":
    main()
