=======================
PyModbus - API changes.
=======================

-------------
Version 3.4.0
-------------
- Modbus<x>Client .connect() returns True/False (connected or not)
- Modbue<x>Server handler=, allow_reuse_addr=, backlog= are no longer accepted
- ModbusTcpClient / AsyncModbusTcpClient no longer support unix path
- StartAsyncUnixServer / ModbusUnixServer removed (never worked on Windows)
- ModbusTlsServer reqclicert= is no longer accepted
- ModbusSerialServer auto_connect= is no longer accepted


-------------
Version 3.3.1
-------------

No changes.

-------------
Version 3.3.0
-------------
- ModbusTcpDiagClient is removed due to lack of support
- Clients have an optional parameter: on_reconnect_callback, Function that will be called just before a reconnection attempt.
- general parameter unit= -> slave=
- move SqlSlaveContext, RedisSlaveContext to examples/contrib (due to lack of maintenance)
- :code:`BinaryPayloadBuilder.to_string` was renamed to :code:`BinaryPayloadBuilder.encode`
- on_reconnect_callback for async clients works slightly different
- utilities/unpack_bitstring now expects an argument named `data` not `string`

-------------
Version 3.2.0
-------------
- helper to convert values in mixin: convert_from_registers, convert_to_registers
- import pymodbus.version -> from pymodbus import __version__, __version_full__
- pymodbus.pymodbus_apply_logging_config(log_file_name="pymodbus.log") to enable file pymodbus_apply_logging_config
- pymodbus.pymodbus_apply_logging_config have default DEBUG, it not called root settings will be used.
- pymodbus/interfaces/IModbusDecoder removed.
- pymodbus/interfaces/IModbusFramer removed.
- pymodbus/interfaces/IModbusSlaveContext -> pymodbus/datastore/ModbusBaseSlaveContext.
- StartAsync<type>Server, removed defer_start argument, return is None.
  instead of using defer_start instantiate the Modbus<type>Server directly.
- `ReturnSlaveNoReponseCountResponse` has been corrected to
  `ReturnSlaveNoResponseCountResponse`
- Option `--modbus-config` for REPL server renamed to `--modbus-config-path`
- client.protocol.<something> --> client.<something>
- client.factory.<something> --> client.<something>

-------------
Version 3.1.0
-------------
- Added --host to client_* examples, to allow easier use.
- unit= in client calls are no longer converted to slave=, but raises a runtime exception.
- Added missing client calls (all standard request are not available as methods).
- client.mask_write_register() changed parameters.
- server classes no longer accept reuse_port= (the socket do not accept it)

---------------------
Version 3.0.1 / 3.0.2
---------------------

No changes.

-------------
Version 3.0.0
-------------

Base
