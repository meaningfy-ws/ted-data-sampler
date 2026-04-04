import logging
import sys
from logging import Logger
from pathlib import Path
from typing import Optional, Set, TextIO

from tqdm import tqdm

from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator
from ted_data_sampler.core.services.logger import setup_logger
from ted_data_sampler.minimal_set.models.missing_xpath import MissingXPathEntry
from ted_data_sampler.minimal_set.models.gap_filler_result import GapFillerResult
from ted_data_sampler.minimal_set.services.missing_xpath_loader import load_missing_xpaths
from ted_data_sampler.minimal_set.services.candidate_discovery import discover_candidates
from ted_data_sampler.minimal_set.services.conditional_xpath_validator import validate_entry
from ted_data_sampler.minimal_set.services.cross_coverage import build_cross_coverage


def fill_gaps(
    entries: list[MissingXPathEntry],
    notice_paths: list[str],
    exclude_paths: Optional[Set[str]] = None,
    logger: Optional[Logger] = None,
    output_path: Optional[Path] = None,
    tqdm_file: Optional[TextIO] = None
) -> GapFillerResult:
    """
    Main entry point for the Pass 2 gap filler algorithm.

    Finds the minimum set of notices that cover all missing XPath entries
    using a greedy set-cover algorithm with cross-coverage optimization.

    Args:
        entries: List of missing XPath entries to cover.
        notice_paths: List of file paths to XML notice files.
        exclude_paths: Optional set of notice paths to exclude from selection
            (e.g., notices already selected in Pass 1).
        logger: Optional logger for progress messages.
        output_path: Optional path to save results immediately after processing.
        tqdm_file: Optional file handle for tqdm progress output.

    Returns:
        GapFillerResult containing selected notices, coverage mapping, and
        any unresolved entries.
    """
    if logger is None:
        logger = setup_logger([sys.stdout])
    if exclude_paths is None:
        exclude_paths = set()

    entry_lookup: dict[str, MissingXPathEntry] = {e.sdk_element_id: e for e in entries}

    pool = sorted(entries, key=lambda e: (-len(e.iterator_xpath), len(e.absolute_xpath)))
    logger.info(f"Pool sorted: {len(pool)} entries to cover")

    candidates = discover_candidates(pool, notice_paths, logger, tqdm_file)

    cross_coverage = build_cross_coverage(pool, candidates, logger)
    sorted_candidates = cross_coverage.sorted_candidates
    notice_to_entries = cross_coverage.notice_to_entries

    selected_notices: list[str] = []
    coverage: dict[str, list[str]] = {}
    covered_ids: Set[str] = set()

    for entry in tqdm(pool, desc="Greedy selection", file=tqdm_file, mininterval=5):
        if entry.sdk_element_id in covered_ids:
            continue

        entry_candidates = sorted_candidates.get(entry.sdk_element_id, [])

        for notice_path in entry_candidates:
            if notice_path in selected_notices or notice_path in exclude_paths:
                continue

            try:
                xml_content = Path(notice_path).read_text(encoding="utf-8")
                validator = XPATHValidator(xml_content=xml_content, logger=logger)
            except Exception as e:
                logger.warning(f"Could not parse {notice_path}: {e}")
                continue

            logger.debug(
                f"Trying {Path(notice_path).name} for {entry.sdk_element_id}"
            )

            if validate_entry(validator, entry, logger):
                selected_notices.append(notice_path)
                notice_covered = [entry.sdk_element_id]
                covered_ids.add(entry.sdk_element_id)
                logger.info(
                    f"Selected {Path(notice_path).name} -> {entry.sdk_element_id}"
                )

                for other_id in notice_to_entries.get(notice_path, []):
                    if other_id in covered_ids:
                        continue
                    other_entry = entry_lookup.get(other_id)
                    if other_entry is None:
                        continue
                    if validate_entry(validator, other_entry, logger):
                        covered_ids.add(other_id)
                        notice_covered.append(other_id)
                        logger.info(
                            f"  Also covers {other_id}"
                        )

                coverage[notice_path] = notice_covered
                validator.close()
                break
            else:
                validator.close()

    unresolved = [e.sdk_element_id for e in pool if e.sdk_element_id not in covered_ids]

    logger.info(
        f"Done: {len(selected_notices)} notices selected, "
        f"{len(covered_ids)} entries covered, "
        f"{len(unresolved)} unresolved"
    )

    result = GapFillerResult(
        selected_notices=selected_notices,
        coverage=coverage,
        unresolved_entries=unresolved
    )

    if output_path:
        result.save(output_path)
        logger.info(f"Results saved to {output_path}")

    return result
