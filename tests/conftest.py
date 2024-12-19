import pytest

from tests import TEST_CONTRACT_NOTICES


@pytest.fixture
def contract_notice_cac() -> str:
    return (TEST_CONTRACT_NOTICES / "629194-2024.xml").read_text()

@pytest.fixture
def contract_notice_without_cac() -> str:
    return (TEST_CONTRACT_NOTICES / "448070-2024.xml").read_text()


@pytest.fixture
def root_xpath_all() -> str:
    return "/*"