"""Test events."""
import unittest

from pymodbus.events import (
    CommunicationRestartEvent,
    EnteredListenModeEvent,
    ModbusEvent,
    RemoteReceiveEvent,
    RemoteSendEvent,
)
from pymodbus.exceptions import NotImplementedException, ParameterException


class ModbusEventsTest(unittest.TestCase):
    """Unittest for the pymodbus.device module."""

    def setUp(self):
        """Set up the test environment"""

    def tearDown(self):
        """Clean up the test environment"""

    def test_modbus_event_base_class(self):
        """Test modbus event base class."""
        event = ModbusEvent()
        self.assertRaises(NotImplementedException, event.encode)
        self.assertRaises(NotImplementedException, lambda: event.decode(None))

    def test_remote_receive_event(self):
        """Test remove receive event."""
        event = RemoteReceiveEvent()
        event.decode(b"\x70")
        self.assertTrue(event.overrun)
        self.assertTrue(event.listen)
        self.assertTrue(event.broadcast)

    def test_remote_sent_event(self):
        """Test remote sent event."""
        event = RemoteSendEvent()
        result = event.encode()
        self.assertEqual(result, b"\x40")
        event.decode(b"\x7f")
        self.assertTrue(event.read)
        self.assertTrue(event.slave_abort)
        self.assertTrue(event.slave_busy)
        self.assertTrue(event.slave_nak)
        self.assertTrue(event.write_timeout)
        self.assertTrue(event.listen)

    def test_remote_sent_event_encode(self):
        """Test remote sent event encode."""
        arguments = {
            "read": True,
            "slave_abort": True,
            "slave_busy": True,
            "slave_nak": True,
            "write_timeout": True,
            "listen": True,
        }
        event = RemoteSendEvent(**arguments)
        result = event.encode()
        self.assertEqual(result, b"\x7f")

    def test_entered_listen_mode_event(self):
        """Test entered listen mode event."""
        event = EnteredListenModeEvent()
        result = event.encode()
        self.assertEqual(result, b"\x04")
        event.decode(b"\x04")
        self.assertEqual(event.value, 0x04)
        self.assertRaises(ParameterException, lambda: event.decode(b"\x00"))

    def test_communication_restart_event(self):
        """Test communication restart event."""
        event = CommunicationRestartEvent()
        result = event.encode()
        self.assertEqual(result, b"\x00")
        event.decode(b"\x00")
        self.assertEqual(event.value, 0x00)
        self.assertRaises(ParameterException, lambda: event.decode(b"\x04"))
