"""Test datastore."""
import logging
import os
from unittest import mock

import pytest

from pymodbus.logging import (
    Log,
    pymodbus_apply_logging_config,
    pymodbus_get_last_frames,
)


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
        LOG_FILE = "pymodbus.log"
        pymodbus_apply_logging_config("debug", LOG_FILE)
        pymodbus_apply_logging_config("info")
        pymodbus_apply_logging_config(logging.NOTSET)
        Log.debug("test 1no")
        pymodbus_apply_logging_config(logging.CRITICAL)
        Log.debug("test 1no")
        pymodbus_apply_logging_config("debug")
        Log.debug("test 1")
        Log.debug("test 1")
        Log.debug("test 1")
        Log.error("get frames")
        Log.critical("get frames")
        pymodbus_apply_logging_config(logging.CRITICAL)
        Log.warning("test 2no")
        pymodbus_apply_logging_config("warning")
        Log.warning("test 2")
        Log.warning("test 2")
        Log.warning("test 2")
        pymodbus_apply_logging_config(logging.CRITICAL)
        Log.critical("test 3no")
        pymodbus_apply_logging_config("critical")
        Log.critical("test 3")
        Log.critical("test 3")
        Log.critical("test 3")
        pymodbus_apply_logging_config(logging.CRITICAL)
        Log.error("test 4no")
        pymodbus_apply_logging_config("error")
        Log.error("test 4")
        Log.error("test 4")
        Log.error("test 4")
        pymodbus_apply_logging_config(logging.CRITICAL)
        Log.info("test 5no")
        pymodbus_apply_logging_config("info")
        Log.info("test 5")
        Log.info("test 5")
        Log.info("test 5")
        logging.shutdown()
        os.remove(LOG_FILE)


    def test_apply_build_no(self):
        """Test pymodbus_apply_logging_config."""
        with mock.patch("pymodbus.logging.Log.build_msg") as build:
            build.return_value = None
            Log.critical("test 0")
            pymodbus_apply_logging_config("debug")
            Log.debug("test 1")
            pymodbus_apply_logging_config("warning")
            Log.warning("test 2")
            pymodbus_apply_logging_config("critical")
            pymodbus_apply_logging_config("error")
            Log.error("test 4")
            pymodbus_apply_logging_config("info")
            Log.info("test 5")

    def test_log_get_frames(self):
        """Test get_frames."""
        pymodbus_get_last_frames()
        for _ in range(100):
            Log.transport_dump(Log.SEND_DATA, b'678', b'9')
        pymodbus_get_last_frames()

    def test_transport_dump(self):
        """Test transport_dump."""
        pymodbus_apply_logging_config("error")
        Log.transport_dump(Log.SEND_DATA, b'123', b'4')
        for _ in range(100):
            Log.transport_dump(Log.SEND_DATA, b'678', b'9')
        pymodbus_apply_logging_config("debug")
        Log.transport_dump(Log.SEND_DATA, b'123', b'4')

    def test_build_frame_log_line(self):
        """Test build_frame_log_line."""
        Log.build_frame_log_line(Log.SEND_DATA, b'123', b'4')
        Log.build_frame_log_line(Log.RECV_DATA, b'123', b'4')
        Log.build_frame_log_line("Unknown", b'123', b'4')

