"""
Copyright (c) 2017 by Riptide I/O
All rights reserved.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

from pymodbus.client.async.factory.tcp import get_factory
from pymodbus.constants import Defaults


class AsyncModbusTCPClient(object):
    def __new__(cls, scheduler, host="127.0.0.1", port=Defaults.Port,
                framer=None, source_address=None, timeout=None, **kwargs):
        factory_class = get_factory(scheduler)
        yieldable = factory_class(host=host, port=port, framer=framer,
                                  source_address=source_address,
                                  timeout=timeout, **kwargs)
        return yieldable

