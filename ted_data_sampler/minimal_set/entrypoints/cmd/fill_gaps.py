import argparse
import sys
from pathlib import Path

from ted_data_sampler.core.services.logger import setup_logger
from ted_data_sampler.minimal_set.models.gap_filler_result import GapFillerResult
from ted_data_sampler.minimal_set.services.missing_xpath_loader import load_missing_xpaths
from ted_data_sampler.minimal_set.services.gap_filler import fill_gaps


class FillGapsCLIException(Exception):
    """Exception raised when CLI arguments are invalid or processing fails."""
    pass


def main():
    """
    CLI entry point for the Pass 2 gap filler algorithm.

    Finds supplementary notices that cover missing/uncovered XPaths from the
    Mapping Workbench. Uses a greedy set-cover algorithm with cross-coverage
    optimization and two-stage XPath validation.

    Arguments:
        -x, --xpaths: Path to JSON file with missing XPath entries
        -n, --notices: Path to text file with notice paths (one per line)
        -e, --exclude: Optional path to text file with already-selected notice
                       paths to exclude (e.g., from Pass 1)
        -o, --output: Path to output folder for results

    Output files (created in output folder):
        - result_notices.txt: Selected notice paths
        - remaining_uncovered.txt: Entry IDs that could not be covered
        - coverage_report.json: Detailed coverage mapping and summary
        - logs.log: Runtime log messages
    """
    parser = argparse.ArgumentParser(
        description="Find supplementary notices that cover missing/uncovered XPaths."
    )
    parser.add_argument("-x", "--xpaths", required=True,
                        help="Path to JSON file with missing XPath entries.")
    parser.add_argument("-n", "--notices", required=True,
                        help="Path to text file with notice paths (one per line).")
    parser.add_argument("-e", "--exclude", required=False, default=None,
                        help="Path to text file with already-selected notice paths to exclude.")
    parser.add_argument("-o", "--output", required=True,
                        help="Path to output folder for the results.")

    args = parser.parse_args()
    xpaths_path = Path(args.xpaths)
    notices_path = Path(args.notices)
    output_path = Path(args.output)

    if not xpaths_path.is_file():
        raise FillGapsCLIException(f"XPaths file does not exist: {xpaths_path}")
    if not notices_path.is_file():
        raise FillGapsCLIException(f"Notices file does not exist: {notices_path}")

    output_path.mkdir(parents=True, exist_ok=True)
    log_file = open(output_path / "logs.log", mode="w", encoding="utf-8")
    logger = setup_logger([sys.stdout, log_file])

    try:
        entries = load_missing_xpaths(xpaths_path)
        logger.info(f"Loaded {len(entries)} missing XPath entries")

        notice_paths = [
            line.strip() for line in notices_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        logger.info(f"Loaded {len(notice_paths)} notice paths")

        exclude_paths = set()
        if args.exclude:
            exclude_path = Path(args.exclude)
            if exclude_path.is_file():
                exclude_paths = {
                    line.strip() for line in exclude_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                }
                logger.info(f"Excluding {len(exclude_paths)} already-selected notices")

        result = fill_gaps(entries, notice_paths, exclude_paths, logger, output_path, tqdm_file=log_file)

        logger.info(f"Selected {len(result.selected_notices)} notices")
        if result.unresolved_entries:
            logger.warning(f"{len(result.unresolved_entries)} entries could not be covered")

    except Exception as e:
        logger.error(e)
        raise FillGapsCLIException(e)
    finally:
        for handler in logger.handlers:
            handler.flush()
        log_file.close()
        sys.stdout.flush()


if __name__ == "__main__":
    main()
