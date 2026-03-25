import logging
from pathlib import Path
from typing import Optional

from pymongo import MongoClient
from ted_sws.core.model.manifestation import XMLManifestation
from ted_sws.core.model.metadata import TEDMetadata
from ted_sws.core.model.notice import Notice
from ted_sws.data_manager.adapters.notice_repository import NoticeRepository
from ted_sws.data_sampler.services.notice_xml_indexer import index_notice
from ted_sws.notice_metadata_processor.services.metadata_normalizer import normalise_notice

from ted_data_sampler import config


class LoadNoticesException(Exception):
    pass


def load_notices_to_mongodb(input_folder: Path,
                            logger: logging.Logger,
                            should_normalise_notice: bool = True) -> int:
    if not input_folder.is_dir():
        raise LoadNoticesException(f"Input folder does not exist: {input_folder}")

    xml_files = list(input_folder.rglob("*.xml"))
    logger.info(f"Found {len(xml_files)} XML files in {input_folder}")

    if not xml_files:
        logger.warning("No XML files found")
        return 0

    mongodb_client = MongoClient(config.MONGO_DB_AUTH_URL)
    notice_repository = NoticeRepository(mongodb_client=mongodb_client)

    loaded_count = 0
    error_count = 0

    for xml_file in xml_files:
        try:
            xml_content = xml_file.read_text(encoding="utf-8")

            xml_manifestation = XMLManifestation(object_data=xml_content)
            original_metadata = TEDMetadata()
            ted_id = extract_ted_id_from_filename(xml_file.name)

            if not ted_id:
                logger.warning(f"Could not extract TED ID from filename: {xml_file.name}")
                error_count += 1
                continue

            notice = Notice(ted_id=ted_id)

            notice.set_xml_manifestation(xml_manifestation)
            notice.set_original_metadata(original_metadata)

            if should_normalise_notice:
                indexed_notice = index_notice(notice=notice)
                notice = normalise_notice(notice=indexed_notice)

            notice_repository.add(notice)

            loaded_count += 1
            logger.info(f"Loaded{' normalised' if should_normalise_notice else ''} notice: {ted_id}")

        except Exception as e:
            logger.error(f"Error loading {xml_file.name}: {str(e)}")
            error_count += 1

    logger.info(f"Loading complete: {loaded_count} loaded, {error_count} errors")
    return loaded_count


def extract_ted_id_from_filename(filename: str) -> Optional[str]:
    """
    Extract TED ID from filename.
    Expected format: 00361695_2024.xml -> 361695-2024
    """
    if not filename.endswith(".xml"):
        return None

    name_without_ext = filename[:-4]
    parts = name_without_ext.rsplit("_", 1)

    if len(parts) == 2:
        return f"{parts[0]}-{parts[1]}"

    return None
