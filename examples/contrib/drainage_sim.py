#!/usr/bin/env python3

# Simulates two Modbus TCP slave servers:
#
# Port 5020: Digital IO (DIO) with 8 discrete inputs and 8 coils. The first two coils each control
#            a simulated pump. Inputs are not used.
#
# Port 5021: Water level meter (WLM) returning the current water level in the input register. It
#            increases chronologically and decreases rapidly when one or two pumps are active.

import asyncio
import logging
from datetime import datetime

from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.server import StartAsyncTcpServer

INITIAL_WATER_LEVEL = 300
WATER_INFLOW = 1
PUMP_OUTFLOW = 8

logging.basicConfig(level = logging.INFO)

dio_di = ModbusSequentialDataBlock(1, [False] * 8)
dio_co = ModbusSequentialDataBlock(1, [False] * 8)
dio_context = ModbusSlaveContext(di = dio_di, co = dio_co)
wlm_ir = ModbusSequentialDataBlock(1, [INITIAL_WATER_LEVEL])
wlm_context = ModbusSlaveContext(ir = wlm_ir)

async def update():
    while True:
        await asyncio.sleep(1)

        # Update water level based on DIO output values (simulating pumps)
        water_level = wlm_ir.getValues(1, 1)[0]
        dio_outputs = dio_co.getValues(1, 2)

        water_level += WATER_INFLOW
        water_level -= (int(dio_outputs[0]) + int(dio_outputs[1])) * PUMP_OUTFLOW
        water_level = max(0, min(INITIAL_WATER_LEVEL * 10, water_level))
        wlm_ir.setValues(1, [water_level])

async def log():
    while True:
        await asyncio.sleep(10)

        dio_outputs = dio_co.getValues(1, 8)
        wlm_level = wlm_ir.getValues(1, 1)[0]

        logging.info(f"{datetime.now()}: WLM water level: {wlm_level}, DIO outputs: {dio_outputs}")

async def run():
    ctx = ModbusServerContext(slaves = dio_context)
    dio_server = asyncio.create_task(StartAsyncTcpServer(context = ctx, address = ("0.0.0.0", 5020)))
    logging.info("Initialising slave server DIO on port 5020")

    ctx = ModbusServerContext(slaves = wlm_context)
    wlm_server = asyncio.create_task(StartAsyncTcpServer(context = ctx, address = ("0.0.0.0", 5021)))
    logging.info("Initialising slave server WLM on port 5021")

    update_task = asyncio.create_task(update())
    logging_task = asyncio.create_task(log())

    logging.info("Init complete")
    await asyncio.gather(dio_server, wlm_server, update_task, logging_task)

if __name__ == "__main__":
    asyncio.run(run(), debug=True)
