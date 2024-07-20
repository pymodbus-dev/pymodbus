"""Test datastore."""
import logging
from unittest import mock

import pytest

from pymodbus.logging import Log, pymodbus_apply_logging_config


class TestLogging:
    """Tests of pymodbus logging."""

    def test_log_dont_call_build_msg(self):
        """Verify that build_msg is not called unnecessary."""
        with mock.patch("pymodbus.logging.Log.build_msg") as build_msg_mock:
            Log.setLevel(logging.INFO)
            Log.debug("test")
            build_msg_mock.assert_not_called()

            Log.setLevel(logging.DEBUG)
            Log.debug("test2")
            build_msg_mock.assert_called_once()

    def test_log_simple(self):
        """Test simple string."""
        txt = "simple string"
        log_txt = Log.build_msg(txt)
        assert log_txt == txt

    @pytest.mark.parametrize(
        ("txt", "result", "params"),
        [
            ("string {} {} {}", "string 101 102 103", (101, 102, 103)),
            ("string {}", "string 0x41 0x42 0x43 0x44", (b"ABCD", ":hex")),
            ("string {}", "string b'41424344'", (b"ABCD", ":b2a")),
            ("string {}", "string 125", (125, ":str")),
        ],
    )
    def test_log_parms(self, txt, result, params):
        """Test string with parameters (old f-string)."""
        log_txt = Log.build_msg(txt, *params)
        assert log_txt == result

    def test_apply_logging(self):
        """Test pymodbus_apply_logging_config."""

        pymodbus_apply_logging_config("debug")
        pymodbus_apply_logging_config(logging.NOTSET)
        pymodbus_apply_logging_config("debug", "pymodbus.log")
        pymodbus_apply_logging_config("info")
        Log.info("test")
        pymodbus_apply_logging_config("warning")
        Log.warning("test")
        pymodbus_apply_logging_config("critical")
        Log.critical("test")
        pymodbus_apply_logging_config("error")
        Log.error("test")
