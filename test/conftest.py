from pymodbus.compat import PYTHON_VERSION

if PYTHON_VERSION < (3,):
    collect_ignore = [
        # TODO: do these really need to be ignored on py2 or can they just get
        #       super() etc fixed?
        "test_client_async.py",
        "test_client_async_tornado.py",
        "test_server_asyncio.py",
    ]
