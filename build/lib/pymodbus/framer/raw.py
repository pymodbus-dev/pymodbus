"""Modbus Raw (passthrough) implementation."""
from __future__ import annotations

from pymodbus.framer.base import FramerBase
from pymodbus.logging import Log


class FramerRaw(FramerBase):
    r"""Modbus RAW Frame Controller.

        [ Device id ][Transaction id ][ Data ]
          1b          2b                Nb

        * data can be 0 - X bytes

    This framer is used for non modbus communication and testing purposes.
    """

    MIN_SIZE = 3

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode ADU."""
        if len(data) < self.MIN_SIZE:
            Log.debug("Short frame: {} wait for more data", data, ":hex")
            return 0, 0, 0, self.EMPTY
        dev_id = int(data[0])
        tid = int(data[1])
        return len(data), dev_id, tid, data[2:]

    def encode(self, pdu: bytes, dev_id: int, tid: int) -> bytes:
        """Encode ADU."""
        return dev_id.to_bytes(1, 'big') + tid.to_bytes(1, 'big') + pdu
