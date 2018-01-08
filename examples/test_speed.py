from pymodbus.client.sync import ModbusSerialClient as Client
from threading import Thread, Event
import time
import logging

FORMAT = '%(asctime)-15s %(levelname)-8s %(module)-8s:%(lineno)-8s %(message)s'

logging.basicConfig(format=FORMAT)
log = logging.getLogger("pymodbus")
log.setLevel(logging.DEBUG)
min_delay = 0.5  # Minimum delay between scans
scan_rate = 1

def poll(client):
    c = Client(method="rtu", port="/tmp/ttyp0", baudrate=9600, timeout=1)
    c.connect()
    while True:
        for unit in range(1, 5):
            resp = client.read_holding_registers(0, 10, unit=unit)
            log.debug(resp)
        time.sleep(1)

class Poller(Thread):
    def __init__(self, port, baudrate, timeout, **kwargs):
        super(Poller, self).__init__(name="Poller Thread")
        self.client = Client(method="rtu",
                             port=port, baudrate=baudrate,
                             timeout=timeout,**kwargs)
        self.daemon = True
        self.stop = Event()
    def run(self):
        self.stop.clear()
        self.client.connect()
        while not self.stop.is_set():
            for unit in range(1, 5):
                resp = self.client.read_holding_registers(0, 10, unit=unit)
                log.debug(resp)
                time.sleep(min_delay)
            time.sleep(scan_rate)
        self.client.close()
    def shutdown(self):
        if not self.stop.is_set():
            self.stop.set()

if __name__ == "__main__":
    poller = Poller(port="/dev/ptyp0", baudrate=9600, timeout=1)
    poller.start()
    time.sleep(200)
    poller.shutdown()


# 105 transactions in 200 seconds