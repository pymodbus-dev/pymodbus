from pymodbus.compat import IS_PYTHON3, PYTHON_VERSION
if not IS_PYTHON3 or IS_PYTHON3 and PYTHON_VERSION.minor < 7:
    collect_ignore = ["test_server_asyncio.py"]
