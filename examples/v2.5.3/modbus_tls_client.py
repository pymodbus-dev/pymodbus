#!/usr/bin/env python3
"""Simple Modbus TCP over TLS client.

This is a simple example of writing a modbus TCP over TLS client that uses
Python builtin module ssl - TLS/SSL wrapper for socket objects for the TLS
feature.
"""
# -------------------------------------------------------------------------- #
# import necessary libraries
# -------------------------------------------------------------------------- #
import ssl

from pymodbus.client import ModbusTlsClient


# -------------------------------------------------------------------------- #
# the TLS detail security can be set in SSLContext which is the context here
# -------------------------------------------------------------------------- #
sslctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
sslctx.verify_mode = ssl.CERT_REQUIRED
sslctx.check_hostname = True

# Prepare client's certificate which the server requires for TLS full handshake
# sslctx.load_cert_chain(certfile="client.crt", keyfile="client.key",
#                        password="pwd")

# -------------------------------------------------------------------------- #
# pass SSLContext which is the context here to ModbusTcpClient()
# -------------------------------------------------------------------------- #
client = ModbusTlsClient("test.host.com", 8020, sslctx=sslctx)
client.connect()

result = client.read_coils(1, 8)
print(result.bits)

client.close()
