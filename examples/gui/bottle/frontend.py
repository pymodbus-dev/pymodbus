"""
Pymodbus Web Frontend
=======================================

This is a simple web frontend using bottle as the web framework.
This can be hosted using any wsgi adapter.
"""
from __future__ import print_function
import json, inspect
from bottle import route, request, Bottle
from bottle import static_file
from bottle import jinja2_template as template

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# REST API
# --------------------------------------------------------------------------- #
class Response(object):
    """
    A collection of common responses for the frontend api
    """
    success = { 'status' : 200 }
    failure = { 'status' : 500 }

class ModbusApiWebApp(object):
    """
    This is the web REST api interace into the pymodbus
    service.  It can be consumed by any utility that can
    make web requests (javascript).
    """
    _namespace = '/api/v1'

    def __init__(self, server):
        """ Initialize a new instance of the ModbusApi

        :param server: The current server instance
        """
        self._server = server

    #---------------------------------------------------------------------#
    # Device API
    #---------------------------------------------------------------------#
    def get_device(self):
        return {
            'mode'        : self._server.control.Mode,
            'delimiter'   : self._server.control.Delimiter,
            'readonly'    : self._server.control.ListenOnly,
            'identity'    : self._server.control.Identity.summary(),
            'counters'    : dict(self._server.control.Counter),
            'diagnostic'  : self._server.control.getDiagnosticRegister(),
        }
    
    def get_device_identity(self):
        return {
            'identity' : dict(self._server.control.Identity)
        }

    def get_device_counters(self):
        return {
            'counters' : dict(self._server.control.Counter)
        }
    
    def get_device_events(self):
        return {
            'events' : self._server.control.Events
        }

    def get_device_plus(self):
        return {
            'plus' : dict(self._server.control.Plus)
        }
    
    def delete_device_events(self):
        self._server.control.clearEvents()
        return Response.success
    
    def get_device_host(self):
        return {
            'hosts' : list(self._server.access)
        }
    
    def post_device_host(self):
        value = request.forms.get('host')
        if value:
            self._server.access.add(value)
        return Response.success
    
    def delete_device_host(self):
        value = request.forms.get('host')
        if value:
            self._server.access.remove(value)
        return Response.success
    
    def post_device_delimiter(self):
        value = request.forms.get('delimiter')
        if value:
            self._server.control.Delimiter = value
        return Response.success
    
    def post_device_mode(self):
        value = request.forms.get('mode')
        if value:
            self._server.control.Mode = value
        return Response.success
    
    def post_device_reset(self):
        self._server.control.reset()
        return Response.success

    #---------------------------------------------------------------------#
    # Datastore Get API
    #---------------------------------------------------------------------#
    def __get_data(self, store, address, count, slave='00'):
        try:
            address, count = int(address), int(count)
            context = self._server.store[int(store)]
            values  = context.getValues(store, address, count)
            values  = dict(zip(range(address, address + count), values))
            result  = { 'data' : values }
            result.update(Response.success)
            return result
        except Exception as ex:
            log.error(ex)
        return Response.failure

    def get_coils(self, address='0', count='1'):
        return self.__get_data(1, address, count)

    def get_discretes(self, address='0', count='1'):
        return self.__get_data(2, address, count)

    def get_holdings(self, address='0', count='1'):
        return self.__get_data(3, address, count)

    def get_inputs(self, address='0', count='1'):
        return self.__get_data(4, address, count)

    #---------------------------------------------------------------------#
    # Datastore Update API
    #---------------------------------------------------------------------#
    def __set_data(self, store, address, values, slave='00'):
        try:
            address = int(address)
            values  = json.loads(values)
            print(values)
            context = self._server.store[int(store)]
            context.setValues(store, address, values)
            return Response.success
        except Exception as ex:
            log.error(ex)
        return Response.failure

    def post_coils(self, address='0'):
        values = request.forms.get('data')
        return self.__set_data(1, address, values)

    def post_discretes(self, address='0'):
        values = request.forms.get('data')
        return self.__set_data(2, address, values)

    def post_holding(self, address='0'):
        values = request.forms.get('data')
        return self.__set_data(3, address, values)

    def post_inputs(self, address='0'):
        values = request.forms.get('data')
        return self.__set_data(4, address, values)

