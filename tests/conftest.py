import lamindb.setup as ln_setup


def pytest_sessionstart(session):
    """Initialize LamindB before any test runs."""
    print("\n🔹 Setting up LamindB test instance...")
    ln_setup.init(storage="lamin_test_instance", name="lamin_test_instance", schema="bionty")


def pytest_sessionfinish(session):
    """Clean up LamindB after all tests are completed."""
    print("\n🔹 Cleaning up LamindB test instance after all tests are done...")
    ln_setup.delete("lamin_test_instance", force=True, require_empty=False)
