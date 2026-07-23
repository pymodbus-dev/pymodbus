#!/usr/bin/env python3
"""
Simple Modbus TCP client that polls holding registers every N seconds
and appends results into a CSV log file.
"""
import csv
import time
import logging
from pymodbus.client.sync import ModbusTcpClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pymodbus.client")

HOST = "localhost"
PORT = 5020
UNIT = 1            # unit id (slave id) - with single=True on server, unit is often ignored
START_ADDR = 0      # starting register
COUNT = 4           # number of registers to read each poll
POLL_INTERVAL = 2   # seconds
CSV_FILE = "modbus_log.csv"

def read_and_append(client, csv_writer):
    rr = client.read_holding_registers(START_ADDR, COUNT, unit=UNIT)
    if rr.isError():
        log.warning("Read error: %s", rr)
        return False
    regs = rr.registers
    timestamp = int(time.time())
    log.info("Read registers @%d: %s", START_ADDR, regs)
    csv_writer.writerow([timestamp] + regs)
    return True

def main():
    client = ModbusTcpClient(HOST, port=PORT)
    if not client.connect():
        log.error("Unable to connect to Modbus server at %s:%d", HOST, PORT)
        return

    # Open CSV once and keep appending
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        # write header if file empty-ish (naive)
        try:
            f.seek(0)
            if f.read(1) == "":
                writer.writerow(["timestamp"] + [f"reg_{i}" for i in range(START_ADDR, START_ADDR+COUNT)])
                f.flush()
        except Exception:
            # ignore seeking errors on some systems
            pass

        try:
            while True:
                success = read_and_append(client, writer)
                if success:
                    f.flush()
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            log.info("Stopping client")
        finally:
            client.close()

if __name__ == "__main__":
    main()
