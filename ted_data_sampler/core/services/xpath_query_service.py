from logging import Logger
from pathlib import Path
from typing import List

from pydantic import BaseModel
from tqdm import tqdm

from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator


class XPathQueryResult(BaseModel):
    xpath: str
    query_result: List[str]

    def __str__(self):
        if not self.query_result:
            return "[]"
        return ",".join(self.query_result)


class NoticeQueryResult(BaseModel):
    file_path: Path
    xpath_query_results: List[XPathQueryResult]
    file_name: str

    def __str__(self):
        return "{}\t{}".format(self.file_name, "\t".join
        ([str(xpath_query_results) for xpath_query_results in self.xpath_query_results]))


class NoticeQuerySummary(BaseModel):
    xpaths: List[str]
    notices_query_result: List[NoticeQueryResult]

    def __str__(self):
        return "{}\t{}\n{}".format("Notice", "\t".join(self.xpaths), "\n".join(str(notice_query_result) for notice_query_result in self.notices_query_result))


def query_notices_with_given_xpaths(xpaths: List[str], notice_paths: List[Path], logger: Logger) -> NoticeQuerySummary:
    result = NoticeQuerySummary(xpaths=xpaths, notices_query_result=[])

    for notice_path in tqdm(notice_paths):
        xml_content = notice_path.read_text()
        xpath_validator = XPATHValidator(logger=logger, xml_content=xml_content)
        notice_result: NoticeQueryResult = NoticeQueryResult(file_path=notice_path, xpath_query_results=[],
                                                             file_name=notice_path.name)
        for xpath in xpaths:
            try:
                validate_result = xpath_validator.validate(xpath)
            except Exception as e:
                query_result = []
            else:
                query_result: List[str] = [xpath_result.value or "[]" for xpath_result in validate_result]
            notice_result.xpath_query_results.append(XPathQueryResult(xpath=xpath, query_result=query_result))

        result.notices_query_result.append(notice_result)

    return result
