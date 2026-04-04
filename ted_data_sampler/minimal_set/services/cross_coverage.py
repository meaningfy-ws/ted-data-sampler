import logging
from logging import Logger
from typing import Optional

from ted_data_sampler.minimal_set.models.cross_coverage_result import CrossCoverageResult
from ted_data_sampler.minimal_set.models.missing_xpath import MissingXPathEntry
from ted_data_sampler.minimal_set.models.candidate_discovery_result import CandidateDiscoveryResult


def build_cross_coverage(
    entries: list[MissingXPathEntry],
    candidate_result: CandidateDiscoveryResult,
    logger: Optional[Logger] = None
) -> CrossCoverageResult:
    """
    Build cross-coverage matrix and sort candidates by coverage count.

    Creates a reverse index mapping each notice to the entries it could cover,
    then sorts each entry's candidate list so that notices covering more entries
    are tried first (greedy optimization).

    Args:
        entries: List of missing XPath entries.
        candidate_result: Result from candidate discovery phase containing
            the candidate mapping.
        logger: Optional logger for progress messages.

    Returns:
        CrossCoverageResult with sorted candidates and reverse mapping.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    candidate_notices = candidate_result.candidates

    notice_to_entries: dict[str, list[str]] = {}

    for entry in entries:
        entry_id = entry.sdk_element_id
        for notice_path in candidate_notices.get(entry_id, []):
            if notice_path not in notice_to_entries:
                notice_to_entries[notice_path] = []
            notice_to_entries[notice_path].append(entry_id)

    sorted_candidates: dict[str, list[str]] = {}
    for entry in entries:
        entry_id = entry.sdk_element_id
        candidates = list(candidate_notices.get(entry_id, []))
        candidates.sort(key=lambda path: -len(notice_to_entries.get(path, [])))
        sorted_candidates[entry_id] = candidates

    logger.info(f"Cross-coverage matrix: {len(notice_to_entries)} notices, {len(entries)} entries")

    return CrossCoverageResult(
        sorted_candidates=sorted_candidates,
        notice_to_entries=notice_to_entries,
        total_notices_in_matrix=len(notice_to_entries),
        total_entries=len(entries)
    )
