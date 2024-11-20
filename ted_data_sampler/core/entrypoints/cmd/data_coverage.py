import argparse
import sys
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import List

from ted_sws.core.model.notice import Notice

from ted_data_sampler import STANDARD_TIME_FORMAT
from ted_data_sampler.core.entrypoints.cmd.data_sampler import DataSamplerException
from ted_data_sampler.core.services.logger import setup_logger
from ted_data_sampler.core.services.sample_data import sample_data_by_notice_source, store_eform_notices_by_sdk_version
from ted_data_sampler.core.services.xpath_coverage_service import run_coverage_over_sdk_versions


class DataCoverageException(Exception):
    """

    """

def get_list_of_strings_from_arg(arg):
    return arg.split(',')

def main():
    parser = argparse.ArgumentParser(description="Xpath coverage based on eforms sdk and stored notices.")
    parser.add_argument("-o", "--output", required=True, help="Path to the output folder.", type=str)
    parser.add_argument("-i", "--input_notices", required=True, help="Path to notices folder (recursive)", type=str)
    parser.add_argument("-n", "--sdk_versions", default="eforms", help="eforms or standard_forms", type=get_list_of_strings_from_arg)

    args = parser.parse_args()
    output_folder_path: Path = Path(args.output)
    notices_folder_path: Path = Path(args.input_notices)
    sdk_versions: List[str] = args.sdk_versions

    if not output_folder_path.is_dir():
        raise DataCoverageException(f"Folder {output_folder_path} does not exist")

    if not notices_folder_path.is_dir():
        raise DataCoverageException(f"File {notices_folder_path} does not exist")

    if not sdk_versions:
        raise DataCoverageException("No sdk_versions specified")

    run_path = output_folder_path / f"data_coverage_run_{datetime.now().strftime(STANDARD_TIME_FORMAT)}"
    run_path.mkdir(parents=True, exist_ok=True)

    # log_file_path = run_path / "logs.log"
    # log_file_io = log_file_path.open(mode="w", encoding="utf-8")
    # logger: Logger = setup_logger([sys.stdout, log_file_io])

    try:
        notice_folder_paths: List[Path] = [Path(notice_path) for notice_path in notices_folder_path.rglob("*.xml") ]
        run_coverage_over_sdk_versions(sdk_versions, output_folder_path, notice_folder_paths)
    except Exception as e:
        raise DataSamplerException(e)


if __name__ == "__main__":
    main()
