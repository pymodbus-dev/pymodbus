"""Singular tests."""

from typing import cast
from unittest import mock

import pytest

import pymodbus.pdu.data_message as data_msg
import pymodbus.pdu.diag_message as diag_msg
import pymodbus.pdu.other_message as file_msg
import pymodbus.pdu.other_message as other_msg
from pymodbus import ModbusException, ModbusIOException
from pymodbus.constants import CLEAR_STATISTICS, DeviceInformation, ExcCodes
from pymodbus.pdu import DecodePDU, ModbusControlBlock, PDUexception


class TestPDUExtras:
    """Modbus PDU singular tests."""

    @pytest.mark.parametrize(
        ("frame", "exp_count"),
        [
            (b"\x01\x01\x00\x00\x07\xd1", 2001),
            (b"\x01\x02\x00\x00\x07\xd1", 2001),
        ],
    )
    def test_bit_1(self, frame, exp_count):
        """Decoding must not raise for an over-max bit read quantity."""
        assert DecodePDU(True).decode(frame).count == exp_count

    @pytest.mark.parametrize(
        "frame",
        [
            b"\x00\x0f\x00\x01\x00\x10\x01\xff",
            b"\x00\x0f\x00\x01\x00\x08\x02\xff\x00",
            b"\x00\x0f\x00\x01\x00\x08\x01",
            b"\x00\x0f\x00\x01\x00\x08\x01\xff\x00",
        ],
    )
    async def test_bit_2(self, frame):
        """Test write multiple coils rejects inconsistent byte counts."""
        request = data_msg.PDUwriteMultipleCoils(True, 0)
        request.from_bytes(frame)
        mx = mock.AsyncMock(return_value=ExcCodes.ILLEGAL_VALUE)
        result = await request.build_response(mx, mx)
        assert isinstance(result, PDUexception)
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE

    @pytest.mark.parametrize("value", [b"\x00\x01", b"\x00\xff", b"\xff\xff"])
    async def test_bit_3(self, value):
        """A value other than 0x0000 or 0xFF00 must answer 0x03 and leave the coil."""
        request = data_msg.PDUwriteSingleCoil(True, 0)
        request.from_bytes(b"\x00\x05\x00\x02" + value)
        result = await request.build_response(
            mock.AsyncMock(return_value=[True]), mock.AsyncMock(return_value=0)
        )
        assert result.function_code == 0x85
        assert isinstance(result, PDUexception)
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE

    @pytest.mark.parametrize(
        ("value", "bit"), [(b"\xff\x00", True), (b"\x00\x00", False)]
    )
    async def test_bit_4(self, value, bit):
        """0xFF00 and 0x0000 are written as ON and OFF."""
        request = data_msg.PDUwriteSingleCoil(False, 1)
        request.from_bytes(b"\x01\x05\x00\x02" + value)
        x_set = mock.AsyncMock(return_value=0)
        result = await request.build_response(mock.AsyncMock(return_value=[bit]), x_set)
        assert result.to_bytes() == b"\x01\x05\x00\x02" + value
        x_set.assert_awaited_once_with(1, 5, 2, [bit])

    def test_bit_5(self):
        """Detect conflict byte and bit count."""
        pdu = data_msg.PDUreadCoils(False, 0)
        assert pdu.from_bytes(b"\x00\x01\x02\x03")

    def test_bit_6(self):
        """Detect write with multiple coils."""
        pdu = data_msg.PDUwriteSingleCoil(True, 0, address=1, bits=[True, True])
        pdu.count = 1
        with pytest.raises(ModbusIOException):
            pdu.to_bytes()

    def test_reg_1(self):
        """Detect read with wrong byte count."""
        pdu = data_msg.PDUreadHoldingRegisters(False, 0)
        assert pdu.from_bytes(b"\x01\x03\x00\x75\x00\x03\x00\x03")
        pdu = data_msg.PDUwriteMultipleRegisters(True, 0)
        assert pdu.from_bytes(b"\x01\x10\x00\x75\x00\x03\x08\x00\x6f\x00\x79\x00\x83")
        assert pdu.from_bytes(b"\x01\x10\x00\x75\x00\x03\x04\x00\x6f\x00\x79\x00\x83")

    def test_reg_2(self):
        """Detect write with multiple registers."""
        for pdu in (
            data_msg.PDUwriteSingleRegister(True, 0, address=1, registers=[True, True]),
            data_msg.PDUwriteMultipleRegisters(
                True, 0, address=1, registers=[True, True]
            ),
        ):
            pdu.count = 1
            with pytest.raises(ModbusIOException):
                pdu.to_bytes()

    def test_reg_3(self):
        """Detect write with multiple registers."""
        for regs in ([], [False] * 122):
            pdu = data_msg.PDUreadWriteMultipleRegisters(
                True, 0, address=1, registers=regs
            )
            with pytest.raises(ModbusIOException):
                pdu.to_bytes()
        for addr in (-1, 65536):
            pdu = data_msg.PDUreadWriteMultipleRegisters(
                True, 0, address=1, write_address=addr, registers=[123]
            )
            with pytest.raises(ModbusIOException):
                pdu.to_bytes()
        pdu = data_msg.PDUreadWriteMultipleRegisters(False, 0)
        assert pdu.from_bytes(b"\x01\x17\x02\x00\x6f\x00\x70")
        pdu = data_msg.PDUreadWriteMultipleRegisters(True, 0)
        assert pdu.from_bytes(b"\x01\x17\x00\x11\x00\x02\x00\x19\x00\x02\x04\x00\x6f")
        assert pdu.from_bytes(
            b"\x01\x17\x00\x11\x00\x02\x00\x19\x00\x03\x04\x00\x6f\x00\x70"
        )

    def test_reg_4(self):
        """Detect write with multiple registers."""
        for masks in ((-1, 0), (0, -1), (0x1FFFF, 0), (0, 0x1FFFF)):
            pdu = data_msg.PDUmaskWriteRegister(
                True, 0, address=1, and_mask=masks[0], or_mask=masks[1]
            )
            with pytest.raises(ModbusIOException):
                pdu.to_bytes()

    def test_diag_1(self):
        """Detect diag message."""
        pdu = diag_msg.PDUdiagnostic(True, 0, message=123)
        assert pdu.message == b"\x00\x7b"
        pdu = diag_msg.PDUdiagnostic(True, 0, message=[123, 0])
        assert pdu.message == b"\x00\x7b\x00\x00"

    async def test_diag_2(self):
        """Detect diag message."""
        pdu = diag_msg.PDUgetClearModbusPlus(True, 0, message=CLEAR_STATISTICS)
        v = mock.AsyncMock()
        await pdu.build_response(v, v)

    def test_diag_3(self):
        """Test basic bit message encoding/decoding."""
        msg = b"\x00\x2b\x0e\x01\x00\x01\x00\x01\x00\x01\x00"
        pdu = DecodePDU(True).decode(msg[:5])
        assert isinstance(pdu, diag_msg.PDUreadDeviceInformation)
        assert pdu.calculatePduSize(msg) == 5
        pdu = diag_msg.PDUreadDeviceInformation(False, 0)
        assert pdu.calculatePduSize(msg[:7]) == 0
        assert pdu.calculatePduSize(msg[:8]) == 0
        assert pdu.calculatePduSize(msg) == 11

    async def test_diag_4(self):
        """Test basic bit message encoding/decoding."""
        TEST_VERSION = b"v2.1.12"
        TEST_MESSAGE = b"\x00\x07Company\x01\x07Product\x02\x07v2.1.12"

        control = ModbusControlBlock()
        control.Identity.VendorName = "Company"
        control.Identity.ProductCode = "Product"
        control.Identity.MajorMinorRevision = TEST_VERSION
        control.Identity.update({0x81: ["Test", "Repeated"]})

        handle = diag_msg.PDUreadDeviceInformation(True, 0)
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert isinstance(result, diag_msg.PDUreadDeviceInformation)
        assert result.information[0x00] == "Company"
        assert result.information[0x01] == "Product"
        assert result.information[0x02] == TEST_VERSION
        with pytest.raises(KeyError):
            _ = result.information[0x81]

        handle = diag_msg.PDUreadDeviceInformation(
            True, 0, read_code=DeviceInformation.SPECIFIC, object_id=0x00
        )
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert cast(diag_msg.PDUreadDeviceInformation, result).information == {
            0x00: "Company"
        }

        handle = diag_msg.PDUreadDeviceInformation(
            True, 0, read_code=DeviceInformation.EXTENDED, object_id=0x80
        )
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert cast(diag_msg.PDUreadDeviceInformation, result).information[0x81] == [
            "Test",
            "Repeated",
        ]
        message = b"\x00\x2b\x0e\x01\x83\x00\x00\x03"
        message += TEST_MESSAGE
        dataset = {
            0x00: "Company",
            0x01: "Product",
            0x02: TEST_VERSION,
        }
        handle = diag_msg.PDUreadDeviceInformation(
            False, 0, read_code=DeviceInformation.BASIC, information=dataset
        )
        result = handle.to_bytes()
        assert result == message
        assert "PDUreadDeviceInformation" in str(handle)

        dataset = {
            0x00: "Company",
            0x01: "Product",
            0x02: TEST_VERSION,
            0x81: ["Test", "Repeated"],
            0x82: PDUexception(0, 0x01, 0),
        }
        message = b"\x00\x2b\x0e\x03\x83\x00\x00\x06"
        message += TEST_MESSAGE
        message += b"\x81\x04Test\x81\x08Repeated\x82\x03\x00\x81\x00"
        handle = diag_msg.PDUreadDeviceInformation(
            False,
            0,
            read_code=DeviceInformation.EXTENDED,
            information=dataset,
        )
        result = handle.to_bytes()
        assert result == message
        longstring = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing "
            "elit. Vivamus rhoncus massa turpis, sit amet ultrices"
            " orci semper ut. Aliquam tristique sapien in lacus "
            "pharetra, in convallis nunc consectetur. Nunc velit "
            "elit, vehicula tempus tempus sed. "
        )
        message = b"\x00\x2b\x0e\x01\x83\xff\x80\x03"
        message += TEST_MESSAGE
        dataset = {
            0x00: "Company",
            0x01: "Product",
            0x02: TEST_VERSION,
            0x80: longstring,
        }
        handle = diag_msg.PDUreadDeviceInformation(
            False, 0, read_code=DeviceInformation.BASIC, information=dataset
        )
        result = handle.to_bytes()
        assert result == message
        assert "PDUreadDeviceInformation" in str(handle)
        message = b"\x00\x2b\x0e\x01\x01\x00\x00\x05"
        message += TEST_MESSAGE
        message += b"\x81\x04Test\x81\x08Repeated\x81\x07Another"
        handle = diag_msg.PDUreadDeviceInformation(
            False, 0, read_code=0x00, information={}
        )
        handle.from_bytes(message)
        assert handle.read_code == DeviceInformation.BASIC
        assert handle.conformity == 0x01
        assert handle.information[0x00] == b"Company"
        assert handle.information[0x01] == b"Product"
        assert handle.information[0x02] == TEST_VERSION
        assert handle.information[0x81] == [b"Test", b"Repeated", b"Another"]

    async def test_diag_5(self):
        """Test basic bit message encoding/decoding."""
        handle = diag_msg.PDUreadDeviceInformation(True, 0)
        handle.read_code = -1
        assert (
            await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0xAB
        handle.read_code = 0x05
        assert (
            await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0xAB
        handle.object_id = -1
        assert (
            await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0xAB
        handle.object_id = 0x100
        assert (
            await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0xAB
        handle = diag_msg.PDUreadDeviceInformation(
            True, 0, read_code=DeviceInformation.SPECIFIC, object_id=0x54
        )
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert isinstance(result, PDUexception)
        assert result.exception_code == ExcCodes.ILLEGAL_ADDRESS
        ModbusControlBlock().Identity[0xFE] = ""
        handle = diag_msg.PDUreadDeviceInformation(
            True, 0, read_code=DeviceInformation.SPECIFIC, object_id=0xFE
        )
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert isinstance(result, PDUexception)
        assert result.exception_code == ExcCodes.ILLEGAL_ADDRESS

    def test_other_1(self):
        """Test get comm event log with events."""
        response = other_msg.PDUgetCommEventLog(False, 0, events=[0x12, 0x34, 0x56])
        assert (
            response.to_bytes() == b"\x00\x0c\x09\x00\x00\x00\x00\x00\x00\x12\x34\x56"
        )
        response.from_bytes(b"\x00\x0c\x09\x00\x00\x00\x12\x00\x12\x12\x34\x56")
        assert response.status
        assert response.message_count == 0x12
        assert response.event_count == 0x12
        assert response.events == [0x12, 0x34, 0x56]

    async def test_other_2(self):
        """Test report device_id request."""
        with mock.patch("pymodbus.pdu.other_message.DeviceInformationFactory") as dif:
            # First test regular identity strings
            identity = {
                0x00: "VN",  # VendorName
                0x01: "PC",  # ProductCode
                0x02: "REV",  # MajorMinorRevision
                0x03: "VU",  # VendorUrl
                0x04: "PN",  # ProductName
                0x05: "MN",  # ModelName
                0x06: "UAN",  # UserApplicationName
                0x07: "RA",  # reserved
                0x08: "RB",  # reserved
            }
            dif.get.return_value = identity
            expected_identity = "-".join(identity.values()).encode()

            request = other_msg.PDUreportDeviceId(True, 0)
            response = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
            assert (
                cast(other_msg.PDUreportDeviceId, response).identifier
                == expected_identity
            )

            # Change to byte strings and test again (final result should be the same)
            identity2 = {
                0x00: b"VN",  # VendorName
                0x01: b"PC",  # ProductCode
                0x02: b"REV",  # MajorMinorRevision
                0x03: b"VU",  # VendorUrl
                0x04: b"PN",  # ProductName
                0x05: b"MN",  # ModelName
                0x06: b"UAN",  # UserApplicationName
                0x07: b"RA",  # reserved
                0x08: b"RB",  # reserved
            }
            dif.get.return_value = identity2

            request = other_msg.PDUreportDeviceId(True, 0)
            response = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
            assert (
                cast(other_msg.PDUreportDeviceId, response).identifier
                == expected_identity
            )

    async def test_other_3(self):
        """Test report device_id."""
        with mock.patch("pymodbus.pdu.other_message.DeviceInformationFactory") as dif:
            dif.get.return_value = {}
            request = other_msg.PDUreportDeviceId(True, 0)
            request.from_bytes(b"\x00\x11\x12")
            response = other_msg.PDUreportDeviceId(
                False,
                0,
                identifier=cast(
                    other_msg.PDUreportDeviceId,
                    await request.build_response(mock.AsyncMock(), mock.AsyncMock()),
                ).identifier,
                status=True,
            )

            assert response.to_bytes() == b"\x00\x11\tPymodbus\xff"
            response.from_bytes(b"\tPymodbus\xff")
            assert response.status
            assert response.identifier == b"Pymodbus"
            response.from_bytes(b"\x00\x11\x03\x12\x00\x00")
            assert response.identifier == b"\x12\x00"
            response.status = False
            assert response.to_bytes() == b"\x00\x11\x03\x12\x00\x00"

    def test_other_4(self):
        """Test decode( to_bytes()) keeps identifier and status unchanged."""
        for identifier, status in ((b"Pymodbus", True), (b"\x12", False)):
            sent = other_msg.PDUreportDeviceId(
                False, 0, identifier=identifier, status=status
            )
            received = other_msg.PDUreportDeviceId(False, 0)
            received.from_bytes(sent.to_bytes())
            assert received.identifier == identifier
            assert received.status == status

    def test_other_5(self):
        """Test byte count pointing outside the received data raises."""
        response = other_msg.PDUreportDeviceId(False, 0)
        for frame in (b"\x00\x11\x00\x12\xff", b"\x00\x11\x04\x12\xff"):
            assert response.from_bytes(frame)

    def test_other_6(self):
        """Test byte count pointing outside the received data raises."""
        response = other_msg.PDUreadFifoQueue(False, 0)
        assert response.calculatePduSize(b"\x01\x18\x00") == 0

    def test_file_1(self):
        """Test file record length generation."""
        assert (
            file_msg.FileRecord(
                file_number=0x01, record_number=0x02, record_data=b"\x00\x01\x02\x04"
            ).record_length
            == 0x02
        )
        with pytest.raises(ModbusException):
            file_msg.FileRecord(record_length=12, record_data=b"\x00\x01\x02\x04")
        with pytest.raises(ModbusException):
            file_msg.FileRecord(record_length=11)

    @pytest.mark.parametrize("server", [True, False])
    def test_file_2(self, server):
        """Test basic bit message encoding/decoding."""
        records = [
            file_msg.FileRecord(
                file_number=0x01, record_number=0x02, record_data=b"\x00\x01\x02\x03"
            )
        ]
        result = file_msg.PDUreadFileRecord(server, 0, records=records).to_bytes()
        if server:
            assert result == b"\x00\x14\x07\x06\x00\x01\x00\x02\x00\x00"
        else:
            assert result == b"\x00\x14\x06\x05\x06\x00\x01\x02\x03"

    def test_file_3(self):
        """Test file_msg.PDUreadFileRecord raises ModbusException on oversized byte_count."""
        handle = file_msg.PDUreadFileRecord(False, 0)
        with pytest.raises(ModbusException):
            handle.from_bytes(
                bytes([0x00, 0x15, 0xFF, 0x06, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01])
            )
        with pytest.raises(ModbusException):
            handle.from_bytes(
                bytes(
                    [
                        0x00,
                        0x15,
                        0xFF,
                        0x06,
                        0x00,
                        0x01,
                        0x00,
                        0x00,
                        0x00,
                        0x01,
                        0x00,
                        0x00,
                    ]
                )
            )

    def test_file_4(self):
        """Test file_msg.PDUreadFifoQueue raises ModbusException on oversized count."""
        handle = file_msg.PDUreadFileRecord(True, 0)
        assert handle.from_bytes(b"\x00\x14\x07\x06\x00\x01\x00\x02\x00\x00\x00\x00")

    def test_file_5(self):
        """Test basic bit message encoding/decoding."""
        records = [
            file_msg.FileRecord(
                file_number=0x01, record_number=0x02, record_data=b"\x00\x01\x02\x03"
            )
        ]
        handle = file_msg.PDUwriteFileRecord(False, 0, records=records)
        result = handle.to_bytes()
        assert result == b"\x00\x15\x0b\x06\x00\x01\x00\x02\x00\x02\x00\x01\x02\x03"

    def test_file_6(self):
        """Test file_msg.PDUreadFifoQueue raises ModbusException on oversized count."""
        handle = file_msg.PDUwriteFileRecord(True, 0)
        assert handle.from_bytes(
            b"\x01\x15\x0e\x06\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00"
        )

    def test_file_7(self):
        """Test file_msg.PDUreadFifoQueue raises ModbusException on oversized count."""
        handle = file_msg.PDUreadFifoQueue(False, 0)
        assert handle.from_bytes(bytes([0x00, 0x18, 0x00, 0x00, 0xFF, 0xFF]))

    def test_file_8(self):
        """Test file_msg.PDUreadFifoQueue raises ModbusException on oversized count."""
        handle = file_msg.PDUreadFifoQueue(False, 0)
        assert handle.from_bytes(b"\x01\x18\x00\x06\x00\x02\x00\x7b\x01\xc8\x00")
        assert handle.from_bytes(b"\x01\x18\x00\x06\x00\x04\x00\x7b\x01\xc8")

    @pytest.mark.parametrize(
        ("server", "frame"),
        [
            (True, b"\x00\x14\x14\x10"),  # read file record, byte count past the frame
            (True, b"\x00\x14\x15\x10"),  # write file record, byte count past the frame
            (
                False,
                b"\x00\x14\x18\x00\x06\x00\x05\x00\x01",
            ),  # fifo count past the frame
        ],
    )
    def test_file_9(self, server, frame):
        """Test bad file record frames fail like other undecodable frames."""
        with pytest.raises(ModbusIOException):
            DecodePDU(server).decode(frame)
