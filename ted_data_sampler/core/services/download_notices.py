import logging
import os
import shutil
import tarfile
import urllib.request
from pathlib import Path
from typing import List, Tuple, Optional


class DownloadNoticesException(Exception):
    pass


def parse_year_month_range(range_str: str) -> List[Tuple[int, int]]:
    """
    Parse year-month range string like '2024:1-2025:6' to list of (year, month) tuples.
    
    Example: '2024:1-2025:6' -> [(2024,1), (2024,2), ..., (2025,6)]
    """
    parts = range_str.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid range format: {range_str}. Expected format: YYYY:M-YYYY:M")

    start_part, end_part = parts

    start_parts = start_part.split(":")
    if len(start_parts) != 2:
        raise ValueError(f"Invalid start format: {start_part}. Expected format: YYYY:M")
    start_year = int(start_parts[0])
    start_month = int(start_parts[1])

    end_parts = end_part.split(":")
    if len(end_parts) != 2:
        raise ValueError(f"Invalid end format: {end_part}. Expected format: YYYY:M")
    end_year = int(end_parts[0])
    end_month = int(end_parts[1])

    if not (1 <= start_month <= 12) or not (1 <= end_month <= 12):
        raise ValueError("Month must be between 1 and 12")

    if end_year < start_year:
        raise ValueError("End year must be smaller then start year")

    result = []
    current_year = start_year
    current_month = start_month

    while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
        result.append((current_year, current_month))
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    return result


def get_download_url(year: int, month: int) -> str:
    """Construct the download URL for a specific year/month."""
    return f"https://ted.europa.eu/packages/monthly/{year}-{month:02d}"


def flatten_extracted_files(month_folder: Path) -> None:
    """
    The outer tar.gz contains subfolders (01, 02, etc.) with inner tar.gz files.
    Extract nested tar.gz files and move XML files up to month_folder.
    """
    for subfolder in month_folder.iterdir():
        if subfolder.is_dir():
            for tar_file in subfolder.glob("*.tar.gz"):
                try:
                    with tarfile.open(tar_file, "r:gz") as inner_tar:
                        inner_tar.extractall(path=month_folder)
                    tar_file.unlink()
                except Exception:
                    pass

            for file in subfolder.iterdir():
                if file.is_file() and file.suffix == ".xml":
                    shutil.move(str(file), str(month_folder) + "/")
            try:
                os.rmdir(subfolder)
            except OSError:
                pass

    for subfolder in month_folder.iterdir():
        if subfolder.is_dir():
            for file in subfolder.iterdir():
                if file.is_file() and file.suffix == ".xml":
                    shutil.move(str(file), str(month_folder) + "/")
            try:
                os.rmdir(subfolder)
            except OSError:
                pass


def download_monthly_notices(year: int, month: int, output_path: Path, logger: logging.Logger) -> bool:
    """
    Download and extract monthly notices for a specific year and month.
    
    :param year: Year (e.g., 2024)
    :param month: Month (1-12)
    :param output_path: Base output path
    :param logger: Logger instance
    :return: True if successful or skipped, False on error
    """
    month_folder = output_path / str(year) / f"{month:02d}"

    if month_folder.is_dir() and any(month_folder.glob("*.xml")):
        logger.info(f"Skipping {year}-{month:02d}: folder already exists with XML files")
        return True

    month_folder.mkdir(parents=True, exist_ok=True)

    url = get_download_url(year, month)
    archive_path = month_folder / f"{year}-{month:02d}.tar.gz"

    logger.info(f"Downloading {year}-{month:02d} from {url}")

    try:
        urllib.request.urlretrieve(url, archive_path)

        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=month_folder)

        archive_path.unlink()

        flatten_extracted_files(month_folder)

        if month_folder.exists() and any(month_folder.iterdir()):
            logger.info(f"Extracted {year}-{month:02d} to {month_folder}")
            return True
        else:
            logger.warning(f"No files found after extraction for {year}-{month:02d}")
            return False

    except Exception as e:
        logger.error(f"Error downloading {year}-{month:02d}: {str(e)}")
        if archive_path.exists():
            archive_path.unlink()
        return False


def download_notices_range(
        output_folder: Path,
        year_month_range: str,
        logger: Optional[logging.Logger] = None
) -> None:
    """
    Download and extract notices for a range of years and months.
    
    :param output_folder: Base output folder (NOTICES_INPUT_FOLDER)
    :param year_month_range: Year-month range string (e.g., "2024:1-2025:6")
    :param logger: Logger instance
    """
    year_month_list = parse_year_month_range(year_month_range)

    output_folder.mkdir(parents=True, exist_ok=True)

    log_file_path = output_folder / "logs.log"

    if logger is None:
        logger = logging.getLogger(__name__)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
    else:
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    logger.info(f"Downloading notices for range: {year_month_range} ({len(year_month_list)} months)")

    success_count = 0
    skip_count = 0
    error_count = 0

    for year, month in year_month_list:
        result = download_monthly_notices(year, month, output_folder, logger)
        if result:
            month_folder = output_folder / str(year) / f"{month:02d}"
            if month_folder.exists() and any(month_folder.iterdir()):
                success_count += 1
            else:
                skip_count += 1
        else:
            error_count += 1

    logger.info(f"Download complete: {success_count} downloaded, {skip_count} skipped, {error_count} errors")
