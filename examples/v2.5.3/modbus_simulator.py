#!/usr/bin/env python3
# pylint: disable=missing-raises-doc
"""An example of creating a fully implemented modbus server.

with read/write data as well as user configurable base data
"""
import logging
import pickle  # nosec
from optparse import OptionParser  # pylint: disable=deprecated-module

from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
from pymodbus.server import StartTcpServer


# -------------------------------------------------------------------------- #
# Logging
# -------------------------------------------------------------------------- #
server_log = logging.getLogger("pymodbus.server")
protocol_log = logging.getLogger("pymodbus.protocol")
_logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------- #
# Extra Global Functions
# -------------------------------------------------------------------------- #
# These are extra helper functions that don't belong in a class
# -------------------------------------------------------------------------- #
# import getpass


def root_test():
    """Check to see if we are running as root"""
    return True  # removed for the time being as it isn't portable
    # return getpass.getuser() == "root"


# -------------------------------------------------------------------------- #
# Helper Classes
# -------------------------------------------------------------------------- #


class ConfigurationException(Exception):
    """Exception for configuration error"""

    def __init__(self, string):
        """Initialize the ConfigurationException instance

        :param string: The message to append to the exception
        """
        Exception.__init__(self, string)
        self.string = string

    def __str__(self):
        """Build a representation of the object

        :returns: A string representation of the object
        """
        return f"Configuration Error: {self.string}"


class Configuration:  # pylint: disable=too-few-public-methods
    """Class used to parse configuration file and create and modbus datastore.

    The format of the configuration file is actually just a
    python pickle, which is a compressed memory dump from
    the scraper.
    """

    def __init__(self, config):
        """Try to load a configuration file.

        lets the file not found exception fall through

        :param config: The pickled datastore
        """
        try:
            self.file = open(config, "rb")  # pylint: disable=consider-using-with
        except Exception as exc:
            _logger.critical(str(exc))
            raise ConfigurationException(  # pylint: disable=raise-missing-from
                f"File not found {config}"
            )

    def parse(self):
        """Parse the config file and creates a server context"""
        handle = pickle.load(self.file)  # nosec
        try:  # test for existence, or bomb
            dsd = handle["di"]
            csd = handle["ci"]
            hsd = handle["hr"]
            isd = handle["ir"]
        except Exception:
            raise ConfigurationException(  # pylint: disable=raise-missing-from
                "Invalid Configuration"
            )
        slave = ModbusSlaveContext(d=dsd, c=csd, h=hsd, i=isd)
        return ModbusServerContext(slaves=slave)


# -------------------------------------------------------------------------- #
# Main start point
# -------------------------------------------------------------------------- #


def main():
    """Server launcher"""
    parser = OptionParser()
    parser.add_option(
        "-c", "--conf", help="The configuration file to load", dest="file"
    )
    parser.add_option(
        "-D",
        "--debug",
        help="Turn on to enable tracing",
        action="store_true",
        dest="debug",
        default=False,
    )
    (opt, _) = parser.parse_args()

    # enable debugging information
    if opt.debug:
        try:
            server_log.setLevel(logging.DEBUG)
            protocol_log.setLevel(logging.DEBUG)
        except Exception:  # pylint: disable=broad-except
            print("Logging is not supported on this system")

    # parse configuration file and run
    try:
        conf = Configuration(opt.file)
        StartTcpServer(context=conf.parse())
    except ConfigurationException as err:
        print(err)
        parser.print_help()


# -------------------------------------------------------------------------- #
# Main jumper
# -------------------------------------------------------------------------- #


if __name__ == "__main__":
    if root_test():
        main()
    else:
        print("This script must be run as root!")
