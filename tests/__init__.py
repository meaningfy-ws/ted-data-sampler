from pathlib import Path

TESTS_PATH: Path = Path(__file__).parent.resolve()
TEST_DATA_PATH: Path = TESTS_PATH / "test_data"
TEST_CONTRACT_NOTICES: Path = TEST_DATA_PATH / "test_contract_notices"