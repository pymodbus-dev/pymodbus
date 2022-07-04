"""Configure pytest."""
import platform

from pkg_resources import parse_version
import pytest


def pytest_configure():
    """Configure pytest."""
    pytest.IS_DARWIN = platform.system().lower() == "darwin"
    pytest.IS_WINDOWS = platform.system().lower() == "windows"

    if pytest.IS_DARWIN:
        # check for SIERRA
        if parse_version("10.12") < parse_version(platform.mac_ver()[0]):
            pytest.SERIAL_PORT = "/dev/ptyp0"
        else:
            pytest.SERIAL_PORT = "/dev/ttyp0"
    else:
        pytest.SERIAL_PORT = "/dev/ptmx"
