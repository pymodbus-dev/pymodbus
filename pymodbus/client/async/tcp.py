"""
Copyright (c) 2017 by Riptide I/O
All rights reserved.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
from pymodbus.client.async.factory.tcp import get_factory
from pymodbus.constants import Defaults
from pymodbus.compat import IS_PYTHON3, PYTHON_VERSION
from pymodbus.client.async.schedulers import ASYNC_IO

logger = logging.getLogger(__name__)


class AsyncModbusTCPClient(object):
    def __new__(cls, scheduler, host="127.0.0.1", port=Defaults.Port,
                framer=None, source_address=None, timeout=None, **kwargs):
        if not (IS_PYTHON3 and PYTHON_VERSION >= (3, 4)) and scheduler == ASYNC_IO:
            logger.critical("ASYNCIO is supported only on python3")
            import sys
            sys.exit(1)
        factory_class = get_factory(scheduler)
        yieldable = factory_class(host=host, port=port, framer=framer,
                                  source_address=source_address,
                                  timeout=timeout, **kwargs)
        return yieldable

