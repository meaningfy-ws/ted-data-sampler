import logging
import sys
from logging import Logger
from pathlib import Path
from typing import Optional, TextIO

from tqdm import tqdm

from ted_data_sampler.minimal_set.models.candidate_discovery_result import CandidateDiscoveryResult
from ted_data_sampler.minimal_set.models.missing_xpath import MissingXPathEntry


def discover_candidates(
    entries: list[MissingXPathEntry],
    notice_paths: list[str],
    logger: Optional[Logger] = None,
    tqdm_file: Optional[TextIO] = None
) -> CandidateDiscoveryResult:
    """
    Perform candidate discovery using fast raw text scanning.

    For each notice, reads the file as raw text and checks if all segments
    of abs_xpath_reduced appear anywhere in the text. This is a loose pre-filter
    that produces candidates - actual validation happens later with XPath queries.

    Args:
        entries: List of missing XPath entries to find candidates for.
        notice_paths: List of file paths to XML notice files.
        logger: Optional logger for progress messages.
        tqdm_file: Optional file handle for tqdm progress output.

    Returns:
        CandidateDiscoveryResult containing candidate mapping and statistics.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    candidate_notices: dict[str, list[str]] = {e.sdk_element_id: [] for e in entries}
    reduced_segments = {
        e.sdk_element_id: [s.strip() for s in e.abs_xpath_reduced.split('/') if s.strip()]
        for e in entries
    }

    logger.info(f"Scanning {len(notice_paths)} notices against {len(entries)} missing entries")

    for notice_path in tqdm(notice_paths, desc="Candidate discovery", file=tqdm_file, mininterval=5):
        try:
            raw_text = Path(notice_path).read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not read {notice_path}: {e}")
            continue

        for entry in entries:
            segments = reduced_segments[entry.sdk_element_id]
            if all(seg in raw_text for seg in segments):
                candidate_notices[entry.sdk_element_id].append(notice_path)

    found = sum(1 for v in candidate_notices.values() if v)
    logger.info(f"Found candidates for {found}/{len(entries)} entries")

    return CandidateDiscoveryResult(
        candidates=candidate_notices,
        entries_with_candidates=found,
        total_notices_scanned=len(notice_paths)
    )
