import json
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel


class GapFillerResult(BaseModel):
    """
    DTO representing the final result of the gap filler algorithm.

    Contains the selected notices that cover the missing XPaths, the coverage
    mapping, and any entries that could not be resolved.

    Attributes:
        selected_notices: List of notice file paths that were selected to cover
            the missing XPaths.
        coverage: Mapping from notice path to list of sdk_element_ids that each
            selected notice covers.
        unresolved_entries: List of sdk_element_ids that could not be covered
            by any notice in the pool.
    """
    selected_notices: List[str]
    coverage: Dict[str, List[str]]
    unresolved_entries: List[str]

    def save(self, output_path: Path) -> None:
        """
        Save the result to the output folder in multiple formats.

        Args:
            output_path: Path to the output folder where results will be saved.

        Creates:
            - result_notices.txt: List of selected notice paths (one per line)
            - remaining_uncovered.txt: List of unresolved entry IDs (one per line)
            - coverage_report.json: Detailed JSON report with coverage mapping
              and summary statistics.
        """
        output_path.mkdir(parents=True, exist_ok=True)

        (output_path / "result_notices.txt").write_text(
            "\n".join(self.selected_notices) + "\n" if self.selected_notices else ""
        )

        (output_path / "remaining_uncovered.txt").write_text(
            "\n".join(self.unresolved_entries) + "\n" if self.unresolved_entries else ""
        )

        report = []
        for notice in self.selected_notices:
            report.append({
                "notice_path": notice,
                "covered_entries": self.coverage.get(notice, [])
            })

        summary = {
            "notices_selected": len(self.selected_notices),
            "resolved": sum(len(v) for v in self.coverage.values()),
            "unresolvable": len(self.unresolved_entries),
        }

        (output_path / "coverage_report.json").write_text(json.dumps({
            "coverage": report,
            "summary": summary
        }, indent=2))