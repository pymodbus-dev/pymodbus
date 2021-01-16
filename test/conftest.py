from pymodbus.compat import PYTHON_VERSION

if PYTHON_VERSION < (3,):
    # These files use syntax introduced in Python 3 (not necessarily 3.0) and
    # just won't be run during tests in Python 2.
    collect_ignore = [
        "test_server_asyncio.py",
    ]