#---------------------------------------------------------------------#
# webpage routes
#---------------------------------------------------------------------#
def register_web_routes(application, register):
    """ A helper method to register the default web routes of
    a single page application.

    :param application: The application instance to register
    :param register: The bottle instance to register the application with
    """
    def get_index_file():
        return template('index.html')
    
    def get_static_file(filename):
        return static_file(filename, root='./media')

    register.route('/', method='GET', name='get_index_file')(get_index_file)
    register.route('/media/<filename:path>', method='GET', name='get_static_file')(get_static_file)

# --------------------------------------------------------------------------- #
# Configurations
# --------------------------------------------------------------------------- #
def register_api_routes(application, register):
    """ A helper method to register the routes of an application
    based on convention. This is easier to manage than having to
    decorate each method with a static route name.

    :param application: The application instance to register
    :param register: The bottle instance to register the application with
    """
    log.info("installing application routes:")
    methods = inspect.getmembers(application)
    methods = filter(lambda n: not n[0].startswith('_'), methods)
    for method, func in dict(methods).iteritems():
        pieces = method.split('_')
        verb, path = pieces[0], pieces[1:]
        args = inspect.getargspec(func).args[1:]
        args = ['<%s>' % arg for arg in args]
        args = '/'.join(args)
        args = '' if len(args) == 0 else '/' + args
        path.insert(0, application._namespace)
        path = '/'.join(path) + args 
        log.info("%6s: %s" % (verb, path))
        register.route(path, method=verb, name=method)(func)

def build_application(server):
    """ Helper method to create and initiailze a bottle application

    :param server: The modbus server to pull instance data from
    :returns: An initialied bottle application
    """
    log.info("building web application")
    api = ModbusApiWebApp(server)
    register = Bottle()
    register_api_routes(api, register)
    register_web_routes(api, register)
    return register

# --------------------------------------------------------------------------- #
# Start Methods
# --------------------------------------------------------------------------- #
def RunModbusFrontend(server, port=8080):
    """ Helper method to host bottle in twisted

    :param server: The modbus server to pull instance data from
    :param port: The port to host the service on
    """
    from bottle import TwistedServer, run

    application = build_application(server)
    run(app=application, server=TwistedServer, port=port)

def RunDebugModbusFrontend(server, port=8080):
    """ Helper method to start the bottle server

    :param server: The modbus server to pull instance data from
    :param port: The port to host the service on
    """
    from bottle import run

    application = build_application(server)
    run(app=application, port=port)

if __name__ == '__main__':
    # ------------------------------------------------------------
    # an example server configuration
    # ------------------------------------------------------------
    from pymodbus.server.async import ModbusServerFactory
    from pymodbus.constants import Defaults
    from pymodbus.device import ModbusDeviceIdentification
    from pymodbus.datastore import ModbusSequentialDataBlock
    from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
    from twisted.internet import reactor

    # ------------------------------------------------------------
    # initialize the identity
    # ------------------------------------------------------------

    identity = ModbusDeviceIdentification()
    identity.VendorName  = 'Pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl   = 'http://github.com/bashwork/pymodbus/'
    identity.ProductName = 'Pymodbus Server'
    identity.ModelName   = 'Pymodbus Server'
    identity.MajorMinorRevision = '1.0'

    # ------------------------------------------------------------
    # initialize the datastore
    # ------------------------------------------------------------
    store = ModbusSlaveContext(
        di = ModbusSequentialDataBlock(0, [17]*100),
        co = ModbusSequentialDataBlock(0, [17]*100),
        hr = ModbusSequentialDataBlock(0, [17]*100),
        ir = ModbusSequentialDataBlock(0, [17]*100))
    context = ModbusServerContext(slaves=store, single=True)

    # ------------------------------------------------------------
    # initialize the factory 
    # ------------------------------------------------------------
    address = ("", Defaults.Port)
    factory = ModbusServerFactory(context, None, identity)

    # ------------------------------------------------------------
    # start the servers
    # ------------------------------------------------------------
    log.info("Starting Modbus TCP Server on %s:%s" % address)
    reactor.listenTCP(address[1], factory, interface=address[0])
    RunDebugModbusFrontend(factory)
