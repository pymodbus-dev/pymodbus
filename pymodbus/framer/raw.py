"""Modbus Raw (passthrough) implementation."""
from __future__ import annotations

from pymodbus.framer.base import FramerBase
from pymodbus.logging import Log


class FramerRaw(FramerBase):
    r"""Modbus RAW Frame Controller.

        [ Device id ][Transaction id ][ Data ]
          1c          2c                Nc

        * data can be 1 - X chars

    This framer is used for non modbus communication and testing purposes.
    """

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode message."""
        if len(data) < 3:
            Log.debug("Short frame: {} wait for more data", data, ":hex")
            return 0, 0, 0, self.EMPTY
        dev_id = int(data[0])
        tid = int(data[1])
        return len(data), dev_id, tid, data[2:]

    def encode(self, pdu: bytes, device_id: int, tid: int) -> bytes:
        """Decode message."""
        return device_id.to_bytes(1, 'big') + tid.to_bytes(1, 'big') + pdu
