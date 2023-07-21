"""
How to explain pymodbus logs using https://rapidscada.net/modbus/ and requests.

Created on 7/19/2023 to support Python 3.8 to 3.11 on macOS, Ubuntu, or Windows.
"""

import contextlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import List, Optional, Tuple, Union
from urllib import request
from urllib.error import HTTPError


RAPID_SCADA_URL = "https://rapidscada.net/modbus/"


@dataclass(frozen=True)
class ParsedModbusResult:  # pylint: disable=too-many-instance-attributes
    """Simple data structure to hold post response of Rapid SCADA."""

    transaction_id: int
    length: int
    unit_id: int
    func_code: int
    is_receive: bool
    zero_index_reg: Optional[int] = None
    quantity: Optional[int] = None
    byte_count: Optional[int] = None
    registers: Optional[List[int]] = None

    def summarize(self) -> dict:
        """Get a summary representation for readability."""
        summary = {"is_receive": self.is_receive}
        if self.zero_index_reg is not None:
            summary["one_index_reg"] = self.zero_index_reg + 1
        if self.registers is not None:
            summary["registers"] = self.registers
        return summary


def explain_with_rapid_scada(
    packet: str,
    is_modbus_tcp: bool = True,
    is_receive: bool = False,
    timeout: Union[float, Tuple[float, float], None] = 15.0,
) -> ParsedModbusResult:
    """
    Explain a Modbus packet using https://rapidscada.net/modbus/.

    Args:
        packet: Packet from pymodbus logs.
        is_modbus_tcp: Set True (default) for Modbus TCP or False for Modbus RTU.
        is_receive: Set True if pymodbus log says RECV, otherwise False for SEND.
        timeout: Optional timeout (sec) for the HTTP post, defaulted to 15-sec.

    Returns:
        Parsed data from Rapid SCADA Modbus Parser.
    """

    class NonEmptyDataFromHTML(HTMLParser):
        """Aggregate all data from an HTML blob."""

        def __init__(self, *, convert_charrefs=True):
            super().__init__(convert_charrefs=convert_charrefs)
            self._data = []

        @property
        def data(self) -> List[str]:
            return self._data

        def handle_data(self, data: str) -> None:
            if not data.strip():
                return
            self._data.append(data.strip())

    data_packet = "+".join(
        [f"{int(hex_str, base=16):02X}" for hex_str in packet.split(" ")],
    )
    with request.urlopen(  # noqa: S310
        request.Request(
            f"{RAPID_SCADA_URL}?ModbusMode={int(is_modbus_tcp)}"
            f"&DataDirection={int(is_receive)}&DataPackage={data_packet}",
            method="POST",
        ),
        timeout=timeout,
    ) as response:
        if response.status != 200:
            raise HTTPError(
                url=response.url,
                code=response.status,
                msg=response.reason,
                hdrs=response.headers,
                fp=response.fp,
            )
        response_data = response.read().decode()
    parser = NonEmptyDataFromHTML()
    parser.feed(response_data)

    # pylint: disable-next=dangerous-default-value
    def get_next_field(prior_field: str, data: List[str] = parser.data) -> str:
        return data[data.index(prior_field) + 1]

    def parse_next_field(prior_field: str, split_index: int = 0) -> int:
        return int(get_next_field(prior_field).split(" ")[split_index], base=16)

    base_result_data = {
        "transaction_id": parse_next_field("Transaction identifier"),
        "length": parse_next_field("Length"),
        "unit_id": parse_next_field("Unit identifier"),
        "func_code": parse_next_field("Function code"),
        "is_receive": is_receive,
    }
    is_receive_fn_code: Tuple[bool, int] = is_receive, base_result_data["func_code"]
    if is_receive_fn_code in [(False, 0x03), (True, 0x10)]:
        return ParsedModbusResult(
            **base_result_data,
            zero_index_reg=parse_next_field("Starting address", split_index=1),
            quantity=parse_next_field("Quantity"),
        )
    if is_receive_fn_code in [(False, 0x10), (True, 0x03)]:
        next_field = "Register value" if is_receive else "Registers value"
        return ParsedModbusResult(
            **base_result_data,
            byte_count=parse_next_field("Byte count"),
            registers=[
                int(raw_value.split(" ")[0], base=16)
                for raw_value in get_next_field(next_field).split(", ")
            ],
        )
    raise NotImplementedError(
        f"Unhandled case with {is_receive=} and {parser.data=}.",
    )


def annotate_pymodbus_logs(file: Union[str, os.PathLike]) -> None:
    """Annotate a pymodbus log file in-place with explanations."""
    with open(file, encoding="utf-8") as in_file, tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False
    ) as out_file:
        for i, line in enumerate(in_file):
            if "Running transaction" in line and i > 0:
                out_file.write("\n")
            out_file.write(line)
            if "SEND:" in line:
                explained = explain_with_rapid_scada(
                    packet=line.split("SEND:")[1].strip(),
                )
                out_file.write(
                    f"Send explained: {explained}\n"
                    f"Send summary: {explained.summarize()}\n",
                )
            if "RECV:" in line:
                explained = explain_with_rapid_scada(
                    packet=line.split("RECV:")[1].strip(),
                    is_receive=True,
                )
                out_file.write(
                    f"Receive explained: {explained}\n"
                    f"Receive summary: {explained.summarize()}\n",
                )
    # NOTE: per NamedTemporaryFile docs, the name cannot be reused on Windows
    # while the file is still open. So we have to use delete=False followed by
    # manually removing the temp file
    shutil.copyfile(out_file.name, file)
    with contextlib.suppress(FileNotFoundError):
        os.remove(out_file.name)
