"""RTU framer."""
# pylint: disable=missing-type-doc
import time

from pymodbus.exceptions import ModbusIOException
from pymodbus.framer.old_framer_base import BYTE_ORDER, FRAME_HEADER, ModbusFramer
from pymodbus.framer.rtu import FramerRTU
from pymodbus.logging import Log
from pymodbus.utilities import ModbusTransactionState


RTU_FRAME_HEADER = BYTE_ORDER + FRAME_HEADER


# --------------------------------------------------------------------------- #
# Modbus RTU old Framer
# --------------------------------------------------------------------------- #
class ModbusRtuFramer(ModbusFramer):
    """Modbus RTU Frame controller.

        [ Start Wait ] [Address ][ Function Code] [ Data ][ CRC ][  End Wait  ]
          3.5 chars     1b         1b               Nb      2b      3.5 chars

    Wait refers to the amount of time required to transmit at least x many
    characters.  In this case it is 3.5 characters.  Also, if we receive a
    wait of 1.5 characters at any point, we must trigger an error message.
    Also, it appears as though this message is little endian. The logic is
    simplified as the following::

        block-on-read:
            read until 3.5 delay
            check for errors
            decode

    The following table is a listing of the baud wait times for the specified
    baud rates::

        ------------------------------------------------------------------
         Baud  1.5c (18 bits)   3.5c (38 bits)
        ------------------------------------------------------------------
         1200   13333.3 us       31666.7 us
         4800    3333.3 us        7916.7 us
         9600    1666.7 us        3958.3 us
        19200     833.3 us        1979.2 us
        38400     416.7 us         989.6 us
        ------------------------------------------------------------------
        1 Byte = start + 8 bits + parity + stop = 11 bits
        (1/Baud)(bits) = delay seconds
    """

    method = "rtu"

    def __init__(self, decoder, client=None):
        """Initialize a new instance of the framer.

        :param decoder: The decoder factory implementation to use
        """
        super().__init__(decoder, client)
        self._hsize = 0x01
        self.function_codes = decoder.lookup.keys() if decoder else {}
        self.message_handler: FramerRTU = FramerRTU(function_codes=self.function_codes)
        self.msg_len = 0

    def decode_data(self, data):
        """Decode data."""
        if len(data) > self._hsize:
            uid = int(data[0])
            fcode = int(data[1])
            return {"slave": uid, "fcode": fcode}
        return {}

    def frameProcessIncomingPacket(self, _single, callback, slave, tid=None):
        """Process new packet pattern."""
        self.message_handler.set_slaves(slave)
        while True:
            used_len, ok = self.message_handler.get_frame_start(self._buffer)
            if used_len:
                self._buffer = self._buffer[used_len:]
            if not ok:
                break
            self.dev_id, self.msg_len, ok = self.message_handler.old_is_frame_ready(self._buffer, self.decoder)
            if not ok:
                Log.debug("Frame - not ready")
                break
            self.dev_id, self.msg_len, ok = self.message_handler.old_check_frame(self._buffer, self.msg_len, self.decoder)
            if not ok:
                Log.debug("Frame check failed, ignoring!!")
                x = self._buffer
                self.resetFrame()
                self._buffer: bytes = x[1:]
                continue
            start = self._hsize
            end = self.msg_len - 2
            buffer = self._buffer[start:end]
            if end > 0:
                Log.debug("Getting Frame - {}", buffer, ":hex")
                data = buffer
            else:
                data = b""
            if (result := self.decoder.decode(data)) is None:
                raise ModbusIOException("Unable to decode request")
            result.slave_id = self.dev_id
            result.transaction_id = 0
            self._buffer = self._buffer[self.msg_len :]
            Log.debug("Frame advanced, resetting header!!")
            callback(result)  # defer or push to a thread?

    def buildPacket(self, message):
        """Create a ready to send modbus packet.

        :param message: The populated request/response to send
        """
        packet = super().buildPacket(message)

        # Ensure that transaction is actually the slave id for serial comms
        message.transaction_id = 0
        return packet

    def sendPacket(self, message: bytes) -> int:
        """Send packets on the bus with 3.5char delay between frames.

        :param message: Message to be sent over the bus
        :return:
        """
        super().resetFrame()
        start = time.time()
        if hasattr(self.client,"ctx"):
            timeout = start + self.client.ctx.comm_params.timeout_connect
        else:
            timeout = start + self.client.comm_params.timeout_connect
        while self.client.state != ModbusTransactionState.IDLE:
            if self.client.state == ModbusTransactionState.TRANSACTION_COMPLETE:
                timestamp = round(time.time(), 6)
                Log.debug(
                    "Changing state to IDLE - Last Frame End - {} Current Time stamp - {}",
                    self.client.last_frame_end,
                    timestamp,
                )
                if self.client.last_frame_end:
                    idle_time = self.client.idle_time()
                    if round(timestamp - idle_time, 6) <= self.client.silent_interval:
                        Log.debug(
                            "Waiting for 3.5 char before next send - {} ms",
                            self.client.silent_interval * 1000,
                        )
                        time.sleep(self.client.silent_interval)
                else:
                    # Recovering from last error ??
                    time.sleep(self.client.silent_interval)
                self.client.state = ModbusTransactionState.IDLE
            elif self.client.state == ModbusTransactionState.RETRYING:
                # Simple lets settle down!!!
                # To check for higher baudrates
                time.sleep(self.client.comm_params.timeout_connect)
                break
            elif time.time() > timeout:
                Log.debug(
                    "Spent more time than the read time out, "
                    "resetting the transaction to IDLE"
                )
                self.client.state = ModbusTransactionState.IDLE
            else:
                Log.debug("Sleeping")
                time.sleep(self.client.silent_interval)
        size = self.client.send(message)
        self.client.last_frame_end = round(time.time(), 6)
        return size
