from typing import Dict, List

from pydantic import BaseModel


class CrossCoverageResult(BaseModel):
    """
    DTO representing the result of cross-coverage analysis.

    This phase builds a reverse index mapping notices to the entries they could
    cover, then sorts each entry's candidate list by coverage count (notices that
    cover more entries are tried first for efficiency).

    Attributes:
        sorted_candidates: Mapping from sdk_element_id to list of notice paths,
            sorted in descending order by how many other entries each notice could
            also cover. Notices with higher cross-coverage are prioritized.
        notice_to_entries: Reverse mapping from notice path to list of
            sdk_element_ids that the notice is a candidate for. Used to detect
            additional coverage when a notice is selected.
        total_notices_in_matrix: Number of unique notices that appear as candidates.
        total_entries: Total number of entries in the input pool.
    """
    sorted_candidates: Dict[str, List[str]]
    notice_to_entries: Dict[str, List[str]]
    total_notices_in_matrix: int
    total_entries: int