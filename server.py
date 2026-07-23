#!/usr/bin/env python3
"""
Minimal Modbus TCP slave (server) using pymodbus.
Listens on localhost:5020 (non-privileged port for easy testing).
Provides simple Modbus data blocks with some demo values.
"""
import logging
import time
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from threading import Thread

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pymodbus.server")

def run_updater(context, interval=5):
    """
    Periodically update some registers to demonstrate changing data.
    """
    slave_id = 0x00
    while True:
        # read current holding registers (example at address 0..9)
        rr = context[slave_id].getValues(3, 0, count=10)  # 3 = holding registers
        # simple update: increment first register, set second as timestamp low
        new0 = (rr[0] + 1) & 0xFFFF
        ts_low = int(time.time()) & 0xFFFF
        context[slave_id].setValues(3, 0, [new0, ts_low] + rr[2:])
        log.info("Updated holding registers: first=%d, ts_low=%d", new0, ts_low)
        time.sleep(interval)

def main():
    # Create initial data blocks (100 items each)
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*100),   # Discrete Inputs
        co=ModbusSequentialDataBlock(0, [0]*100),   # Coils
        hr=ModbusSequentialDataBlock(0, [0]*100),   # Holding Registers
        ir=ModbusSequentialDataBlock(0, [0]*100)    # Input Registers
    )
    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()
    identity.VendorName = 'pymodbus-sim'
    identity.ProductCode = 'PM'
    identity.VendorUrl = 'http://example.com'
    identity.ProductName = 'pymodbus demo server'
    identity.ModelName = 'pymodbus-sim'
    identity.MajorMinorRevision = '1.0'

    # Initialize a few demo values
    context[0].setValues(3, 0, [42, int(time.time()) & 0xFFFF] + [0]*98)

    # Start a background thread to mutate registers periodically
    t = Thread(target=run_updater, args=(context, 5), daemon=True)
    t.start()

    # Start TCP server on port 5020
    address = ("0.0.0.0", 5020)
    log.info("Starting Modbus TCP server on %s:%d", address[0], address[1])
    StartTcpServer(context, identity=identity, address=address)

if __name__ == "__main__":
    main()
