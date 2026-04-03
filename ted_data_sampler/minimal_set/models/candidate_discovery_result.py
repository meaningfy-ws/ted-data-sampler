from typing import Dict, List

from pydantic import BaseModel


class CandidateDiscoveryResult(BaseModel):
    """
    DTO representing the result of the candidate discovery phase.

    This phase performs a fast pre-filter using raw text scanning to find
    which notices could potentially contain elements matching the missing
    XPath entries.

    Attributes:
        candidates: Mapping from sdk_element_id to list of notice file paths
            that are candidates for covering that entry. A candidate notice
            contains all segments of abs_xpath_reduced in its raw text.
        entries_with_candidates: Count of entries that have at least one
            candidate notice. Entries with zero candidates cannot be covered.
        total_notices_scanned: Total number of notices that were scanned
            during the candidate discovery phase.
    """
    candidates: Dict[str, List[str]]
    entries_with_candidates: int
    total_notices_scanned: int