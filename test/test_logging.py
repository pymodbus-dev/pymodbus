"""Test datastore."""
import logging

from unittest.mock import patch
import pytest

from pymodbus import pymodbus_apply_logging_config
from pymodbus.logging import Log


class TestLogging:
    """Tests of pymodbus logging."""

    def test_log_dont_call_build_msg(self):
        with patch("pymodbus.logging.Log.build_msg") as build_msg_mock:

            Log.setLevel(logging.INFO)
            Log.debug("test")
            assert build_msg_mock.call_count == 0

            Log.setLevel(logging.DEBUG)
            Log.debug("test2")
            assert build_msg_mock.call_count == 1


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
