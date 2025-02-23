from pathlib import Path
from typing import List

from pymongo import MongoClient
from ted_sws.core.model.notice import Notice
from ted_sws.data_manager.adapters.notice_repository import NoticeRepository

from ted_data_sampler import config
from ted_data_sampler.core.services.sample_data import get_notices_by_id


def store_eforms_notices_grouped_by_sdk_version_notice_type_notice_subtype(output_path: Path, notices: List[Notice]):
    for notice in notices:
        notice_path: Path = output_path / notice.normalised_metadata.eform_sdk_version / notice.normalised_metadata.notice_type.split("/")[-1] / notice.normalised_metadata.eforms_subtype / f"{notice.ted_id}.xml"
        notice_path.parent.mkdir(parents=True, exist_ok=True)
        notice_path.write_text(notice.xml_manifestation.object_data)


if __name__ == '__main__':
    notices_folder_path = Path("/mnt/c/Users/user/Desktop/data_sampler_run_2024-11-23_11-50-33")
    out_path = notices_folder_path.parent / "output_grouped"
    notice_ids = [notice_path.stem for notice_path in notices_folder_path.rglob('*.xml')]
    print(f"Nr of notices ids: {len(notice_ids)}")
    mongodb_client = MongoClient(config.MONGO_DB_AUTH_URL)
    notice_repository = NoticeRepository(mongodb_client=mongodb_client)

    notices = get_notices_by_id(notice_repository, notice_ids)
    print(f"Nr of notices: {len(notices)}")
    store_eforms_notices_grouped_by_sdk_version_notice_type_notice_subtype(out_path, notices)