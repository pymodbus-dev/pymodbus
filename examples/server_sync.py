#!/usr/bin/env python3
"""Pymodbus Synchronous Server Example.

The synchronous server is implemented in pure python without any third
party libraries (unless you need to use the serial protocols which require
pyserial).

Start it as:
    python3 server_sync.py

After start it will accept client connections.
The corresponding client can be started as:
    python3 server_sync.py
"""

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from examples.helper import _logger, get_commandline
from pymodbus.server.sync import (
    StartSerialServer,
    StartTcpServer,
    StartTlsServer,
    StartUdpServer,
)
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
    ModbusSparseDataBlock,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.version import version

FRAMERS = {
    "ascii": ModbusAsciiFramer,
    "binary": ModbusBinaryFramer,
    "rtu": ModbusRtuFramer,
    "socket": ModbusSocketFramer,
    "tls": ModbusTlsFramer,
}


def setup_sync_server():
    """Run client setup.

    use --comm at command line to select the type of communication
    use --framer at command line to select the modbus framer
    use --log at command line to set logging level
    use --store at command line to set type of datastore
    The remaining parameters are defined static.
    """
    args = get_commandline(True)
    _logger.info("### Create datastore")

    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #
    # The datastores only respond to the addresses that are initialized
    # If you initialize a DataBlock to addresses of 0x00 to 0xFF, a request to
    # 0x100 will respond with an invalid address exception.
    # This is because many devices exhibit this kind of behavior (but not all)
    # ----------------------------------------------------------------------- #
    if not args.store:
        args.store = "sequential"
    if args.store == "sequential":
        # Continuing, use a sequential block without gaps.
        datablock = ModbusSequentialDataBlock(0x00, [17] * 100)
    elif args.store == "sparse":
        # Continuing, or use a sparse DataBlock which can have gaps
        datablock = ModbusSparseDataBlock({0x00: 0, 0x05: 1})
    elif args.store == "factory":
        # Alternately, use the factory methods to initialize the DataBlocks
        # or simply do not pass them to have them initialized to 0x00 on the
        # full address range::
        datablock = ModbusSequentialDataBlock.create()

    if args.slaves:
        # The server then makes use of a server context that allows the server
        # to respond with different slave contexts for different unit ids.
        # By default it will return the same context for every unit id supplied
        # (broadcast mode).
        # However, this can be overloaded by setting the single flag to False and
        # then supplying a dictionary of unit id to context mapping::
        #
        # The slave context can also be initialized in zero_mode which means
        # that a request to address(0-7) will map to the address (0-7).
        # The default is False which is based on section 4.4 of the
        # specification, so address(0-7) will map to (1-8)::
        # ----------------------------------------------------------------------- #
        context = {
            0x01: ModbusSlaveContext(
                di=datablock,
                co=datablock,
                hr=datablock,
                ir=datablock,
            ),
            0x02: ModbusSlaveContext(
                di=datablock,
                co=datablock,
                hr=datablock,
                ir=datablock,
            ),
            0x03: ModbusSlaveContext(
                di=datablock,
                co=datablock,
                hr=datablock,
                ir=datablock,
                zero_mode=True
            )
        }
    else:
        context = ModbusSlaveContext(
            di=datablock,
            co=datablock,
            hr=datablock,
            ir=datablock,
        )

    # Build data storage
    store = ModbusServerContext(slaves=context, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    # If you don"t set this or any fields, they are defaulted to empty strings.
    # ----------------------------------------------------------------------- #
    identity = ModbusDeviceIdentification(
        info_name={
            "VendorName": "Pymodbus",
            "ProductCode": "PM",
            "VendorUrl": "https://github.com/riptideio/pymodbus/",
            "ProductName": "Pymodbus Server",
            "ModelName": "Pymodbus Server",
            "MajorMinorRevision": version.short(),
        }
    )

    if not args.comm:
        args.comm = "tcp"
    return args.comm, store, identity, args.framer


def run_server():
    """Run server."""
    server, store, identity, framer = setup_sync_server()

    _logger.info("### start server")
    if server == "tcp":
        if not framer:
            framer = "socket"
        StartTcpServer(
            context=store,  # Data storage
            identity=identity,  # server identify
            address=("", 5020),  # listen address
            custom_functions=[],  # allow custom handling
            framer=FRAMERS[framer],  # The framer strategy to use
            handler=None,  # handler for each session
            allow_reuse_address=True,  # allow the reuse of an address
            ignore_missing_slaves=True,  # ignore request to a missing slave
            broadcast_enable=False,  # treat unit_id 0 as broadcast address,
            # TBD timeout=1,  # waiting time for request to complete
            # TBD strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif server == "udp":
        if not framer:
            framer = "socket"
        StartUdpServer(
            context=store,  # Data storage
            identity=identity,  # server identify
            address=("", 5020),  # listen address
            custom_functions=[],  # allow custom handling
            framer=FRAMERS[framer],  # The framer strategy to use
            handler=None,  # handler for each session
            # TBD allow_reuse_address=True,  # allow the reuse of an address
            ignore_missing_slaves=True,  # ignore request to a missing slave
            broadcast_enable=False,  # treat unit_id 0 as broadcast address,
            # TBD timeout=1,  # waiting time for request to complete
            # TBD strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif server == "serial":
        # socat -d -d PTY,link=/tmp/ptyp0,raw,echo=0,ispeed=9600 PTY,
        #             link=/tmp/ttyp0,raw,echo=0,ospeed=9600
        if not framer:
            framer = "rtu"
        StartSerialServer(
            context=store,  # Data storage
            identity=identity,  # server identify
            timeout=.005,  # waiting time for request to complete
            port="/dev/ptyp0",  # serial port
            custom_functions=[],  # allow custom handling
            framer=FRAMERS[framer],  # The framer strategy to use
            handler=None,  # handler for each session
            stopbits=1,  # The number of stop bits to use
            bytesize=7,  # The bytesize of the serial messages
            parity="even",  # Which kind of parity to use
            baudrate=9600,  # The baud rate to use for the serial device
            handle_local_echo=False,  # Handle local echo of the USB-to-RS485 adaptor
            ignore_missing_slaves=True,  # ignore request to a missing slave
            broadcast_enable=False,  # treat unit_id 0 as broadcast address,
            strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif server == "tls":
        if not framer:
            framer = "tls"
        StartTlsServer(
            context=store,  # Data storage
            host="localhost",  # define tcp address where to connect to.
            port=5020,  # on which port
            identity=identity,  # server identify
            custom_functions=[],  # allow custom handling
            address=("", 5020),  # listen address
            framer=FRAMERS[framer],  # The framer strategy to use
            handler=None,  # handler for each session
            allow_reuse_address=True,  # allow the reuse of an address
            certfile=None,  # The cert file path for TLS (used if sslctx is None)
            sslctx=None,    # The SSLContext to use for TLS (default None and auto create)
            keyfile=None,  # The key file path for TLS (used if sslctx is None)
            password=None,  # The password for for decrypting the private key file
            reqclicert=False,  # Force the sever request client"s certificate
            ignore_missing_slaves=True,  # ignore request to a missing slave
            broadcast_enable=False,  # treat unit_id 0 as broadcast address,
            # TBD timeout=1,  # waiting time for request to complete
            # TBD strict=True,  # use strict timing, t1.5 for Modbus RTU
        )


if __name__ == "__main__":
    run_server()
