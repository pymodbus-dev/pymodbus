"""Modbus Request/Response Decoders."""
from __future__ import annotations

from pymodbus.exceptions import MessageRegisterException, ModbusException
from pymodbus.logging import Log

from .pdu import ExceptionResponse, ModbusPDU


class DecodePDU:
    """Decode pdu requests/responses (server/client)."""

    _pdu_class_table: set[tuple[type[ModbusPDU], type[ModbusPDU]]] = set()
    _pdu_sub_class_table: set[tuple[type[ModbusPDU], type[ModbusPDU]]] = set()

    def __init__(self, is_server: bool) -> None:
        """Initialize function_tables."""
        inx = 0 if is_server else 1
        self.lookup: dict[int, type[ModbusPDU]] = {cl[inx].function_code: cl[inx] for cl in self._pdu_class_table}
        self.sub_lookup: dict[int, dict[int, type[ModbusPDU]]] = {}
        for f in self._pdu_sub_class_table:
            if (function_code := f[inx].function_code) not in self.sub_lookup:
                self.sub_lookup[function_code] = {f[inx].sub_function_code: f[inx]}
            else:
                self.sub_lookup[function_code][f[inx].sub_function_code] = f[inx]

    def lookupPduClass(self, data: bytes) -> type[ModbusPDU] | None:
        """Use `function_code` to determine the class of the PDU."""
        func_code = int(data[1])
        if func_code & 0x80:
            return ExceptionResponse
        if func_code == 0x2B:  # mei message, sub_function_code is 1 byte
            sub_func_code = int(data[2])
            return self.sub_lookup[func_code].get(sub_func_code, None)
        if func_code == 0x08:  # diag message,  sub_function_code is 2 bytes
            sub_func_code = int(data[3])
            return self.sub_lookup[func_code].get(sub_func_code, None)
        return self.lookup.get(func_code, None)

    @classmethod
    def add_pdu(cls, req: type[ModbusPDU], resp: type[ModbusPDU]):
        """Register request/response."""
        cls._pdu_class_table.add((req, resp))

    @classmethod
    def add_sub_pdu(cls, req: type[ModbusPDU], resp: type[ModbusPDU]):
        """Register request/response."""
        cls._pdu_sub_class_table.add((req, resp))

    def register(self, custom_class: type[ModbusPDU]) -> None:
        """Register a function and sub function class with the decoder."""
        if not issubclass(custom_class, ModbusPDU):
            raise MessageRegisterException(
                f'"{custom_class.__class__.__name__}" is Not a valid Modbus Message'
                ". Class needs to be derived from "
                "`pymodbus.pdu.ModbusPDU` "
            )
        self.lookup[custom_class.function_code] = custom_class
        if custom_class.sub_function_code >= 0:
            if custom_class.function_code not in self.sub_lookup:
                self.sub_lookup[custom_class.function_code] = {}
            self.sub_lookup[custom_class.function_code][
                custom_class.sub_function_code
            ] = custom_class

    def decode(self, frame: bytes) -> ModbusPDU | None:
        """Decode a frame."""
        try:
            if (function_code := int(frame[0])) > 0x80:
                pdu_exp = ExceptionResponse(function_code & 0x7F)
                pdu_exp.decode(frame[1:])
                return pdu_exp
            if not (pdu_class := self.lookup.get(function_code, None)):
                Log.debug("decode PDU failed for function code {}", function_code)
                raise ModbusException(f"Unknown response {function_code}")
            pdu = pdu_class()
            pdu.decode(frame[1:])
            if pdu.sub_function_code >= 0:
                lookup = self.sub_lookup.get(pdu.function_code, {})
                if sub_class := lookup.get(pdu.sub_function_code, None):
                    pdu = sub_class()
                    pdu.decode(frame[1:])
            Log.debug("decoded PDU function_code({} sub {}) -> {} ", pdu.function_code, pdu.sub_function_code, str(pdu))
            return pdu
        except (ModbusException, ValueError, IndexError) as exc:
            Log.warning("Unable to decode frame {}", exc)
        return None
