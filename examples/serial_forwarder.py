"""Pymodbus SerialRTU2TCP Forwarder

usage :
python3 serial_forwarder.py --log DEBUG --port "/dev/ttyUSB0" --baudrate 9600 --server_ip "192.168.1.27" --server_port 5020 --slaves 1 2 3

sudo python3 serial_forwarder.py --port "/dev/ttyUSB0" --baudrate 9600 --server_ip "192.168.1.27" --server_port=502 --slaves 1 2 3
"""

import argparse
import logging
import signal

from pymodbus.server.async_io import ModbusTcpServer
from pymodbus.client import ModbusSerialClient
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore.remote import RemoteSlaveContext

FORMAT = "%(asctime)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
logging.basicConfig(format=FORMAT)
_logger = logging.getLogger()

def raise_graceful_exit(*args):
    """enters shutdown mode"""
    _logger.info("receiving shutdown signal now")
    raise SystemExit

class SerialForwarderTCPServer():
    """SerialRTU2TCP Forwarder Server"""
    def __init__(self):
        self.server=None

    async def run(self):
        """run the server"""
        port, baudrate, server_port, server_ip, slaves = get_commandline()
        client = ModbusSerialClient(method='rtu', port=port, baudrate=baudrate)
        _logger.info("RTU bus on %s - baudrate %s", port, baudrate)
        store={}
        for i in slaves:
            store[i]=RemoteSlaveContext(client, unit=i)
        context = ModbusServerContext(slaves=store, single=False)
        self.server = ModbusTcpServer(context, address=(server_ip, server_port), allow_reuse_address=True)
        _logger.info("serving on %s port %s", server_ip, server_port)
        _logger.info("listening to slaves : %s", context.slaves())
        await self.server.serve_forever()

    async def stop(self):
        """stop the server"""
        if self.server:
            await self.server.shutdown()
            _logger.info("TCP server is down")

def get_commandline():
    """Read and validate command line arguments"""
    logchoices=["critical", "error", "warning", "info", "debug"]

    parser = argparse.ArgumentParser(description="Command line options for examples")
    parser.add_argument("--log", help=",".join(logchoices), default="info", type=str)
    parser.add_argument("--port", help="RTU serial port", default = '/dev/ttyUSB0', type=str)
    parser.add_argument("--baudrate", help="RTU baudrate", default = 9600, type=int)
    parser.add_argument("--server_port", help="server port", default = 5020, type=int)
    parser.add_argument("--server_ip", help="server IP", default="127.0.0.1", type=str)
    parser.add_argument("--slaves", help="list of slaves to forward", type=int, nargs="+")

    args = parser.parse_args()

    # set defaults
    _logger.setLevel(args.log.upper() if args.log.lower() in logchoices else logging.INFO)
    if not args.slaves:
        args.slaves = {1,2,3}
    return args.port, args.baudrate, args.server_port, args.server_ip, args.slaves

if __name__ == "__main__":
    server = SerialForwarderTCPServer()
    import asyncio
    try:
        signal.signal(signal.SIGINT, raise_graceful_exit)
        asyncio.run(server.run())
    finally:
        asyncio.run(server.stop())
