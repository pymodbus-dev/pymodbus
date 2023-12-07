"""Test device."""
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


class TestDataStore:
    """Unittest for the pymodbus.device module."""

    # -----------------------------------------------------------------------#
    #  Setup/TearDown
    # -----------------------------------------------------------------------#

    info = None
    ident = None
    control = None

    def setup_method(self):
        """Do setup."""
        self.info = {
            0x00: "Bashwork",  # VendorName
            0x01: "PTM",  # ProductCode
            0x02: "1.0",  # MajorMinorRevision
            0x03: "http://internets.com",  # VendorUrl
            0x04: "pymodbus",  # ProductName
            0x05: "bashwork",  # ModelName
            0x06: "pytest",  # UserApplicationName
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

    def test_update_identity(self):
        """Test device identification reading."""
        self.control.Identity.update(self.ident)
        assert self.control.Identity.VendorName == "Bashwork"
        assert self.control.Identity.ProductCode == "PTM"
        assert self.control.Identity.MajorMinorRevision == "1.0"
        assert self.control.Identity.VendorUrl == "http://internets.com"
        assert self.control.Identity.ProductName == "pymodbus"
        assert self.control.Identity.ModelName == "bashwork"
        assert self.control.Identity.UserApplicationName == "pytest"

    def test_device_identification_factory(self):
        """Test device identification reading."""
        self.control.Identity.update(self.ident)
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.SPECIFIC, 0x00
        )
        assert result[0x00] == "Bashwork"

        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.BASIC, 0x00
        )
        assert result[0x00] == "Bashwork"
        assert result[0x01] == "PTM"
        assert result[0x02] == "1.0"

        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.REGULAR, 0x00
        )
        assert result[0x00] == "Bashwork"
        assert result[0x01] == "PTM"
        assert result[0x02] == "1.0"
        assert result[0x03] == "http://internets.com"
        assert result[0x04] == "pymodbus"
        assert result[0x05] == "bashwork"
        assert result[0x06] == "pytest"

    def test_device_identification_factory_lookup(self):
        """Test device identification factory lookup."""
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.BASIC, 0x00
        )
        assert sorted(result.keys()) == [0x00, 0x01, 0x02]
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.BASIC, 0x02
        )
        assert sorted(result.keys()) == [0x02]
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.REGULAR, 0x00
        )
        assert sorted(result.keys()) == [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06]
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.REGULAR, 0x01
        )
        assert sorted(result.keys()) == [0x01, 0x02, 0x03, 0x04, 0x05, 0x06]
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.REGULAR, 0x05
        )
        assert sorted(result.keys()) == [0x05, 0x06]
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.EXTENDED, 0x00
        )
        assert sorted(result.keys()) == [
            0x00,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x80,
            0x82,
            0xFF,
        ]
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.EXTENDED, 0x02
        )
        assert sorted(result.keys()) == [0x02, 0x03, 0x04, 0x05, 0x06, 0x80, 0x82, 0xFF]
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.EXTENDED, 0x06
        )
        assert sorted(result.keys()) == [0x06, 0x80, 0x82, 0xFF]
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.EXTENDED, 0x80
        )
        assert sorted(result.keys()) == [0x80, 0x82, 0xFF]
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.EXTENDED, 0x82
        )
        assert sorted(result.keys()) == [0x82, 0xFF]
        result = DeviceInformationFactory.get(
            self.control, DeviceInformation.EXTENDED, 0x81
        )
        assert sorted(result.keys()) == [
            0x00,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x80,
            0x82,
            0xFF,
        ]

    def test_basic_commands(self):
        """Test device identification reading."""
        assert str(self.ident) == "DeviceIdentity"
        assert str(self.control) == "ModbusControl"

    def test_modbus_device_identification_get(self):
        """Test device identification reading."""
        assert self.ident[0x00] == "Bashwork"
        assert self.ident[0x01] == "PTM"
        assert self.ident[0x02] == "1.0"
        assert self.ident[0x03] == "http://internets.com"
        assert self.ident[0x04] == "pymodbus"
        assert self.ident[0x05] == "bashwork"
        assert self.ident[0x06] == "pytest"
        assert self.ident[0x07] != "x"
        assert self.ident[0x08] != "x"
        assert self.ident[0x10] != "reserved"
        assert not self.ident[0x54]

    def test_modbus_device_identification_summary(self):
        """Test device identification summary creation."""
        summary = sorted(self.ident.summary().values())
        expected = sorted(list(self.info.values())[:0x07])  # remove private
        assert summary == expected

    def test_modbus_device_identification_set(self):
        """Test a device identification writing."""
        self.ident[0x07] = "y"
        self.ident[0x08] = "y"
        self.ident[0x10] = "public"
        self.ident[0x54] = "testing"

        assert self.ident[0x07] != "y"
        assert self.ident[0x08] != "y"
        assert self.ident[0x10] == "public"
        assert self.ident[0x54] == "testing"

    def test_modbus_control_block_ascii_modes(self):
        """Test a server control block ascii mode."""
        assert id(self.control) == id(ModbusControlBlock())
        self.control.Mode = "RTU"
        assert self.control.Mode == "RTU"
        self.control.Mode = "FAKE"
        assert self.control.Mode != "FAKE"

    def test_modbus_control_block_counters(self):
        """Tests the MCB counters methods."""
        assert not self.control.Counter.BusMessage
        for _ in range(10):
            self.control.Counter.BusMessage += 1
            self.control.Counter.SlaveMessage += 1
        assert self.control.Counter.BusMessage == 10
        self.control.Counter.BusMessage = 0x00
        assert not self.control.Counter.BusMessage
        assert self.control.Counter.SlaveMessage == 10
        self.control.Counter.reset()
        assert not self.control.Counter.SlaveMessage

    def test_modbus_control_block_update(self):
        """Tests the MCB counters update methods."""
        values = {"SlaveMessage": 5, "BusMessage": 5}
        self.control.Counter.BusMessage += 1
        self.control.Counter.SlaveMessage += 1
        self.control.Counter.update(values)
        assert self.control.Counter.SlaveMessage == 6
        assert self.control.Counter.BusMessage == 6

    def test_modbus_control_block_iterator(self):
        """Tests the MCB counters iterator."""
        self.control.Counter.reset()
        for _, count in self.control:
            assert not count

    def test_modbus_counters_handler_iterator(self):
        """Tests the MCB counters iterator."""
        self.control.Counter.reset()
        for _, count in self.control.Counter:
            assert not count

    def test_modbus_control_block_counter_summary(self):
        """Tests retrieving the current counter summary."""
        assert not self.control.Counter.summary()
        for _ in range(10):
            self.control.Counter.BusMessage += 1
            self.control.Counter.SlaveMessage += 1
            self.control.Counter.SlaveNAK += 1
            self.control.Counter.BusCharacterOverrun += 1
        assert self.control.Counter.summary() == 0xA9
        self.control.Counter.reset()
        assert not self.control.Counter.summary()

    def test_modbus_control_block_listen(self):
        """Test the MCB listen flag methods."""
        self.control.ListenOnly = False
        assert not self.control.ListenOnly
        self.control.ListenOnly = not self.control.ListenOnly
        assert self.control.ListenOnly

    def test_modbus_control_block_delimiter(self):
        """Tests the MCB delimiter setting methods."""
        self.control.Delimiter = b"\r"
        assert self.control.Delimiter == b"\r"
        self.control.Delimiter = "="
        assert self.control.Delimiter == b"="
        self.control.Delimiter = 61
        assert self.control.Delimiter == b"="

    def test_modbus_control_block_diagnostic(self):
        """Tests the MCB delimiter setting methods."""
        assert self.control.getDiagnosticRegister() == [False] * 16
        for i in (1, 3, 4, 6):
            self.control.setDiagnostic({i: True})
        assert self.control.getDiagnostic(1)
        assert not self.control.getDiagnostic(2)
        actual = [False, True, False, True, True, False, True] + [False] * 9
        assert actual == self.control.getDiagnosticRegister()
        for i in range(16):
            self.control.setDiagnostic({i: False})

    def test_modbus_control_block_invalid_diagnostic(self):
        """Tests querying invalid MCB counters methods."""
        assert not self.control.getDiagnostic(-1)
        assert not self.control.getDiagnostic(17)
        assert not self.control.getDiagnostic(None)
        assert not self.control.getDiagnostic([1, 2, 3])

    def test_clearing_control_events(self):
        """Test adding and clearing modbus events."""
        assert self.control.Events == []
        event = ModbusEvent()
        self.control.addEvent(event)
        assert self.control.Events == [event]
        assert self.control.Counter.Event == 1
        self.control.clearEvents()
        assert self.control.Events == []
        assert self.control.Counter.Event == 1

    def test_retrieving_control_events(self):
        """Test adding and removing a host."""
        assert self.control.Events == []
        event = RemoteReceiveEvent()
        self.control.addEvent(event)
        assert self.control.Events == [event]
        packet = self.control.getEvents()
        assert packet == b"\x40"

    def test_modbus_plus_statistics(self):
        """Test device identification reading."""
        default = [0x0000] * 55
        statistics = ModbusPlusStatistics()
        assert default == statistics.encode()
        statistics.reset()
        assert default == statistics.encode()
        assert default == self.control.Plus.encode()

    def test_modbus_plus_statistics_helpers(self):
        """Test modbus plus statistics helper methods."""
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
        assert sorted(summary) == sorted(stats_summary)
        assert not sum(sum(value[1]) for value in statistics)
