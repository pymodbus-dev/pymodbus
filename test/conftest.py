from pymodbus.compat import PYTHON_VERSION
if PYTHON_VERSION < (3,):
    collect_ignore = ["test_server_asyncio.py"]
