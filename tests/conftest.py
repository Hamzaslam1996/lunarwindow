import pytest

from lunarwindow.ephemeris import kernels

needs_kernels = pytest.mark.skipif(
    not kernels.kernels_present(), reason="SPICE kernels not present (scripts/fetch_kernels.py)"
)


@pytest.fixture(scope="session")
def spice_loaded():
    kernels.load()
    yield
