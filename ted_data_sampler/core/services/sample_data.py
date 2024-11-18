from logging import Logger
from pathlib import Path
from typing import List

from pymongo import MongoClient
from ted_sws.core.model.metadata import NoticeSource
from ted_sws.core.model.notice import Notice, NoticeStatus
from ted_sws.data_manager.adapters.notice_repository import NoticeRepository, NOTICE_STATUS
from ted_sws.data_sampler.services.notice_xml_indexer import get_minimal_set_of_notices_for_coverage_xpaths

from ted_data_sampler import config
from ted_data_sampler.core.services.logger import execute_function_with_logging_execution_time


class SampleDataServiceException(Exception):
    """

    """


UNRECOGNISED_NOTICE_SOURCE_ERROR = "Unrecognized notice source"


def get_notices_by_id(notice_repository: NoticeRepository, notice_ids: List[str]) -> List[Notice]:
    return [notice_repository.get(notice_id) for notice_id in notice_ids]


def sample_standard_forms_data(mongodb_client: MongoClient, logger: Logger) -> List[Notice]:
    raise NotImplementedError


def sample_eforms_data_by_sdk_version(sdk_version: str, mongodb_client: MongoClient, logger: Logger) -> List[Notice]:
    notice_repository = NoticeRepository(mongodb_client=mongodb_client)
    notice_source = str(NoticeSource.ELECTRONIC_FORM)
    normalised_eforms_notice_ids = list(notice_repository.collection.find(
        {NOTICE_STATUS: str(NoticeStatus.NORMALISED_METADATA),
         "normalised_metadata.notice_source": notice_source,
         "normalised_metadata.eform_sdk_version": sdk_version},
        {"ted_id": 1}))
    normalised_eforms_notice_ids = [notice_id["ted_id"] for notice_id in normalised_eforms_notice_ids]
    logger.info(f"Detected {len(normalised_eforms_notice_ids)} for {notice_source} with sdk version: {sdk_version}")
    minimal_set_of_notice_ids: List[str] = execute_function_with_logging_execution_time(logger,
                                                                                        get_minimal_set_of_notices_for_coverage_xpaths,
                                                                                        normalised_eforms_notice_ids,
                                                                                        mongodb_client)

    logger.info(f"Minimal set of notices for {sdk_version}: {len(minimal_set_of_notice_ids)}")
    return execute_function_with_logging_execution_time(logger, get_notices_by_id, notice_repository,
                                                        minimal_set_of_notice_ids)


def sample_eforms_data_by_available_sdk_versions(mongodb_client: MongoClient, logger: Logger) -> List[Notice]:
    notice_repository = NoticeRepository(mongodb_client=mongodb_client)
    notice_source = str(NoticeSource.ELECTRONIC_FORM)
    logger.info(f"Sampling data for {notice_source}")

    eforms_sdk_distinct: List[str] = list(notice_repository.collection.distinct("normalised_metadata.eform_sdk_version",
                                                                                {
                                                                                    "normalised_metadata.notice_source": notice_source}))
    logger.info(f"Detected {len(eforms_sdk_distinct)} sdk version of {notice_source} notices: {eforms_sdk_distinct}")

    minimal_set_of_notices_by_sdk_version = []
    for sdk_version in eforms_sdk_distinct:
        minimal_set_of_notices = sample_eforms_data_by_sdk_version(sdk_version, mongodb_client, logger)
        minimal_set_of_notices_by_sdk_version.extend(minimal_set_of_notices)

    return minimal_set_of_notices_by_sdk_version


def sample_data_by_notice_source(notice_source: NoticeSource, logger: Logger) -> List[Notice]:
    mongodb_client = MongoClient(config.MONGO_DB_AUTH_URL)

    if notice_source == NoticeSource.ELECTRONIC_FORM:
        return sample_eforms_data_by_available_sdk_versions(mongodb_client=mongodb_client, logger=logger)
    elif notice_source == NoticeSource.STANDARD_FORM:
        return sample_standard_forms_data(mongodb_client=mongodb_client, logger=logger)
    else:
        logger.error(UNRECOGNISED_NOTICE_SOURCE_ERROR)
        raise SampleDataServiceException(UNRECOGNISED_NOTICE_SOURCE_ERROR)


def store_eform_notices_by_sdk_version(output_path: Path, notices: List[Notice], logger: Logger) -> None:
    logger.info("Storing eforms notices by sdk version")
    output_path.mkdir(parents=True, exist_ok=True)
    for notice in notices:
        if notice.status < NoticeStatus.NORMALISED_METADATA or notice.normalised_metadata.notice_source != NoticeSource.ELECTRONIC_FORM:
            logger.warning(f"Skip store for notice {notice.ted_id}. Check it status or notice source")
            continue
        notice_path = output_path / notice.normalised_metadata.eform_sdk_version / f"{notice.ted_id}.xml"
        notice_path.parent.mkdir(parents=True, exist_ok=True)
        notice_path.write_text(notice.xml_manifestation.object_data)
    logger.info("Storing eforms notices by sdk version done")
