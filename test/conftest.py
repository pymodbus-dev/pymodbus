import platform
from pkg_resources import parse_version


IS_DARWIN = platform.system().lower() == "darwin"
IS_WINDOWS = platform.system().lower() == "windows"

if IS_DARWIN:
    # check for SIERRA
    if parse_version("10.12") < parse_version(platform.mac_ver()[0]):
        SERIAL_PORT = '/dev/ptyp0'
    else:
        SERIAL_PORT = '/dev/ttyp0'
else:
    SERIAL_PORT = "/dev/ptmx"
