from pymodbus.compat import PYTHON_VERSION
if PYTHON_VERSION < (3,):
    # These files use syntax introduced between Python 2 and our lowest
    # supported Python 3 version.  We just won't run these tests in Python 2.
    collect_ignore = [
        "test_client_async_asyncio.py",
        "test_server_asyncio.py",
    ]
