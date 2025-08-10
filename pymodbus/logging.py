"""Pymodbus: Modbus Protocol Implementation.

Released under the BSD license
"""
from __future__ import annotations

import logging
from binascii import b2a_hex
from logging import NullHandler as __null

from pymodbus.utilities import hexlify_packets


# ---------------------------------------------------------------------------#
#  Block unhandled logging
# ---------------------------------------------------------------------------#
logging.getLogger("pymodbus_internal").addHandler(__null())


def pymodbus_apply_logging_config(
    level: str | int = logging.DEBUG, log_file_name: str | None = None
):
    """Apply basic logging configuration used by default by Pymodbus maintainers.

    :param level: (optional) set log level, if not set it is inherited.
    :param log_file_name: (optional) log additional to file

    Please call this function to format logging appropriately when opening issues.
    """
    if isinstance(level, str):
        level = level.upper()
    Log.apply_logging_config(level, log_file_name)

def pymodbus_get_last_frames() -> str:
    """Prepare and return last frames, for automatic debugging."""
    return Log.get_last_frames()

class Log:
    """Class to hide logging complexity.

    :meta private:
    """

    SEND_DATA = "send"
    RECV_DATA = "recv"
    EXTRA_DATA = "extra"
    MAX_FRAMES = 20
    frame_dump: list[tuple] = []

    _logger = logging.getLogger(__name__)
    last_log_text = ""
    repeat_log = False

    @classmethod
    def apply_logging_config(cls, level, log_file_name):
        """Apply basic logging configuration."""
        if level == logging.NOTSET:
            level = cls._logger.getEffectiveLevel()
        if isinstance(level, str):
            level = level.upper()
        log_stream_handler = logging.StreamHandler()
        log_formatter = logging.Formatter(
            "%(asctime)s %(levelname)-5s %(module)s:%(lineno)s %(message)s"
        )
        log_stream_handler.setFormatter(log_formatter)
        cls._logger.addHandler(log_stream_handler)
        if log_file_name:
            log_file_handler = logging.FileHandler(log_file_name)
            log_file_handler.setFormatter(log_formatter)
            cls._logger.addHandler(log_file_handler)
        cls.setLevel(level)

    @classmethod
    def setLevel(cls, level):
        """Apply basic logging level."""
        cls._logger.setLevel(level)

    @classmethod
    def build_frame_log_line(cls, data_type, data, old_data):
        """Change frame into log line."""
        if data_type == cls.SEND_DATA:
            log_text = cls.build_msg("send: {}", data, ":hex")
        elif data_type == cls.RECV_DATA:
            log_text = cls.build_msg(
                "recv: {} extra data: {}",
                data,
                ":hex",
                old_data,
                ":hex",
            )
        else:
            log_text = cls.build_msg(
                "extra: {} unexpected data: {}",
                data,
                ":hex",
                old_data,
                ":hex",
            )
        return log_text

    @classmethod
    def get_last_frames(cls):
        """Prepare and return last frames, for automatic debugging."""
        log_text = ""
        for (data_type, data, old_data) in cls.frame_dump:
            log_text += f"\n>>>>> {cls.build_frame_log_line(data_type, data, old_data)}"
        cls.frame_dump = []
        return log_text

    @classmethod
    def transport_dump(cls, data_type, data, old_data):
        """Debug transport data."""
        if not cls._logger.isEnabledFor(logging.DEBUG):
            cls.frame_dump.append((data_type, data, old_data))
            if len(cls.frame_dump) > cls.MAX_FRAMES:
                del cls.frame_dump[0]
            return

        cls.frame_dump = []
        cls._logger.debug(cls.build_frame_log_line(data_type, data, old_data), stacklevel=2)

    @classmethod
    def build_msg(cls, txt, *args):
        """Build message."""
        string_args = []
        count_args = len(args) - 1
        skip = False
        for i in range(count_args + 1):
            if skip:
                skip = False
                continue
            if (
                i < count_args
                and isinstance(args[i + 1], str)
                and args[i + 1][0] == ":"
            ):
                if args[i + 1] == ":hex":
                    string_args.append(hexlify_packets(args[i]))
                elif args[i + 1] == ":str":
                    string_args.append(str(args[i]))
                else: # args[i + 1] == ":b2a":
                    string_args.append(b2a_hex(args[i]))
                skip = True
            else:
                string_args.append(args[i])
        if (log_text := txt.format(*string_args)) != cls.last_log_text:
            cls.last_log_text = log_text
            cls.repeat_log = False
            return log_text
        if not cls.repeat_log:
            cls.repeat_log = True
            return "Repeating...."
        return cls.last_log_text

    @classmethod
    def info(cls, txt, *args):
        """Log info messages."""
        if cls._logger.isEnabledFor(logging.INFO):
            if (log_text := cls.build_msg(txt, *args)):
                cls._logger.info(log_text, stacklevel=2)

    @classmethod
    def debug(cls, txt, *args):
        """Log debug messages."""
        if cls._logger.isEnabledFor(logging.DEBUG):
            if (log_text := cls.build_msg(txt, *args)):
                cls._logger.debug(log_text, stacklevel=2)

    @classmethod
    def warning(cls, txt, *args):
        """Log warning messages."""
        if cls._logger.isEnabledFor(logging.WARNING):
            if (log_text := cls.build_msg(txt, *args)):
                cls._logger.warning(log_text, stacklevel=2)

    @classmethod
    def error(cls, txt, *args):
        """Log error messages."""
        if cls._logger.isEnabledFor(logging.ERROR):
            if (log_text := cls.build_msg(txt, *args)):
                if not cls._logger.isEnabledFor(logging.DEBUG):
                    log_text += cls.get_last_frames()
                cls._logger.error(log_text, stacklevel=2)

    @classmethod
    def critical(cls, txt, *args):
        """Log critical messages."""
        if (log_text := cls.build_msg(txt, *args)):
            if not cls._logger.isEnabledFor(logging.DEBUG):
                log_text += cls.get_last_frames()
            cls._logger.critical(log_text, stacklevel=2)
