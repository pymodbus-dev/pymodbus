"""
"""
from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet

from pymodbus.constants import Defaults
from pymodbus.server.async import ModbusServerFactory
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.internal.ptwisted import InstallManagementConsole

class Options(usage.Options):
    """
    The following are the options available to the
    pymodbus server.
    """
    optParameters = [
        ["port", "p", Defaults.Port, "The port number to listen on."],
        ["type", "t", "tcp", "The type of server to host (tcp, udp, ascii, rtu)"],
        ["store", "s", "./datastore", "The pickled datastore to use"],
        ["console", "c", False, "Should the management console be started"],
    ]

class ModbusServiceMaker(object):
    """
    A helper class used to build a twisted plugin
    """
    implements(IServiceMaker, IPlugin)
    tapname = "pymodbus"
    description = "A modbus server"
    options = Options

    def makeService(self, options):
        """
        Construct a service from the given options
        """
        if options["type"] == "tcp":
            server = internet.TCPServer
        else: server = internet.UDPServer


        framer = ModbusSocketFramer
        context = self._build_context(options['store'])
        factory = ModbusServerFactory(None, framer)
        if options['console']:
            InstallManagementConsole({ 'server' : factory })
        return server(int(options["port"]), factory)

    def _build_context(self, path):
        """
        A helper method to unpickle a datastore,
        note, this should be a ModbusServerContext.
        """
        import pickle
        try:
            context = pickle.load(path)
        except Exception: context = None
        return context

serviceMaker = ModbusServiceMaker()
