"""
Copyright (c) 2017 by Riptide I/O
All rights reserved.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

from pymodbus.client.async.factory.serial import get_factory


class AsyncModbusSerialClient(object):
    def __new__(cls, scheduler, framer, port,  **kwargs):
        factory_class = get_factory(scheduler)
        yieldable = factory_class(framer=framer, port=port, **kwargs)
        return yieldable
