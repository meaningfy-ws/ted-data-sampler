import sys
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import List

from tqdm import tqdm

from ted_data_sampler import STANDARD_TIME_FORMAT
from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator
from ted_data_sampler.core.services.import_eforms_fields import extract_xpaths_by_sdk_version
from ted_data_sampler.core.services.logger import execute_function_with_logging_execution_time
from ted_data_sampler.core.services.logger import setup_logger


def detect_uncovered_xpaths_of_sdk_from_stored_notices(sdk_version: str, xpaths: List[str], notices_path: List[Path],
                                                       logger: Logger = None) -> List[str]:
    if not logger:
        logger = setup_logger([sys.stdout])

    uncovered_xpaths = xpaths.copy()
    pbar = tqdm(total=len(uncovered_xpaths), desc=f"XPaths coverage for {sdk_version}", dynamic_ncols=True)
    for notice_path in notices_path:
        xpath_validator = XPATHValidator(xml_content=notice_path.read_text(), logger=logger)

        for xpath in uncovered_xpaths:
            try:
                validator_result = xpath_validator.validate(xpath)
            except Exception: #TODO: Temporary solution
                break
            if len(validator_result) > 0:
                uncovered_xpaths.remove(xpath)
                pbar.update(1)
                if len(uncovered_xpaths) == 0:
                    logger.info("All xpaths are covered")
                    return uncovered_xpaths

    return uncovered_xpaths


def run_coverage_over_sdk_versions(eform_sdk_versions: List[str], output_folder: Path,
                                   eform_notices_path: List[Path]) -> None:
    assert len(eform_sdk_versions) > 0
    assert output_folder.exists()
    assert len(eform_notices_path) > 0

    output_run_folder = output_folder / f"coverage_run_{datetime.now().strftime(STANDARD_TIME_FORMAT)}"
    output_run_folder.mkdir(parents=True, exist_ok=True)
    for eform_sdk_version in eform_sdk_versions:
        eform_output_path: Path = output_run_folder / f"{eform_sdk_version}"
        eform_output_path.mkdir(parents=True, exist_ok=True)
        log_file_path: Path = eform_output_path / f"run_logs.log"
        log_file = log_file_path.open(mode="w", encoding="utf-8")
        logger: Logger = setup_logger([log_file])

        sdk_xpaths = extract_xpaths_by_sdk_version(eform_sdk_version)
        (eform_output_path / "all_sdk_xpaths.txt").write_text("\n".join(sdk_xpaths))

        uncovered_xpaths: List[str] = execute_function_with_logging_execution_time(logger,
                                                                                   detect_uncovered_xpaths_of_sdk_from_stored_notices,
                                                                                   eform_sdk_version, sdk_xpaths,
                                                                                   eform_notices_path, logger)
        (eform_output_path / "uncovered_sdk_xpaths.txt").write_text("\n".join(uncovered_xpaths))
        covered_xpaths: List[str] = list(set(sdk_xpaths) - set(uncovered_xpaths))
        (eform_output_path / "covered_sdk_xpaths.txt").write_text("\n".join(covered_xpaths))

        logger.info(f"Coverage of xpaths in {eform_sdk_version} sdk version: {len(covered_xpaths)}/{len(sdk_xpaths)}")
