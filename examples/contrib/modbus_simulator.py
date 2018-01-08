#!/usr/bin/env python
"""
An example of creating a fully implemented modbus server
with read/write data as well as user configurable base data
"""

import pickle
from optparse import OptionParser
from twisted.internet import reactor

from pymodbus.server.async import StartTcpServer
from pymodbus.datastore import ModbusServerContext,ModbusSlaveContext

# -------------------------------------------------------------------------- #
# Logging
# -------------------------------------------------------------------------- #
import logging
logging.basicConfig()

server_log = logging.getLogger("pymodbus.server")
protocol_log = logging.getLogger("pymodbus.protocol")

# -------------------------------------------------------------------------- #
# Extra Global Functions
# -------------------------------------------------------------------------- #
# These are extra helper functions that don't belong in a class
# -------------------------------------------------------------------------- #
import getpass


def root_test():
    """ Simple test to see if we are running as root """
    return True  # removed for the time being as it isn't portable
    #return getpass.getuser() == "root"

# -------------------------------------------------------------------------- #
# Helper Classes
# -------------------------------------------------------------------------- #


class ConfigurationException(Exception):
    """ Exception for configuration error """

    def __init__(self, string):
        """ Initializes the ConfigurationException instance

        :param string: The message to append to the exception
        """
        Exception.__init__(self, string)
        self.string = string

    def __str__(self):
        """ Builds a representation of the object

        :returns: A string representation of the object
        """
        return 'Configuration Error: %s' % self.string



class Configuration:
    """
    Class used to parse configuration file and create and modbus
    datastore.

    The format of the configuration file is actually just a
    python pickle, which is a compressed memory dump from
    the scraper.
    """

    def __init__(self, config):
        """
        Trys to load a configuration file, lets the file not
        found exception fall through

        :param config: The pickled datastore
        """
        try:
            self.file = open(config, "rb")
        except Exception as e:
            _logger.critical(str(e))
            raise ConfigurationException("File not found %s" % config)

    def parse(self):
        """ Parses the config file and creates a server context
        """
        handle = pickle.load(self.file)
        try:  # test for existance, or bomb
            dsd = handle['di']
            csd = handle['ci']
            hsd = handle['hr']
            isd = handle['ir']
        except Exception:
            raise ConfigurationException("Invalid Configuration")
        slave = ModbusSlaveContext(d=dsd, c=csd, h=hsd, i=isd)
        return ModbusServerContext(slaves=slave)

# -------------------------------------------------------------------------- #
# Main start point
# -------------------------------------------------------------------------- #


def main():
    """ Server launcher """
    parser = OptionParser()
    parser.add_option("-c", "--conf",
                      help="The configuration file to load",
                      dest="file")
    parser.add_option("-D", "--debug",
                      help="Turn on to enable tracing",
                      action="store_true", dest="debug", default=False)
    (opt, arg) = parser.parse_args()

    # enable debugging information
    if opt.debug:
        try:
            server_log.setLevel(logging.DEBUG)
            protocol_log.setLevel(logging.DEBUG)
        except Exception as e:
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
