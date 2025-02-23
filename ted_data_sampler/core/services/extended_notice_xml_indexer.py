from pathlib import Path
from typing import List

from pymongo import MongoClient
from ted_sws.core.model.notice import NoticeStatus
from ted_sws.data_manager.adapters.notice_repository import NoticeRepository
from ted_sws.data_sampler.services.notice_xml_indexer import get_unique_xpaths_covered_by_notices

from ted_data_sampler import logger


def get_minimal_set_of_notices_for_coverage_list_of_xpaths(
        xpaths: List[str],
        mongodb_client: MongoClient) -> List[str]:
    xpaths_len = len(xpaths)

    all_notices_id: List[str] = list(
        NoticeRepository(mongodb_client=mongodb_client).get_notice_ids_by_status(NoticeStatus.NORMALISED_METADATA))
    logger.info(f"The number of currently available normalised notices: {len(all_notices_id)}")
    available_xpaths = get_unique_xpaths_covered_by_notices(notice_ids=all_notices_id, mongodb_client=mongodb_client)
    available_xpaths_len = len(available_xpaths)

    logger.info(f"The number of unique xpaths in the available notices: {available_xpaths_len}")
    logger.info(f"The number of xpaths to be covered: {xpaths_len}")


    Path("/mnt/c/Users/user/Desktop/ted-data-sampler/1.txt").write_text("\n".join(xpaths))
    Path("/mnt/c/Users/user/Desktop/ted-data-sampler/2.txt").write_text("\n".join(available_xpaths))
    return []

    sets_difference: set = set(xpaths) - set(available_xpaths)
    if len(sets_difference) > 0:
        logger.info(f"The xpaths to be covered is not a subset of existing xpaths from the available notices")
        logger.info(f"The nr. of uncovered XPaths: {len(sets_difference)}")
        #logger.info(f"Missing XPaths in the available notices: ")
        #logger.info(f"{sets_difference}")
        return []
    else:
        logger.info(f"The xpaths to be covered is a subset of existing xpaths")



    search_notices = all_notices_id.copy()
    notice_repository = NoticeRepository(mongodb_client=mongodb_client)
    logger.info("Start detecting minimal set of notices")
    minimal_set_of_notices = []
    while len(xpaths):
        logger.info(f"Remains xpaths: {len(xpaths)}")
        tmp_result = list(notice_repository.xml_metadata_repository.collection.aggregate([
            {"$match": {
                "ted_id": {"$in": search_notices},
                "metadata_type": {"$eq": "xml"}
            }
            },
            {"$unwind": "$unique_xpaths"},
            {"$match": {
                "unique_xpaths": {"$in": xpaths},
            }
            },
            {"$group": {"_id": "$ted_id", "count": {"$sum": 1}, "xpaths": {"$addToSet": "$unique_xpaths"}
                        }},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ], allowDiskUse=True))
        if tmp_result:
            tmp_result = tmp_result[0]
            search_notices.remove(tmp_result["_id"])
            minimal_set_of_notices.append(tmp_result["_id"])
            for xpath in tmp_result["xpaths"]:
                xpaths.remove(xpath)
    logger.info(f"Nr. of minimal set of notices to cover the XPaths: {len(minimal_set_of_notices)}")
    return minimal_set_of_notices