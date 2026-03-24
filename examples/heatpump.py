#!/usr/bin/env python3
"""Controlling a Daikin Altherma 3 heatpump, and presenting data in Home Assistant.

This app is used to control a Daikin heatpump, by reading the temperatures
of deposit for the underfloor heating.

Based on the temperatures and the time of the day (electricity periods P1, P2 and P3) it
is determined to start/stop the heat pump (Daikin Altherma3)

The data is made available in modbus and observed by a Home Assistant server, and presented
to the home users.

Schematic of deposit:

             +--------+
    A) -->  -+        |  F)
             |     E) +--+- --> C)
             |        |  |
    B) <--  -+        |  |
             |        +--+- <-- D)
             +--------+

    A) Intake from heat pump (hot)
    B) Return to heat pump (cold)
    C) Output to underfloor circulation pump (hot)
    D) return from underfloor pipes (cold)
    E) Output from tank (hot)
    F) Thermostatic mixing valve (output is fixed at max 30 degrees)

The 5 point are measured.

The algorithm is quite simple:

    Difference between A) and heat pump setpoint shows the loss in the connection pipes.
    Difference between D) and underfloor heating thermostats show if heat is required.

Remark: the return from the underfloor heating is connected to a thermostatic valve,
on the output to the circulation pump. This allows to e.g. heat the tank to 50 degrees,
while still circulating 30 degrees. Using the thermostatic valve, dramatically reduces
the number of times the heat pump is started (when started it runs longer) and thus saving
electricity.

The thermo meters are read via 1-wire protocol.

usage::

    heatpump.py [-h]
                       [--log {critical,error,warning,info,debug}]
                       [--port <PORT>]
                       [--test]

    -h, --help
        show this help message and exit
    -l, --log {critical,error,warning,info,debug}
        set log level, default is info
    -t, --time
        Limit run time (used e.g. in automated test)
    -p, --port PORT
        set port to listen on
"""
import argparse
import asyncio
from contextlib import suppress
from time import time
from typing import cast

from pymodbus import Log, pymodbus_apply_logging_config
from pymodbus.client import ModbusTcpClient as client
from pymodbus.constants import ExcCodes
from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice


DEVICE_ID = 1
BITS_ADDR = 0
THERMO_ADDR = (1, 3, 5, 7, 9) # Thermometros A-E
ALIVE_ADDR = (11, 12) # Call count, 1 minute counter


class OneWire:  # pylint: disable=(too-few-public-methods
    """Read 1wire thermometros."""

    def read_all(self) -> list[float]:
        """Read 1wire."""
        return [31.2, 32.3, 33.4, 34.5, 35.6]



class Heatpump:
    """Handle heatpump measurement."""

    def __init__(self, cmdline: list[str] | None = None):
        """Create instance."""
        parser = argparse.ArgumentParser(description="Daikin heatpump")
        parser.add_argument(
            "-l",
            "--log",
            choices=["critical", "error", "warning", "info", "debug"],
            help="set log level, default is info",
            dest="log",
            default="info",
            type=str,
        )
        parser.add_argument(
            "-p",
            "--port",
            help="set listen port, default is 5020",
            dest="port",
            default=5020,
            type=str,
        )
        parser.add_argument(
            "-t",
            "--time",
            help="limit run time",
            dest="test_time",
            default=0,
            type=int,
        )
        args = parser.parse_args(cmdline)
        self.test_time = args.test_time
        pymodbus_apply_logging_config(args.log.upper())
        Log.info("Start heatpump monitor.")

        device = SimDevice(DEVICE_ID,
            simdata=[
                SimData(BITS_ADDR, datatype=DataType.BITS),
                SimData(THERMO_ADDR[0], values=0.0, count=len(THERMO_ADDR), datatype=DataType.FLOAT32),
                SimData(ALIVE_ADDR[0], values=0, count=len(ALIVE_ADDR), datatype=DataType.INT16),
            ],
            use_bit_addressing=True,
            action=self.catch_requests
        )
        self.server = ModbusTcpServer(device, address=("", args.port))
        self.serving: asyncio.Future = asyncio.Future()
        self.last_keepalive = 0
        self.one_wire = OneWire()
        self.server_task: asyncio.Task | None = None

    async def catch_requests(
            self,
            _function_code: int,
            _start_address: int,
            _address: int,
            _count: int,
            registers: list[int],
            _set_values: list[int] | list[bool] | None
        ) -> None | ExcCodes:
        """Run action."""
        registers[ALIVE_ADDR[0]] = 0 if registers[ALIVE_ADDR[0]] > 32000 else registers[ALIVE_ADDR[0]] + 1
        return None

    async def serve_forever(self):
        """Update thermometro reading, as well as a keepalive counter."""
        Log.debug("updating_task: started")
        while True:
            if self.serving.done() or self.serving.cancelled():
                return
            await asyncio.sleep(1)
            Log.debug("Update values.")

            if (sec := int(time())) >= self.last_keepalive +60:
                keepalive = cast(list[int], await self.server.async_getValues(DEVICE_ID, 3, ALIVE_ADDR[1], count=1))
                keepalive[0] = 0 if keepalive[0] > 32000 else keepalive[0] + 1
                await self.server.async_setValues(DEVICE_ID, 16, ALIVE_ADDR[1], keepalive)
                self.last_keepalive = sec

            values = self.one_wire.read_all()
            regs: list[int] = []
            for value in values:
                regs.extend(client.convert_to_registers(value, data_type=client.DATATYPE.FLOAT32))
            await self.server.async_setValues(DEVICE_ID, 0x16, THERMO_ADDR[0], regs)

    async def shutdown(self, delayed):  # pragma: no cover
        """Close server."""
        if delayed:
            await asyncio.sleep(delayed)
        Log.debug("Shutdown initiated.")
        if not self.serving.done():
            self.serving.set_result(True)
            await asyncio.sleep(1)
        await self.server.shutdown()
        if self.server_task:
            if not self.server_task.cancelled():
                self.server_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.server_task

    async def run_updating_server(self):
        """Start updating_task concurrently with the current task."""
        Log.info("Starting tasks.")
        self.server_task = asyncio.create_task(self.server.serve_forever())
        self.server_task.set_name("server task")
        await asyncio.sleep(1)
        shutdown_task: asyncio.Task | None = None
        if self.test_time:  # pragma: no cover
            shutdown_task = asyncio.create_task(self.shutdown(self.test_time))
        Log.debug("Forever loop.")
        await self.serve_forever()
        if shutdown_task:
            if not shutdown_task.cancelled():  # pragma: no cover
                shutdown_task.cancel()
            with suppress(asyncio.CancelledError):
                await shutdown_task



async def main(cmdline=None):
    """Combine setup and run."""
    obj = Heatpump(cmdline)
    await obj.run_updating_server()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
