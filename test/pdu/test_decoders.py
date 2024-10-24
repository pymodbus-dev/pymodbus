"""Test factory."""
import pytest

from pymodbus.exceptions import MessageRegisterException
from pymodbus.pdu import ModbusPDU
from pymodbus.pdu.decoders import DecodePDU


class TestModbusPDU:
    """Test ModbusPDU."""

    client = DecodePDU(False)
    server = DecodePDU(True)
    requests = (
        (0x01, b"\x01\x00\x01\x00\x01"),  # read coils
        (0x02, b"\x02\x00\x01\x00\x01"),  # read discrete inputs
        (0x03, b"\x03\x00\x01\x00\x01"),  # read holding registers
        (0x04, b"\x04\x00\x01\x00\x01"),  # read input registers
        (0x05, b"\x05\x00\x01\x00\x01"),  # write single coil
        (0x06, b"\x06\x00\x01\x00\x01"),  # write single register
        (0x07, b"\x07"),  # read exception status
        (0x08, b"\x08\x00\x00\x00\x00"),  # read diagnostic
        (0x0B, b"\x0b"),  # get comm event counters
        (0x0C, b"\x0c"),  # get comm event log
        (0x0F, b"\x0f\x00\x01\x00\x08\x01\x00\xff"),  # write multiple coils
        (0x10, b"\x10\x00\x01\x00\x02\x04\0xff\xff"),  # write multiple registers
        (0x11, b"\x11"),  # report slave id
        (
            0x14,
            b"\x14\x0e\x06\x00\x04\x00\x01\x00\x02\x06\x00\x03\x00\x09\x00\x02",
        ),  # read file record
        (
            0x15,
            b"\x15\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d",
        ),  # write file record
        (0x16, b"\x16\x00\x01\x00\xff\xff\x00"),  # mask write register
        (
            0x17,
            b"\x17\x00\x01\x00\x01\x00\x01\x00\x01\x02\x12\x34",
        ),  # r/w multiple regs
        (0x18, b"\x18\x00\x01"),  # read fifo queue
        (0x2B, b"\x2b\x0e\x01\x00"),  # read device identification
    )

    responses = (
        (0x01, b"\x01\x01\x01"),  # read coils
        (0x02, b"\x02\x01\x01"),  # read discrete inputs
        (0x03, b"\x03\x02\x01\x01"),  # read holding registers
        (0x04, b"\x04\x02\x01\x01"),  # read input registers
        (0x05, b"\x05\x00\x01\x00\x01"),  # write single coil
        (0x06, b"\x06\x00\x01\x00\x01"),  # write single register
        (0x07, b"\x07\x00"),  # read exception status
        (0x08, b"\x08\x00\x00\x00\x00"),  # read diagnostic
        (0x0B, b"\x0b\x00\x00\x00\x00"),  # get comm event counters
        (0x0C, b"\x0c\x08\x00\x00\x01\x08\x01\x21\x20\x00"),  # get comm event log
        (0x0F, b"\x0f\x00\x01\x00\x08"),  # write multiple coils
        (0x10, b"\x10\x00\x01\x00\x02"),  # write multiple registers
        (0x11, b"\x11\x03\x05\x01\x54"),  # report slave id (device specific)
        (
            0x14,
            b"\x14\x0c\x05\x06\x0d\xfe\x00\x20\x05\x06\x33\xcd\x00\x40",
        ),  # read file record
        (
            0x15,
            b"\x15\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d",
        ),  # write file record
        (0x16, b"\x16\x00\x01\x00\xff\xff\x00"),  # mask write register
        (0x17, b"\x17\x02\x12\x34"),  # read/write multiple registers
        (0x18, b"\x18\x00\x01\x00\x01\x00\x00"),  # read fifo queue
        (
            0x2B,
            b"\x2b\x0e\x01\x01\x00\x00\x01\x00\x01\x77",
        ),  # read device identification
    )

    exceptions = (
        (0x81, b"\x81\x01\xd0\x50"),  # illegal function exception
        (0x82, b"\x82\x02\x90\xa1"),  # illegal data address exception
        (0x83, b"\x83\x03\x50\xf1"),  # illegal data value exception
        (0x84, b"\x84\x04\x13\x03"),  # skave device failure exception
        (0x85, b"\x85\x05\xd3\x53"),  # acknowledge exception
        (0x86, b"\x86\x06\x93\xa2"),  # slave device busy exception
        (0x87, b"\x87\x08\x53\xf2"),  # memory parity exception
        (0x88, b"\x88\x0a\x16\x06"),  # gateway path unavailable exception
        (0x89, b"\x89\x0b\xd6\x56"),  # gateway target failed exception
    )

    bad = (
        (0x80, b"\x80\x00\x00\x00"),  # Unknown Function
        (0x81, b"\x81\x00\x00\x00"),  # error message
    )


    @pytest.mark.parametrize(("code", "frame"), list(responses) + list(exceptions))
    def test_client_lookup(self, code, frame):
        """Test lookup for responses."""
        data = b'\x01' + frame
        pdu = self.client.lookupPduClass(data)
        assert pdu
        if not code & 0x80:
            assert pdu.function_code == code

    @pytest.mark.parametrize(("code", "frame"), list(requests))
    def test_server_lookup(self, code, frame):
        """Test lookup for requests."""
        data = b'\x01' + frame
        pdu = self.client.lookupPduClass(data)
        assert pdu
        if not code & 0x80:
            assert pdu.function_code == code

    @pytest.mark.parametrize(("code", "frame"), list(responses) + list(exceptions))
    def test_client_decode(self, code, frame):
        """Test lookup for responses."""
        pdu = self.client.decode(frame)
        assert pdu.function_code == code

    @pytest.mark.parametrize(("code", "frame"), list(requests))
    def test_server_decode(self, code, frame):
        """Test lookup for requests."""
        pdu = self.server.decode(frame)
        assert pdu.function_code == code

    @pytest.mark.parametrize(("frame"), [b'', b'NO FRAME'])
    @pytest.mark.parametrize(("decoder"), [server, client])
    def test_decode_bad_frame(self, decoder, frame):
        """Test lookup bad frames."""
        assert not decoder.decode(frame)

    def test_decode_unknown_sub(self):
        """Test for unknown sub code."""
        assert self.client.decode(b"\x08\x00\xF0\xF0\x00")

    @pytest.mark.parametrize(("decoder"), [server, client])
    def test_register_custom_request(self, decoder):
        """Test server register custom request."""

        class CustomRequestResponse(ModbusPDU):
            """Custom request."""

            function_code = 0x70

            def encode(self):
                """Encode."""
                return self.function_code.to_bytes(1) + b'123'

            def decode(self, _data):
                """Decode."""

        class NoCustomRequestResponse:
            """Custom request."""

            function_code = 0x70

            def encode(self):
                """Encode."""

            def decode(self, _data):
                """Decode."""

        decoder.register(CustomRequestResponse)
        data = b'\x01' + CustomRequestResponse().encode()
        assert decoder.lookupPduClass(data)
        CustomRequestResponse.sub_function_code = 0xF7
        decoder.register(CustomRequestResponse)
        CustomRequestResponse.sub_function_code = 0xF4
        decoder.register(CustomRequestResponse)
        data = b'\x01' + CustomRequestResponse().encode()
        assert self.server.lookupPduClass(data)
        with pytest.raises(MessageRegisterException):
            decoder.register(NoCustomRequestResponse)
