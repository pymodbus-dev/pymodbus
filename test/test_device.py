"""Test device."""
import unittest

from pymodbus.constants import DeviceInformation
from pymodbus.device import (
    DeviceInformationFactory,
    ModbusControlBlock,
    ModbusDeviceIdentification,
    ModbusPlusStatistics,
)
from pymodbus.events import ModbusEvent, RemoteReceiveEvent


# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class SimpleDataStoreTest(unittest.TestCase):
    """Unittest for the pymodbus.device module."""

    # -----------------------------------------------------------------------#
    #  Setup/TearDown
    # -----------------------------------------------------------------------#

    def setUp(self):
        """Do setup."""
        self.info = {
            0x00: "Bashwork",  # VendorName
            0x01: "PTM",  # ProductCode
            0x02: "1.0",  # MajorMinorRevision
            0x03: "http://internets.com",  # VendorUrl
            0x04: "pymodbus",  # ProductName
            0x05: "bashwork",  # ModelName
            0x06: "unittest",  # UserApplicationName
            0x07: "x",  # reserved
            0x08: "x",  # reserved
            0x10: "reserved",  # reserved
            0x80: "custom1",  # device specific start
            0x82: "custom2",  # device specific
            0xFF: "customlast",  # device specific last
        }
        self.ident = ModbusDeviceIdentification(self.info)
        self.control = ModbusControlBlock()
        self.control.reset()

    def tearDown(self):
        """Clean up the test environment"""
        del self.ident
        del self.control

    def test_update_identity(self):
        """Test device identification reading"""
        self.control.Identity.update(self.ident)
        self.assertEqual(self.control.Identity.VendorName, "Bashwork")
        self.assertEqual(self.control.Identity.ProductCode, "PTM")
        self.assertEqual(self.control.Identity.MajorMinorRevision, "1.0")
        self.assertEqual(self.control.Identity.VendorUrl, "http://internets.com")
        self.assertEqual(self.control.Identity.ProductName, "pymodbus")
        self.assertEqual(self.control.Identity.ModelName, "bashwork")
        self.assertEqual(self.control.Identity.UserApplicationName, "unittest")

    def test_device_identification_factory(self):
        """Test device identification reading"""
        self.control.Identity.update(self.ident)
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Specific, 0x00
        )
        self.assertEqual(result[0x00], "Bashwork")

        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Basic, 0x00
        )
        self.assertEqual(result[0x00], "Bashwork")
        self.assertEqual(result[0x01], "PTM")
        self.assertEqual(result[0x02], "1.0")

        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Regular, 0x00
        )
        self.assertEqual(result[0x00], "Bashwork")
        self.assertEqual(result[0x01], "PTM")
        self.assertEqual(result[0x02], "1.0")
        self.assertEqual(result[0x03], "http://internets.com")
        self.assertEqual(result[0x04], "pymodbus")
        self.assertEqual(result[0x05], "bashwork")
        self.assertEqual(result[0x06], "unittest")

    def test_device_identification_factory_lookup(self):
        """Test device identification factory lookup."""
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Basic, 0x00
        )
        self.assertEqual(sorted(result.keys()), [0x00, 0x01, 0x02])
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Basic, 0x02
        )
        self.assertEqual(sorted(result.keys()), [0x02])
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Regular, 0x00
        )
        self.assertEqual(
            sorted(result.keys()), [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06]
        )
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Regular, 0x01
        )
        self.assertEqual(sorted(result.keys()), [0x01, 0x02, 0x03, 0x04, 0x05, 0x06])
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Regular, 0x05
        )
        self.assertEqual(sorted(result.keys()), [0x05, 0x06])
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Extended, 0x00
        )
        self.assertEqual(
            sorted(result.keys()),
            [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x80, 0x82, 0xFF],
        )
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Extended, 0x02
        )
        self.assertEqual(
            sorted(result.keys()), [0x02, 0x03, 0x04, 0x05, 0x06, 0x80, 0x82, 0xFF]
        )
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Extended, 0x06
        )
        self.assertEqual(sorted(result.keys()), [0x06, 0x80, 0x82, 0xFF])
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Extended, 0x80
        )
        self.assertEqual(sorted(result.keys()), [0x80, 0x82, 0xFF])
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Extended, 0x82
        )
        self.assertEqual(sorted(result.keys()), [0x82, 0xFF])
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.Extended, 0x81
        )
        self.assertEqual(
            sorted(result.keys()),
            [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x80, 0x82, 0xFF],
        )

    def test_basic_commands(self):
        """Test device identification reading"""
        self.assertEqual(str(self.ident), "DeviceIdentity")
        self.assertEqual(str(self.control), "ModbusControl")

    def test_modbus_device_identification_get(self):
        """Test device identification reading"""
        self.assertEqual(self.ident[0x00], "Bashwork")
        self.assertEqual(self.ident[0x01], "PTM")
        self.assertEqual(self.ident[0x02], "1.0")
        self.assertEqual(self.ident[0x03], "http://internets.com")
        self.assertEqual(self.ident[0x04], "pymodbus")
        self.assertEqual(self.ident[0x05], "bashwork")
        self.assertEqual(self.ident[0x06], "unittest")
        self.assertNotEqual(self.ident[0x07], "x")
        self.assertNotEqual(self.ident[0x08], "x")
        self.assertNotEqual(self.ident[0x10], "reserved")
        self.assertEqual(self.ident[0x54], "")

    def test_modbus_device_identification_summary(self):
        """Test device identification summary creation"""
        summary = sorted(self.ident.summary().values())
        expected = sorted(list(self.info.values())[:0x07])  # remove private
        self.assertEqual(summary, expected)

    def test_modbus_device_identification_set(self):
        """Test a device identification writing"""
        self.ident[0x07] = "y"
        self.ident[0x08] = "y"
        self.ident[0x10] = "public"
        self.ident[0x54] = "testing"

        self.assertNotEqual("y", self.ident[0x07])
        self.assertNotEqual("y", self.ident[0x08])
        self.assertEqual("public", self.ident[0x10])
        self.assertEqual("testing", self.ident[0x54])

    def test_modbus_control_block_ascii_modes(self):
        """Test a server control block ascii mode"""
        self.assertEqual(id(self.control), id(ModbusControlBlock()))
        self.control.Mode = "RTU"
        self.assertEqual("RTU", self.control.Mode)
        self.control.Mode = "FAKE"
        self.assertNotEqual("FAKE", self.control.Mode)

    def test_modbus_control_block_counters(self):
        """Tests the MCB counters methods"""
        self.assertEqual(0x0, self.control.Counter.BusMessage)
        for _ in range(10):
            self.control.Counter.BusMessage += 1
            self.control.Counter.SlaveMessage += 1
        self.assertEqual(10, self.control.Counter.BusMessage)
        self.control.Counter.BusMessage = 0x00
        self.assertEqual(0, self.control.Counter.BusMessage)
        self.assertEqual(10, self.control.Counter.SlaveMessage)
        self.control.Counter.reset()
        self.assertEqual(0, self.control.Counter.SlaveMessage)

    def test_modbus_control_block_update(self):
        """Tests the MCB counters update methods"""
        values = {"SlaveMessage": 5, "BusMessage": 5}
        self.control.Counter.BusMessage += 1
        self.control.Counter.SlaveMessage += 1
        self.control.Counter.update(values)
        self.assertEqual(6, self.control.Counter.SlaveMessage)
        self.assertEqual(6, self.control.Counter.BusMessage)

    def test_modbus_control_block_iterator(self):
        """Tests the MCB counters iterator"""
        self.control.Counter.reset()
        for _, count in self.control:
            self.assertEqual(0, count)

    def test_modbus_counters_handler_iterator(self):
        """Tests the MCB counters iterator"""
        self.control.Counter.reset()
        for _, count in self.control.Counter:
            self.assertEqual(0, count)

    def test_modbus_control_block_counter_summary(self):
        """Tests retrieving the current counter summary"""
        self.assertEqual(0x00, self.control.Counter.summary())
        for _ in range(10):
            self.control.Counter.BusMessage += 1
            self.control.Counter.SlaveMessage += 1
            self.control.Counter.SlaveNAK += 1
            self.control.Counter.BusCharacterOverrun += 1
        self.assertEqual(0xA9, self.control.Counter.summary())
        self.control.Counter.reset()
        self.assertEqual(0x00, self.control.Counter.summary())

    def test_modbus_control_block_listen(self):
        """Test the MCB listen flag methods"""
        self.control.ListenOnly = False
        self.assertEqual(self.control.ListenOnly, False)
        self.control.ListenOnly = not self.control.ListenOnly
        self.assertEqual(self.control.ListenOnly, True)

    def test_modbus_control_block_delimiter(self):
        """Tests the MCB delimiter setting methods"""
        self.control.Delimiter = b"\r"
        self.assertEqual(self.control.Delimiter, b"\r")
        self.control.Delimiter = "="
        self.assertEqual(self.control.Delimiter, b"=")
        self.control.Delimiter = 61
        self.assertEqual(self.control.Delimiter, b"=")

    def test_modbus_control_block_diagnostic(self):
        """Tests the MCB delimiter setting methods"""
        self.assertEqual([False] * 16, self.control.getDiagnosticRegister())
        for i in (1, 3, 4, 6):
            self.control.setDiagnostic({i: True})
        self.assertEqual(True, self.control.getDiagnostic(1))
        self.assertEqual(False, self.control.getDiagnostic(2))
        actual = [False, True, False, True, True, False, True] + [False] * 9
        self.assertEqual(actual, self.control.getDiagnosticRegister())
        for i in range(16):
            self.control.setDiagnostic({i: False})

    def test_modbus_control_block_invalid_diagnostic(self):
        """Tests querying invalid MCB counters methods"""
        self.assertEqual(None, self.control.getDiagnostic(-1))
        self.assertEqual(None, self.control.getDiagnostic(17))
        self.assertEqual(None, self.control.getDiagnostic(None))
        self.assertEqual(None, self.control.getDiagnostic([1, 2, 3]))

    def test_clearing_control_events(self):
        """Test adding and clearing modbus events"""
        self.assertEqual(self.control.Events, [])
        event = ModbusEvent()
        self.control.addEvent(event)
        self.assertEqual(self.control.Events, [event])
        self.assertEqual(self.control.Counter.Event, 1)
        self.control.clearEvents()
        self.assertEqual(self.control.Events, [])
        self.assertEqual(self.control.Counter.Event, 1)

    def test_retrieving_control_events(self):
        """Test adding and removing a host"""
        self.assertEqual(self.control.Events, [])
        event = RemoteReceiveEvent()
        self.control.addEvent(event)
        self.assertEqual(self.control.Events, [event])
        packet = self.control.getEvents()
        self.assertEqual(packet, b"\x40")

    def test_modbus_plus_statistics(self):
        """Test device identification reading"""
        default = [0x0000] * 55
        statistics = ModbusPlusStatistics()
        self.assertEqual(default, statistics.encode())
        statistics.reset()
        self.assertEqual(default, statistics.encode())
        self.assertEqual(default, self.control.Plus.encode())

    def test_modbus_plus_statistics_helpers(self):
        """Test modbus plus statistics helper methods"""
        statistics = ModbusPlusStatistics()
        summary = [
            [0],
            [0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0],
            [0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0],
            [0],
            [0],
            [0],
            [0, 0],
            [0],
            [0],
            [0],
            [0],
            [0],
            [0],
            [0],
            [0, 0],
            [0],
            [0],
            [0],
            [0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0],
            [0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0],
            [0],
            [0, 0],
            [0],
            [0],
            [0],
            [0],
            [0, 0],
            [0],
            [0],
            [0],
            [0],
            [0],
            [0, 0],
            [0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        stats_summary = list(statistics.summary())
        self.assertEqual(sorted(summary), sorted(stats_summary))
        self.assertEqual(0x00, sum(sum(value[1]) for value in statistics))
