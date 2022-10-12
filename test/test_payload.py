"""Payload Utilities Test Fixture.

This fixture tests the functionality of the payload
utilities.

* PayloadBuilder
* PayloadDecoder
"""
import unittest

from pymodbus.constants import Endian
from pymodbus.exceptions import ParameterException
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder


# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class ModbusPayloadUtilityTests(unittest.TestCase):
    """Modbus payload utility tests."""

    # ----------------------------------------------------------------------- #
    # Setup/TearDown
    # ----------------------------------------------------------------------- #

    def setUp(self):
        """Initialize the test environment and builds request/result encoding pairs."""
        self.little_endian_payload = (
            b"\x01\x02\x00\x03\x00\x00\x00\x04\x00\x00\x00\x00"
            b"\x00\x00\x00\xff\xfe\xff\xfd\xff\xff\xff\xfc\xff"
            b"\xff\xff\xff\xff\xff\xff\x00\x00\xa0\x3f\x00\x00"
            b"\x00\x00\x00\x00\x19\x40\x01\x00\x74\x65\x73\x74"
            b"\x11"
        )

        self.big_endian_payload = (
            b"\x01\x00\x02\x00\x00\x00\x03\x00\x00\x00\x00\x00"
            b"\x00\x00\x04\xff\xff\xfe\xff\xff\xff\xfd\xff\xff"
            b"\xff\xff\xff\xff\xff\xfc\x3f\xa0\x00\x00\x40\x19"
            b"\x00\x00\x00\x00\x00\x00\x00\x01\x74\x65\x73\x74"
            b"\x11"
        )

        self.bitstring = [True, False, False, False, True, False, False, False]

    def tearDown(self):
        """Clean up the test environment"""

    # ----------------------------------------------------------------------- #
    # Payload Builder Tests
    # ----------------------------------------------------------------------- #

    def test_little_endian_payload_builder(self):
        """Test basic bit message encoding/decoding"""
        builder = BinaryPayloadBuilder(byteorder=Endian.Little, wordorder=Endian.Little)
        builder.add_8bit_uint(1)
        builder.add_16bit_uint(2)
        builder.add_32bit_uint(3)
        builder.add_64bit_uint(4)
        builder.add_8bit_int(-1)
        builder.add_16bit_int(-2)
        builder.add_32bit_int(-3)
        builder.add_64bit_int(-4)
        builder.add_32bit_float(1.25)
        builder.add_64bit_float(6.25)
        builder.add_16bit_uint(1)  # placeholder
        builder.add_string(b"test")
        builder.add_bits(self.bitstring)
        self.assertEqual(self.little_endian_payload, builder.to_string())

    def test_big_endian_payload_builder(self):
        """Test basic bit message encoding/decoding"""
        builder = BinaryPayloadBuilder(byteorder=Endian.Big)
        builder.add_8bit_uint(1)
        builder.add_16bit_uint(2)
        builder.add_32bit_uint(3)
        builder.add_64bit_uint(4)
        builder.add_8bit_int(-1)
        builder.add_16bit_int(-2)
        builder.add_32bit_int(-3)
        builder.add_64bit_int(-4)
        builder.add_32bit_float(1.25)
        builder.add_64bit_float(6.25)
        builder.add_16bit_uint(1)  # placeholder
        builder.add_string("test")
        builder.add_bits(self.bitstring)
        self.assertEqual(self.big_endian_payload, builder.to_string())

    def test_payload_builder_reset(self):
        """Test basic bit message encoding/decoding"""
        builder = BinaryPayloadBuilder()
        builder.add_8bit_uint(0x12)
        builder.add_8bit_uint(0x34)
        builder.add_8bit_uint(0x56)
        builder.add_8bit_uint(0x78)
        self.assertEqual(b"\x12\x34\x56\x78", builder.to_string())
        self.assertEqual([b"\x12\x34", b"\x56\x78"], builder.build())
        builder.reset()
        self.assertEqual(b"", builder.to_string())
        self.assertEqual([], builder.build())

    def test_payload_builder_with_raw_payload(self):
        """Test basic bit message encoding/decoding"""
        _coils1 = [
            False,
            False,
            True,
            True,
            False,
            True,
            False,
            False,
            False,
            False,
            False,
            True,
            False,
            False,
            True,
            False,
            False,
            True,
            True,
            True,
            True,
            False,
            False,
            False,
            False,
            True,
            False,
            True,
            False,
            True,
            True,
            False,
        ]
        _coils2 = [
            False,
            False,
            False,
            True,
            False,
            False,
            True,
            False,
            False,
            False,
            True,
            True,
            False,
            True,
            False,
            False,
            False,
            True,
            False,
            True,
            False,
            True,
            True,
            False,
            False,
            True,
            True,
            True,
            True,
            False,
            False,
            False,
        ]

        builder = BinaryPayloadBuilder(
            [b"\x12", b"\x34", b"\x56", b"\x78"], repack=True
        )
        self.assertEqual(b"\x12\x34\x56\x78", builder.to_string())
        self.assertEqual([13330, 30806], builder.to_registers())
        coils = builder.to_coils()
        self.assertEqual(_coils1, coils)

        builder = BinaryPayloadBuilder(
            [b"\x12", b"\x34", b"\x56", b"\x78"], byteorder=Endian.Big
        )
        self.assertEqual(b"\x12\x34\x56\x78", builder.to_string())
        self.assertEqual([4660, 22136], builder.to_registers())
        self.assertEqual("\x12\x34\x56\x78", str(builder))
        coils = builder.to_coils()
        self.assertEqual(_coils2, coils)

    # ----------------------------------------------------------------------- #
    # Payload Decoder Tests
    # ----------------------------------------------------------------------- #

    def test_little_endian_payload_decoder(self):
        """Test basic bit message encoding/decoding"""
        decoder = BinaryPayloadDecoder(
            self.little_endian_payload, byteorder=Endian.Little, wordorder=Endian.Little
        )
        self.assertEqual(1, decoder.decode_8bit_uint())
        self.assertEqual(2, decoder.decode_16bit_uint())
        self.assertEqual(3, decoder.decode_32bit_uint())
        self.assertEqual(4, decoder.decode_64bit_uint())
        self.assertEqual(-1, decoder.decode_8bit_int())
        self.assertEqual(-2, decoder.decode_16bit_int())
        self.assertEqual(-3, decoder.decode_32bit_int())
        self.assertEqual(-4, decoder.decode_64bit_int())
        self.assertEqual(1.25, decoder.decode_32bit_float())
        self.assertEqual(6.25, decoder.decode_64bit_float())
        self.assertEqual(None, decoder.skip_bytes(2))
        self.assertEqual("test", decoder.decode_string(4).decode())
        self.assertEqual(self.bitstring, decoder.decode_bits())

    def test_big_endian_payload_decoder(self):
        """Test basic bit message encoding/decoding"""
        decoder = BinaryPayloadDecoder(self.big_endian_payload, byteorder=Endian.Big)
        self.assertEqual(1, decoder.decode_8bit_uint())
        self.assertEqual(2, decoder.decode_16bit_uint())
        self.assertEqual(3, decoder.decode_32bit_uint())
        self.assertEqual(4, decoder.decode_64bit_uint())
        self.assertEqual(-1, decoder.decode_8bit_int())
        self.assertEqual(-2, decoder.decode_16bit_int())
        self.assertEqual(-3, decoder.decode_32bit_int())
        self.assertEqual(-4, decoder.decode_64bit_int())
        self.assertEqual(1.25, decoder.decode_32bit_float())
        self.assertEqual(6.25, decoder.decode_64bit_float())
        self.assertEqual(None, decoder.skip_bytes(2))
        self.assertEqual(b"test", decoder.decode_string(4))
        self.assertEqual(self.bitstring, decoder.decode_bits())

    def test_payload_decoder_reset(self):
        """Test the payload decoder reset functionality"""
        decoder = BinaryPayloadDecoder(b"\x12\x34")
        self.assertEqual(0x12, decoder.decode_8bit_uint())
        self.assertEqual(0x34, decoder.decode_8bit_uint())
        decoder.reset()
        self.assertEqual(0x3412, decoder.decode_16bit_uint())

    def test_payload_decoder_register_factory(self):
        """Test the payload decoder reset functionality"""
        payload = [1, 2, 3, 4]
        decoder = BinaryPayloadDecoder.fromRegisters(payload, byteorder=Endian.Little)
        encoded = b"\x00\x01\x00\x02\x00\x03\x00\x04"
        self.assertEqual(encoded, decoder.decode_string(8))

        decoder = BinaryPayloadDecoder.fromRegisters(payload, byteorder=Endian.Big)
        encoded = b"\x00\x01\x00\x02\x00\x03\x00\x04"
        self.assertEqual(encoded, decoder.decode_string(8))

        self.assertRaises(
            ParameterException, lambda: BinaryPayloadDecoder.fromRegisters("abcd")
        )

    def test_payload_decoder_coil_factory(self):
        """Test the payload decoder reset functionality"""
        payload = [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1]
        decoder = BinaryPayloadDecoder.fromCoils(payload, byteorder=Endian.Little)
        encoded = b"\x88\x11"
        self.assertEqual(encoded, decoder.decode_string(2))

        decoder = BinaryPayloadDecoder.fromCoils(payload, byteorder=Endian.Big)
        encoded = b"\x88\x11"
        self.assertEqual(encoded, decoder.decode_string(2))

        self.assertRaises(
            ParameterException, lambda: BinaryPayloadDecoder.fromCoils("abcd")
        )
