import pytest
import lamindb_setup as ln_setup

@pytest.fixture(scope="session")
def setup_instance():
    """
    Initialize a LamindB test instance before all tests start.
    Cleans up after the test session ends.
    """
    ln_setup.init(storage="tests", name="tests", schema="bionty")
    yield  # Run tests using this instance
    ln_setup.delete("tests", force=True, require_empty=False)
