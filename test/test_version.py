"""Test version."""
from pymodbus import __version__ as pymodbus_version
from pymodbus import __version_full__ as pymodbus_version_full
from pymodbus.version import Version, version


class TestVersion:  # pylint: disable=too-few-public-methods
    """Unittest for the pymodbus._version code."""

    def test_version_class(self):
        """Test version class."""
        test_version = Version("test", 1, 2, 3, "sometag")
        assert test_version.short() == "1.2.3.sometag"
        assert str(test_version) == "[test, version 1.2.3.sometag]"
        assert test_version.package == "test"

        assert pymodbus_version == version.short()
        assert pymodbus_version_full == str(version)
        assert version.package == "pymodbus"
