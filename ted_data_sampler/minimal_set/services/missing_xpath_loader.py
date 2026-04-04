import json
from pathlib import Path
from typing import List

from ted_data_sampler.minimal_set.models.missing_xpath import MissingXPathEntry


def load_missing_xpaths(path: Path) -> List[MissingXPathEntry]:
    """
    Load missing XPath entries from a JSON file.

    Args:
        path: Path to the JSON file containing missing XPath entries.

    Returns:
        List of MissingXPathEntry objects parsed from the JSON file.

    The JSON file can be either:
    - A list of entry objects
    - A dict with "entries" key containing a list of entry objects
    - A dict with "xpaths" key containing a list of entry objects
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries", data.get("xpaths", [data]))
    return [MissingXPathEntry(**entry) for entry in data]