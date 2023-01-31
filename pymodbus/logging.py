"""Pymodbus: Modbus Protocol Implementation.

Released under the the BSD license
"""

import logging
from binascii import b2a_hex
from logging import NullHandler as __null

from pymodbus.utilities import hexlify_packets


# ---------------------------------------------------------------------------#
#  Block unhandled logging
# ---------------------------------------------------------------------------#
logging.getLogger(__name__).addHandler(__null())


class Log:
    """Class to hide logging complexity.

    :meta private:
    """

    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    DEBUG = logging.DEBUG
    INFO = logging.INFO

    LOG_LEVEL = logging.WARNING
    _logger = logging.getLogger(__name__)

    @classmethod
    def apply_logging_config(cls, level=logging.WARNING):
        """Apply basic logging configuration"""
        logging.basicConfig(
            format="%(asctime)s %(levelname)-5s %(module)s:%(lineno)s %(message)s",
            datefmt="%H:%M:%S",
        )
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
        if logging.INFO >= cls.LOG_LEVEL:
            cls._logger.info(cls.build_msg(txt, *args))

    @classmethod
    def debug(cls, txt, *args):
        """Log debug messagees."""
        if logging.DEBUG >= cls.LOG_LEVEL:
            cls._logger.debug(cls.build_msg(txt, *args))

    @classmethod
    def warning(cls, txt, *args):
        """Log warning messagees."""
        if logging.WARNING >= cls.LOG_LEVEL:
            cls._logger.warning(cls.build_msg(txt, *args))

    @classmethod
    def error(cls, txt, *args):
        """Log error messagees."""
        if logging.ERROR >= cls.LOG_LEVEL:
            cls._logger.error(cls.build_msg(txt, *args))

    @classmethod
    def critical(cls, txt, *args):
        """Log critical messagees."""
        if logging.CRITICAL >= cls.LOG_LEVEL:
            cls._logger.critical(cls.build_msg(txt, *args))
