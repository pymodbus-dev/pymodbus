#!/usr/bin/env python
"""
Simple Asynchronous Modbus TCP over TLS client
---------------------------------------------------------------------------

This is a simple example of writing a asynchronous modbus TCP over TLS client
that uses Python builtin module ssl - TLS/SSL wrapper for socket objects for
the TLS feature and asyncio.
"""
# -------------------------------------------------------------------------- #
# import neccessary libraries
# -------------------------------------------------------------------------- #
import ssl
from pymodbus.client.asynchronous.tls import AsyncModbusTLSClient
from pymodbus.client.asynchronous.schedulers import ASYNC_IO

# -------------------------------------------------------------------------- #
# the TLS detail security can be set in SSLContext which is the context here
# -------------------------------------------------------------------------- #
sslctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
sslctx.verify_mode = ssl.CERT_REQUIRED
sslctx.check_hostname = True

# Prepare client's certificate which the server requires for TLS full handshake
# sslctx.load_cert_chain(certfile="client.crt", keyfile="client.key",
#                        password="pwd")

async def start_async_test(client):
    result = await client.read_coils(1, 8)
    print(result.bits)
    await client.write_coils(1, [False]*3)
    result = await client.read_coils(1, 8)
    print(result.bits)

if __name__ == '__main__':
# -------------------------------------------------------------------------- #
# pass SSLContext which is the context here to ModbusTcpClient()
# -------------------------------------------------------------------------- #
    loop, client = AsyncModbusTLSClient(ASYNC_IO, 'test.host.com', 8020,
                                        sslctx=sslctx)
    loop.run_until_complete(start_async_test(client.protocol))
    loop.close()
