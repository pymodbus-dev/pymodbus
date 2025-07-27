Pymodbus 4.0 upgrade procedure
==============================

Pymodbus 4.0 contains a number of incompatibilities with Pymodbus 3.x, however
most of these are simple edits.


Python 3.9
----------
Python 3.9 is reaching end of life and from october 2025 no longer receives security updates.

Pymodbus starting with v4.0 start using python 3.10 features, and thus users need to update to
at least python v3.10

Users that cannot upgrade the python version, should not upgrade pymodbus to v4.X


Start<x>Server
--------------
custom_funcion= is changed to custom_pdu= and is handled by Modbus<x>Server.


payload classes removed
-----------------------
Please replace by result.convert_from_registers() and/or convert_to_registers()


Simple replacements
-------------------

please replace parameters as follows

- slave= with device_id=
- slaves= with device_ids=
- ModbusServerContext(slaves=) with ModbusServerContext(devices=)

please rename classes/methods as follows

- ModbusSlaveContext to ModbusDeviceContext
- RemoteSlaveContext to RemoteDeviceContext
- report_slave_id to report_device_id
- diag_read_slave_message_count with diag_read_device_message_count
- diag_read_slave_no_response_count with diag_read_device_no_response_count
- diag_read_slave_nak_count with diag_read_device_nak_count
- diag_read_slave_busy_count with diag_read_device_busy_count
- ReturnSlaveMessageCountRequest with ReturnDeviceMessageCountRequest
- ReturnSlaveNoResponseCountRequest with ReturnDeviceNoResponseCountRequest
- ReturnSlaveNAKCountRequest with ReturnDeviceNAKCountRequest
- ReturnSlaveBusyCountRequest with ReturnDeviceBusyCountRequest
- ReturnSlaveBusCharacterOverrunCountRequest with ReturnDeviceBusCharacterOverrunCountRequest
