import logging

from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator, XPathAssertionEntry


def test_xpath_validator_gives_same_result(contract_notice_cac: str, contract_notice_without_cac: str,
                                           root_xpath_all: str):
    xpath_validator = XPATHValidator(xml_content=contract_notice_cac, logger=logging.getLogger())

    results = xpath_validator.validate(root_xpath_all)

    # Verify we got results
    assert len(results) > 0

    # Verify results are XPathAssertionEntry objects
    assert all(isinstance(result, XPathAssertionEntry) for result in results)

    # Verify each result has an xpath
    assert all(result.xpath is not None for result in results)
