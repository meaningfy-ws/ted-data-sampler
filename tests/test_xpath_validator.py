import logging

from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator


def test_xpath_validator_gives_same_result(contract_notice_cac: str, contract_notice_without_cac: str,
                                           root_xpath_all: str):
    xpath_validator = XPATHValidator(xml_content=contract_notice_cac, logger=logging.getLogger())

    print(xpath_validator.validate(root_xpath_all))
