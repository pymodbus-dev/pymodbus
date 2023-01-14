"""Test interfaces."""
import unittest

from pymodbus.exceptions import NotImplementedException
from pymodbus.interfaces import (
    IModbusDecoder,
    IModbusFramer,
    IModbusSlaveContext,
    IPayloadBuilder,
    Singleton,
)


class _SingleInstance(Singleton):  # pylint: disable=too-few-public-methods
    """Single instance."""


class ModbusInterfaceTestsTest(unittest.TestCase):
    """Unittest for the pymodbus.interfaces module."""

    def setUp(self):
        """Initialize the test environment"""

    def tearDown(self):
        """Clean up the test environment"""

    def test_singleton_interface(self):
        """Test that the singleton interface works"""
        first = _SingleInstance()
        second = _SingleInstance()
        self.assertEqual(first, second)

    def test_imodbusdecoder(self):
        """Test that the base class isn't implemented"""
        x_base = None
        instance = IModbusDecoder()
        self.assertRaises(NotImplementedException, lambda: instance.decode(x_base))
        self.assertRaises(
            NotImplementedException, lambda: instance.lookupPduClass(x_base)
        )
        self.assertRaises(NotImplementedException, lambda: instance.register(x_base))

    def test_modbus_framer_interface(self):
        """Test that the base class isn't implemented"""
        x_base = None
        instance = IModbusFramer()
        self.assertRaises(NotImplementedException, instance.checkFrame)
        self.assertRaises(NotImplementedException, instance.advanceFrame)
        self.assertRaises(NotImplementedException, instance.isFrameReady)
        self.assertRaises(NotImplementedException, instance.getFrame)
        self.assertRaises(NotImplementedException, lambda: instance.addToFrame(x_base))
        self.assertRaises(
            NotImplementedException, lambda: instance.populateResult(x_base)
        )
        self.assertRaises(
            NotImplementedException,
            lambda: instance.processIncomingPacket(x_base, x_base),
        )
        self.assertRaises(NotImplementedException, lambda: instance.buildPacket(x_base))

    def test_modbus_slave_context_interface(self):
        """Test that the base class isn't implemented"""
        x_base = None
        instance = IModbusSlaveContext()
        self.assertRaises(NotImplementedException, instance.reset)
        self.assertRaises(
            NotImplementedException, lambda: instance.validate(x_base, x_base, x_base)
        )
        self.assertRaises(
            NotImplementedException, lambda: instance.getValues(x_base, x_base, x_base)
        )
        self.assertRaises(
            NotImplementedException, lambda: instance.setValues(x_base, x_base, x_base)
        )

    def test_modbus_payload_builder_interface(self):
        """Test that the base class isn't implemented"""
        instance = IPayloadBuilder()
        self.assertRaises(
            NotImplementedException,
            lambda: instance.build(),  # pylint: disable=unnecessary-lambda
        )
