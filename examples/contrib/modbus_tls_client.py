#!/usr/bin/env python
"""
Simple Modbus TCP over TLS client
---------------------------------------------------------------------------

This is a simple example of writing a modbus TCP over TLS client that uses
Python builtin module ssl - TLS/SSL wrapper for socket objects for the TLS
feature.
"""
# -------------------------------------------------------------------------- #
# import neccessary libraries
# -------------------------------------------------------------------------- #
import ssl
from pymodbus.client.sync import ModbusTlsClient

# -------------------------------------------------------------------------- #
# the TLS detail security can be set in SSLContext which is the context here
# -------------------------------------------------------------------------- #
context = ssl.create_default_context()
context.options |= ssl.OP_NO_SSLv2
context.options |= ssl.OP_NO_SSLv3
context.options |= ssl.OP_NO_TLSv1
context.options |= ssl.OP_NO_TLSv1_1

# -------------------------------------------------------------------------- #
# pass SSLContext which is the context here to ModbusTcpClient()
# -------------------------------------------------------------------------- #
client = ModbusTlsClient('test.host.com', 8020, sslctx=context)
client.connect()

result = client.read_coils(1, 8)
print(result.bits)

client.close()
