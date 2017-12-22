#!/usr/bin/env python
# -------------------------------------------------------------------------- #
# System
# -------------------------------------------------------------------------- #
import os
import getpass
import pickle
from threading import Thread

# -------------------------------------------------------------------------- #
# SNMP Simulator
# -------------------------------------------------------------------------- #
from twisted.internet import reactor
from twisted.internet import error as twisted_error
from pymodbus.server.async import ModbusServerFactory
from pymodbus.datastore import ModbusServerContext,ModbusSlaveContext

# -------------------------------------------------------------------------- #
# Logging
# -------------------------------------------------------------------------- #
import logging
log = logging.getLogger("pymodbus")

# -------------------------------------------------------------------------- #
# Application Error
# -------------------------------------------------------------------------- #


class ConfigurationException(Exception):
    """ Exception for configuration error """
    pass

# -------------------------------------------------------------------------- #
# Extra Global Functions
# -------------------------------------------------------------------------- #
# These are extra helper functions that don't belong in a class
# -------------------------------------------------------------------------- #


def root_test():
    """ Simple test to see if we are running as root """
    return getpass.getuser() == "root"

# -------------------------------------------------------------------------- #
# Simulator Class
# -------------------------------------------------------------------------- #


class Simulator(object):
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
            self.file = open(config, "r")
        except Exception:
            raise ConfigurationException("File not found %s" % config)

    def _parse(self):
        """ Parses the config file and creates a server context """
        try:
            handle = pickle.load(self.file)
            dsd = handle['di']
            csd = handle['ci']
            hsd = handle['hr']
            isd = handle['ir']
        except KeyError:
            raise ConfigurationException("Invalid Configuration")
        slave = ModbusSlaveContext(d=dsd, c=csd, h=hsd, i=isd)
        return ModbusServerContext(slaves=slave)

    def _simulator(self):
        """ Starts the snmp simulator """
        ports = [502]+range(20000,25000)
        for port in ports:
            try:
                reactor.listenTCP(port, ModbusServerFactory(self._parse()))
                log.debug('listening on port %d' % port)
                return port
            except twisted_error.CannotListenError:
                pass

    def run(self):
        """ Used to run the simulator """
        log.debug('simulator started')
        reactor.callWhenRunning(self._simulator)

# -------------------------------------------------------------------------- #
# Network reset thread
# -------------------------------------------------------------------------- #
# This is linux only, maybe I should make a base class that can be filled
# in for linux(debian/redhat)/windows/nix
# -------------------------------------------------------------------------- #


class NetworkReset(Thread):
    """
    This class is simply a daemon that is spun off at the end of the
    program to call the network restart function (an easy way to
    remove all the virtual interfaces)
    """

    def __init__(self):
        """ Initialize a new network reset thread """
        Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        """ Run the network reset """
        os.system("/etc/init.d/networking restart")
