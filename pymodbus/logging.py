"""Pymodbus: Modbus Protocol Implementation.

Released under the the BSD license
"""
import logging
from binascii import b2a_hex
from logging import NullHandler as __null
from typing import Union

from pymodbus.utilities import hexlify_packets


# ---------------------------------------------------------------------------#
#  Block unhandled logging
# ---------------------------------------------------------------------------#
logging.getLogger(__name__).addHandler(__null())


def pymodbus_apply_logging_config(
    level: Union[str, int] = logging.DEBUG, log_file_name: str = None
):
    """Apply basic logging configuration used by default by Pymodbus maintainers.

    :param level: (optional) set log level, if not set it is inherited.
    :param log_file_name: (optional) log additional to file

    Please call this function to format logging appropriately when opening issues.
    """
    Log.apply_logging_config(level, log_file_name)


class Log:
    """Class to hide logging complexity.

    :meta private:
    """

    LOG_LEVEL = logging.NOTSET
    _logger = logging.getLogger(__name__)

    @classmethod
    def apply_logging_config(cls, level, log_file_name):
        """Apply basic logging configuration"""
        if level == logging.NOTSET:
            level = cls._logger.getEffectiveLevel()
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
        """Apply basic logging level"""
        cls._logger.setLevel(level)
        cls.LOG_LEVEL = level

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
                elif args[i + 1] == ":b2a":
                    string_args.append(b2a_hex(args[i]))
                skip = True
            else:
                string_args.append(args[i])
        return txt.format(*string_args)

    @classmethod
    def info(cls, txt, *args):
        """Log info messagees."""
        if cls.LOG_LEVEL == logging.NOTSET:
            cls.LOG_LEVEL = cls._logger.getEffectiveLevel()
        if logging.INFO >= cls.LOG_LEVEL:
            cls._logger.info(cls.build_msg(txt, *args))

    @classmethod
    def debug(cls, txt, *args):
        """Log debug messagees."""
        if cls.LOG_LEVEL == logging.NOTSET:
            cls.LOG_LEVEL = cls._logger.getEffectiveLevel()
        if logging.DEBUG >= cls.LOG_LEVEL:
            cls._logger.debug(cls.build_msg(txt, *args))

    @classmethod
    def warning(cls, txt, *args):
        """Log warning messagees."""
        if cls.LOG_LEVEL == logging.NOTSET:
            cls.LOG_LEVEL = cls._logger.getEffectiveLevel()
        if logging.WARNING >= cls.LOG_LEVEL:
            cls._logger.warning(cls.build_msg(txt, *args))

    @classmethod
    def error(cls, txt, *args):
        """Log error messagees."""
        if cls.LOG_LEVEL == logging.NOTSET:
            cls.LOG_LEVEL = cls._logger.getEffectiveLevel()
        if logging.ERROR >= cls.LOG_LEVEL:
            cls._logger.error(cls.build_msg(txt, *args))

    @classmethod
    def critical(cls, txt, *args):
        """Log critical messagees."""
        if cls.LOG_LEVEL == logging.NOTSET:
            cls.LOG_LEVEL = cls._logger.getEffectiveLevel()
        if logging.CRITICAL >= cls.LOG_LEVEL:
            cls._logger.critical(cls.build_msg(txt, *args))
