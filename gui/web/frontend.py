'''
Pymodbus Web Frontend
=======================================

This is a simple web frontend using bottle as the web framework.
This can be hosted using any wsgi adapter.
'''
from bottle import route, request, Bottle
from bottle import jinja2_template as template
from pymodbus.device import ModbusAccessControl
from pymodbus.device import ModbusControlBlock

#---------------------------------------------------------------------------# 
# REST API
#---------------------------------------------------------------------------# 
class Response(object):
    '''
    A collection of common responses for the frontend api
    '''
    successful = { 'status' : 200 }
    failure    = { 'status' : 500 }

class ModbusApiWebApp(object):
    '''
    This is the web REST api interace into the pymodbus
    service.  It can be consumed by any utility that can
    make web requests (javascript).
    '''
    _namespace = '/api/v1'

    def __init__(self, server):
        ''' Initialize a new instance of the ModbusApi

        :param server: The current server instance
        '''
        self._server = server

    #---------------------------------------------------------------------#
    # Device API
    #---------------------------------------------------------------------#
    def get_device(self):
        return {
            'mode'        : self._server.control.Mode,
            'delimiter'   : self._server.control.Delimiter,
            'listen-only' : self._server.control.ListenOnly,
            'identity'    : self._server.control.Identity.summary(),
            'counters'    : dict(self._server.control.Counter),
            'diagnostic'  : self._server.control.getDiagnosticRegister(),
        }
    
    def get_device_identity(self):
        return {
            'identity' : dict(self._server.control.Identity)
        }
    
    def get_device_events(self):
        return {
            'events' : self._server.control.Events
        }
    
    def delete_device_events(self):
        self._server.control.clearEvents()
        return Response.successful
    
    def get_device_host(self):
        return {
            'hosts' : list(self._server.access)
        }
    
    def post_device_host(self):
        value = request.forms.get('host')
        if value:
            self._server.access.add(value)
        return Response.successful
    
    def delete_device_host(self):
        value = request.forms.get('host')
        if value:
            self._server.access.remove(value)
        return Response.successful
    
    def post_device_delimiter(self):
        value = request.forms.get('delimiter')
        if value:
            self._server.control.Delimiter = value
        return Response.successful
    
    def post_device_mode(self):
        value = request.forms.get('mode')
        if value:
            self._server.control.Mode = value
        return Response.successful
    
    def post_device_reset(self):
        self._server.control.reset()
        return Response.successful

    #---------------------------------------------------------------------#
    # Datastore API
    #---------------------------------------------------------------------#

#---------------------------------------------------------------------------# 
# Configurations
#---------------------------------------------------------------------------# 
def register_routes(application, register):
    ''' A helper method to register the routes of an application
    based on convention.

    :param application: The application instance to register
    :param register: The bottle instance to register the application with
    '''
    from bottle import route

    methods = dir(application)
    methods = filter(lambda n: not n.startswith('_'), methods)
    for method in methods:
        pieces = method.split('_')
        verb, path = pieces[0], pieces[1:]
        path.insert(0, application._namespace)
        path = '/'.join(path)
        func = application.__getattribute__(method)
        register.route(path, method=verb, name=method)(func)

def build_application(server):
    ''' Helper method to create and initiailze a bottle application

    :param server: The modbus server to pull instance data from
    :returns: An initialied bottle application
    '''
    api = ModbusApiWebApp(server)
    register = Bottle()
    register_routes(api, register)
    return register

#---------------------------------------------------------------------------# 
# Start Methods
#---------------------------------------------------------------------------# 
def RunModbusFrontend(server, port=503):
    ''' Helper method to host bottle in twisted

    :param server: The modbus server to pull instance data from
    :param port: The port to host the service on
    '''
    from bottle import TwistedServer, run
    application = build_application(server)
    run(app=application, server=TwistedServer, port=port)

def RunDebugModbusFrontend(server, port=503):
    ''' Helper method to start the bottle server

    :param server: The modbus server to pull instance data from
    :param port: The port to host the service on
    '''
    from bottle import run

    application = build_application(server)
    run(app=application, port=port)

if __name__ == '__main__':
    from pymodbus.server.async import ModbusServerFactory

    RunDebugModbusFrontend(ModbusServerFactory)
