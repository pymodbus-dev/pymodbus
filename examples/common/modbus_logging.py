#!/usr/bin/env python
"""
Pymodbus Logging Examples
--------------------------------------------------------------------------
"""
import logging
import logging.handlers as Handlers

if __name__ == "__main__":
    # ----------------------------------------------------------------------- #
    # This will simply send everything logged to console
    # ----------------------------------------------------------------------- #
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    # ----------------------------------------------------------------------- #
    # This will send the error messages in the specified namespace to a file.
    # The available namespaces in pymodbus are as follows:
    # ----------------------------------------------------------------------- #
    # * pymodbus.*          - The root namespace
    # * pymodbus.server.*   - all logging messages involving the modbus server
    # * pymodbus.client.*   - all logging messages involving the client
    # * pymodbus.protocol.* - all logging messages inside the protocol layer
    # ----------------------------------------------------------------------- #
    logging.basicConfig()
    log = logging.getLogger('pymodbus.server')
    log.setLevel(logging.ERROR)

    # ----------------------------------------------------------------------- #
    # This will send the error messages to the specified handlers:
    # * docs.python.org/library/logging.html
    # ----------------------------------------------------------------------- #
    log = logging.getLogger('pymodbus')
    log.setLevel(logging.ERROR)
    handlers = [
        Handlers.RotatingFileHandler("logfile", maxBytes=1024*1024),
        Handlers.SMTPHandler("mx.host.com",
                             "pymodbus@host.com",
                             ["support@host.com"],
                             "Pymodbus"),
        Handlers.SysLogHandler(facility="daemon"),
        Handlers.DatagramHandler('localhost', 12345),
    ]
    [log.addHandler(h) for h in handlers]

