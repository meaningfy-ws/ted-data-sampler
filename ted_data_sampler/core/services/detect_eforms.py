from pathlib import Path
from typing import List

from tqdm import tqdm


def detect_and_save_eforms_notices_path(all_notices_path: Path, output_notices_files_path: Path) -> None:
    assert all_notices_path.is_dir()
    assert output_notices_files_path.is_file()


    notices_paths = [Path(notice) for notice in output_notices_files_path.rglob("*.xml")]
    eform_notice_paths: List[str] = []
    for notice_path in tqdm(notices_paths):

        # 8 digits if eforms, 6 if standard forms
        if len(str(notice_path.stem).split("_")[0]) == 8:
            eform_notice_paths.append(str(notice_path))
    output_notices_files_path.write_text("\n".join(eform_notice_paths))