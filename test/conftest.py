from pymodbus.compat import PYTHON_VERSION

collect_ignore = []

if PYTHON_VERSION < (3,):
    # These files use syntax introduced between Python 2 and our lowest
    # supported Python 3 version.  We just won't run these tests in Python 2.
    collect_ignore.extend([
        "test_client_async_asyncio.py",
        "test_server_asyncio.py",
    ])

if PYTHON_VERSION < (3, 6):
    collect_ignore.extend([
        "test_client_async_trio.py",
        "test_server_trio.py",
    ])
