"""Test transport."""

import pytest

from pymodbus.message.socket import MessageSocket


class TestMessageSocket:
    """Test message module."""

    @staticmethod
    @pytest.fixture(name="frame")
    def prepare_frame():
        """Return message object."""
        return MessageSocket([1], False)


    @pytest.mark.parametrize(
        ("packet", "used_len", "res_id", "res"),
        [
            (b':010100010001FC\r\n', 17, 1, b'\x01\x00\x01\x00\x01'),
            (b':00010001000AF4\r\n', 17, 0, b'\x01\x00\x01\x00\x0a'),
            (b':01010001000AF3\r\n', 17, 1, b'\x01\x00\x01\x00\x0a'),
            (b':61620001000A32\r\n', 17, 97, b'\x62\x00\x01\x00\x0a'),
            (b':01270001000ACD\r\n', 17, 1, b'\x27\x00\x01\x00\x0a'),
            (b':010100', 0, 0, b''), # short frame
            (b':00010001000AF4', 0, 0, b''),
            (b'abc:00010001000AF4', 3, 0, b''), # garble before frame
            (b'abc00010001000AF4', 17, 0, b''), # only garble
            (b':01010001000A00\r\n', 17, 0, b''),
        ],
    )
    def xtest_decode(self, frame, packet, used_len, res_id, res):
        """Test decode."""
        res_len, tid, dev_id, data = frame.decode(packet)
        assert res_len == used_len
        assert data == res
        assert not tid
        assert dev_id == res_id

    @pytest.mark.parametrize(
        ("data", "dev_id", "res_msg"),
        [
            (b'\x01\x05\x04\x00\x17', 1, b':010105040017DE\r\n'),
            (b'\x03\x07\x06\x00\x73', 2, b':0203070600737B\r\n'),
            (b'\x08\x00\x01', 3, b':03080001F4\r\n'),
        ],
    )
    def xtest_encode(self, frame, data, dev_id, res_msg):
        """Test encode."""
        msg = frame.encode(data, dev_id, 0)
        assert res_msg == msg
        assert dev_id == int(msg[1:3], 16)

    @pytest.mark.parametrize(
        ("data", "dev_id", "res_msg"),
        [
            (b'\x01\x05\x04\x00\x17', 1, b':010105040017DF\r\n'),
            (b'\x03\x07\x06\x00\x73', 2, b':0203070600737D\r\n'),
            (b'\x08\x00\x01', 3, b':03080001F7\r\n'),
        ],
    )
    def xtest_roundtrip(self, frame, data, dev_id, res_msg):
        """Test encode."""
        msg = frame.encode(data, dev_id, 0)
        res_len, _, res_id, res_data = frame.decode(msg)
        assert data == res_data
        assert dev_id == res_id
        assert res_len == len(res_msg)

    # def test_recv_split_packet():
    #     """Test receive packet."""
    #     response_ok = False
    #
    # def _handle_response(_reply):
    #     """Handle response."""
    #     nonlocal response_ok
    #     response_ok = True
    #
    #     message = bytearray(b"\x00\x01\x00\x00\x00\x0b\x01\x03\x08\x00\xb5\x12\x2f\x37\x21\x00\x03")
    #     for i in range(0, len(message)):
    #         part1 = message[:i]
    #         part2 = message[i:]
    #         response_ok = False
    #         framer = ModbusSocketFramer(ClientDecoder())
    #         if i:
    #             framer.processIncomingPacket(part1, _handle_response, slave=0)
    #             assert not response_ok, "Response should not be accepted"
    #         framer.processIncomingPacket(part2, _handle_response, slave=0)
    #         assert response_ok, "Response is valid, but not accepted"
    #
    # def test_recv_socket_exception_packet():
    #     """Test receive packet."""
    #     response_ok = False
    #
    #     def _handle_response(_reply):
    #         """Handle response."""
    #         nonlocal response_ok
    #         response_ok = True
    #
    #     message = bytearray(b"\x00\x02\x00\x00\x00\x03\x01\x84\x02")
    #     response_ok = False
    #     framer = ModbusSocketFramer(ClientDecoder())
    #     framer.processIncomingPacket(message, _handle_response, slave=0)
    #     assert response_ok, "Response is valid, but not accepted"
    #
    #     message = bytearray(b"\x00\x01\x00\x00\x00\x0b\x01\x03\x08\x00\xb5\x12\x2f\x37\x21\x00\x03")
    #     response_ok = False
    #     framer = ModbusSocketFramer(ClientDecoder())
    #     framer.processIncomingPacket(message, _handle_response, slave=0)
    #     assert response_ok, "Response is valid, but not accepted"

    # (ModbusSocketFramer, b'\x00\x00\x00\x00\x00\x06\x00\x01\x00\x01\x00\n',),
    # request = ReadCoilsRequest(1, 10)
    # assert test_framer.buildPacket(request) == message

    # (ModbusSocketFramer, b'\x00\x00\x00\x00\x00\x06\x01\x01\x00\x01\x00\n',),
    # @pytest.mark.parametrize(("slave"), [0x01, 0x02])
    # def test_processincomingpacket_ok(framer, message, slave):

    # (ModbusSocketFramer, b'\x00\x00\x00\x00\x00\x06\x01\x27\x00\x01\x00\n',),
    # def test_processincomingpacket_not_ok(framer, message):

    # (ModbusSocketFramer, b'\x00\x00\x00\x00\x00\x06\x61\x62\x00\x01\x00\n',),
    # def test_decode_data(framer, message, expected):
