from pathlib import Path
from typing import List

from ted_sws.core.model.notice import Notice


def store_eforms_notices_grouped_by_sdk_version_notice_type_notice_subtype(output_path: Path, notices: List[Notice]):
    for notice in notices:
        notice_path: Path = output_path / notice.normalised_metadata.eform_sdk_version / \
                            notice.normalised_metadata.notice_type.split("/")[
                                -1] / notice.normalised_metadata.eforms_subtype / f"{notice.ted_id}.xml"
        notice_path.parent.mkdir(parents=True, exist_ok=True)
        notice_path.write_text(notice.xml_manifestation.object_data)
