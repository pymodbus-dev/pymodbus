"""Test datastore."""
import logging

import pytest

from pymodbus import pymodbus_apply_logging_config
from pymodbus.logging import Log


class TestLogging:
    """Tests of pymodbus logging."""

    def test_log_our_default(self):
        """Test default logging"""
        logging.getLogger().setLevel(logging.WARNING)
        Log.setLevel(logging.NOTSET)
        Log.info("test")
        assert Log.LOG_LEVEL == logging.WARNING
        Log.setLevel(logging.NOTSET)
        logging.getLogger().setLevel(logging.INFO)
        Log.info("test")
        assert Log.LOG_LEVEL == logging.INFO
        Log.setLevel(logging.NOTSET)
        pymodbus_apply_logging_config()
        assert Log.LOG_LEVEL == logging.DEBUG

    def test_log_set_level(self):
        """Test default logging"""
        pymodbus_apply_logging_config(logging.DEBUG)
        assert Log.LOG_LEVEL == logging.DEBUG
        pymodbus_apply_logging_config(logging.INFO)
        assert Log.LOG_LEVEL == logging.INFO

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
