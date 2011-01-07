'''
'''
from bottle import route, run
from bottle import get, post, delete
from pymodbus.device import ModbusAccessControl
from pymodbus.device import ModbusControlBlock

#---------------------------------------------------------------------------# 
# Singletons
#---------------------------------------------------------------------------# 
_modbus_access  = ModbusAccessControl()
_modbus_control = ModbusControlBlock()

#---------------------------------------------------------------------------# 
# REST API
#---------------------------------------------------------------------------# 
@get('/api/device')
def get_device():
    return {
        'mode'        : _modbus_control.Mode,
        'delimiter'   : _modbus_control.Delimiter,
        'listen-only' : _modbus_control.ListenOnly,
        'identity'    : _modbus_control.Identity.summary(),
        'counters'    : dict(_modbus_control.Counter),
        'diagnostic'  : _modbus_control.getDiagnosticRegister(),
    }

@get('/api/device/identity')
def get_device_identity():
    return { 'identity' : dict(_modbus_control.Identity) }

@get('/api/device/events')
def get_device_events():
    return { 'events' : _modbus_control.Events }

@delete('/api/device/events')
def delete_device_events():
    _modbus_control.clearEvents()
    return { 'status' : 200 }

@get('/api/device/host')
def get_device_host():
    return { 'hosts' : list(_modbus_access) }

@post('/api/device/host')
def post_device_host():
    value = request.forms.get('host')
    if value: _modbus_access.add(value)
    return { 'status' : 200 }

@delete('/api/device/host')
def delete_device_host():
    value = request.forms.get('host')
    if value: _modbus_access.remove(value)
    return { 'status' : 200 }

@post('/api/device/delimiter')
def post_device_delimiter():
    value = request.forms.get('delimiter')
    if value: _modbus_control.Delimiter = value
    return { 'status' : 200 }

@post('/api/device/mode')
def post_device_mode():
    value = request.forms.get('mode')
    if value: _modbus_control.Mode = value
    return { 'status' : 200 }

@post('/api/device/reset')
def post_device_reset():
    return { 'status' : 200 }

#---------------------------------------------------------------------------# 
# Webpage
#---------------------------------------------------------------------------# 
run(port=8080)
