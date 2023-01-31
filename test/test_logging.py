"""Test datastore."""
import pytest

from pymodbus import pymodbus_apply_logging_config
from pymodbus.logging import Log


class TestLogging:
    """Tests of pymodbus logging."""

    def test_log_our_default(self):
        """Test default logging"""
        pymodbus_apply_logging_config()
        assert Log.LOG_LEVEL == Log.WARNING

    def test_log_set_level(self):
        """Test default logging"""
        pymodbus_apply_logging_config(Log.DEBUG)
        assert Log.LOG_LEVEL == Log.DEBUG
        pymodbus_apply_logging_config(Log.INFO)
        assert Log.LOG_LEVEL == Log.INFO

    def test_log_simple(self):
        """Test simple string"""
        txt = "simple string"
        log_txt = Log.build_msg(txt)
        assert log_txt == txt

    @pytest.mark.parametrize(
        "txt, result, params",
        [
            ("string {} {} {}", "string 101 102 103", (101, 102, 103)),
            ("string {}", "string 0x41 0x42 0x43 0x44", (b"ABCD", ":hex")),
            ("string {}", "string 125", (125, ":str")),
        ],
    )
    def test_log_parms(self, txt, result, params):
        """Test string with parameters (old f-string)"""
        log_txt = Log.build_msg(txt, *params)
        assert log_txt == result
