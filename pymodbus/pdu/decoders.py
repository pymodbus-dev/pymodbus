"""Modbus Request/Response Decoders."""
from __future__ import annotations

import copy

from pymodbus.exceptions import MessageRegisterException, ModbusException
from pymodbus.logging import Log

from .exceptionresponse import ExceptionResponse
from .pdu import ModbusPDU


class DecodePDU:
    """Decode pdu requests/responses (server/client)."""

    pdu_table: dict[int, tuple[type[ModbusPDU], type[ModbusPDU]]] = {}
    pdu_sub_table: dict[int, dict[int, tuple[type[ModbusPDU], type[ModbusPDU]]]] = {}


    def __init__(self, is_server: bool) -> None:
        """Initialize function_tables."""
        self.pdu_inx = 0 if is_server else 1

    def lookupPduClass(self, data: bytes) -> type[ModbusPDU] | None:
        """Use `function_code` to determine the class of the PDU."""
        if (func_code := int(data[1])) & 0x80:
            return ExceptionResponse
        if not (pdu := self.pdu_table.get(func_code, (None, None))[self.pdu_inx]):
            return None
        if (sub_func_code := pdu.decode_sub_function_code(data)) < 0:
            return pdu
        return self.pdu_sub_table[func_code].get(sub_func_code, (None, None))[self.pdu_inx]

    def list_function_codes(self):
        """Return list of function codes."""
        return list(self.pdu_table)

    @classmethod
    def add_pdu(cls, req: type[ModbusPDU], resp: type[ModbusPDU]):
        """Register request/response."""
        cls.pdu_table[req.function_code] = (req, resp)

    @classmethod
    def add_sub_pdu(cls, req: type[ModbusPDU], resp: type[ModbusPDU]):
        """Register request/response."""
        if req.function_code not in cls.pdu_sub_table:
            cls.pdu_sub_table[req.function_code] = {}
        cls.pdu_sub_table[req.function_code][req.sub_function_code] = (req, resp)

    def register(self, custom_class: type[ModbusPDU]) -> None:
        """Register a function and sub function class with the decoder."""
        if not issubclass(custom_class, ModbusPDU):
            raise MessageRegisterException(
                f'"{custom_class.__class__.__name__}" is Not a valid Modbus Message'
                ". Class needs to be derived from "
                "`pymodbus.pdu.ModbusPDU` "
            )
        if "pdu_table" not in self.__dict__:
            self.pdu_table = copy.deepcopy(DecodePDU.pdu_table)
        self.pdu_table[custom_class.function_code] = (custom_class, custom_class)

    def decode(self, frame: bytes) -> ModbusPDU | None:
        """Decode a frame."""
        try:
            if (function_code := int(frame[0])) > 0x80:
                pdu_exp = ExceptionResponse(function_code & 0x7F)
                pdu_exp.decode(frame[1:])
                return pdu_exp
            if not (pdu_class := self.pdu_table.get(function_code, (None, None))[self.pdu_inx]):
                Log.debug("decode PDU failed for function code {}", function_code)
                raise ModbusException(f"Unknown response {function_code}")
            pdu = pdu_class()
            pdu.decode(frame[1:])
            if pdu.sub_function_code >= 0:
                lookup = self.pdu_sub_table.get(pdu.function_code, {})
                if sub_class := lookup.get(pdu.sub_function_code, (None,None))[self.pdu_inx]:
                    pdu = sub_class()
                    pdu.decode(frame[1:])
            Log.debug("decoded PDU function_code({} sub {}) -> {} ", pdu.function_code, pdu.sub_function_code, str(pdu))
            return pdu
        except (ModbusException, ValueError, IndexError) as exc:
            Log.warning("Unable to decode frame {}", exc)
        return None
