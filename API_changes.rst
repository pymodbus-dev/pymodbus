API changes
===========
Versions (X.Y.Z) where Z > 0 e.g. 3.0.1 do NOT have API changes!

API changes 3.8.0
-----------------




API changes 3.7.0
-----------------
- default slave changed to 1 from 0 (which is broadcast).
- broadcast_enable, retry_on_empty, no_resend_on_retry parameters removed.
- class method generate_ssl() added to TLS client (sync/async).
- removed certfile, keyfile, password from TLS client, please use generate_ssl()
- on_reconnect_callback() removed from clients (sync/async).
- on_connect_callback(true/false) added to async clients.
- binary framer no longer supported
- Framer.<type> renamed to FramerType.<type>
- PDU classes moved to pymodbus/pdu
- Simulator config custom actions kwargs -> parameters
- Non defined parameters (kwargs) no longer valid
- Drop support for Python 3.8 (its no longer tested, but will probably work)


API changes 3.6.0
-----------------
- framer= is an enum: pymodbus.Framer, but still accept a framer class


API changes 3.5.0
-----------------
- Remove handler parameter from ModbusUdpServer
- Remove loop parameter from ModbusSerialServer
- Remove handler and allow_reuse_port from repl default config
- Static classes from the :code:`constants` module are now inheriting from :code:`enum.Enum` and using `UPPER_CASE` naming scheme, this affects:
  - :code:`MoreData`
  - :code:`DeviceInformation`
  - :code:`ModbusPlusOperation`
  - :code:`Endian`
  - :code:`ModbusStatus`
- Async clients now accepts `no_resend_on_retry=True`, to not resend the request when retrying.
- ModbusSerialServer now accepts request_tracer=.


API changes 3.4.0
-----------------
- Modbus<x>Client .connect() returns True/False (connected or not)
- Modbue<x>Server handler=, allow_reuse_addr=, backlog= are no longer accepted
- ModbusTcpClient / AsyncModbusTcpClient no longer support unix path
- StartAsyncUnixServer / ModbusUnixServer removed (never worked on Windows)
- ModbusTlsServer reqclicert= is no longer accepted
- ModbusSerialServer auto_connect= is no longer accepted
- ModbusSimulatorServer.serve_forever(only_start=False) added to allow return


API changes 3.3.0
-----------------
- ModbusTcpDiagClient is removed due to lack of support
- Clients have an optional parameter: on_reconnect_callback, Function that will be called just before a reconnection attempt.
- general parameter unit= -> slave=
- move SqlSlaveContext, RedisSlaveContext to examples/contrib (due to lack of maintenance)
- :code:`BinaryPayloadBuilder.to_string` was renamed to :code:`BinaryPayloadBuilder.encode`
- on_reconnect_callback for async clients works slightly different
- utilities/unpack_bitstring now expects an argument named `data` not `string`


API changes 3.2.0
-----------------
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


API changes 3.1.0
-----------------
- Added --host to client_* examples, to allow easier use.
- unit= in client calls are no longer converted to slave=, but raises a runtime exception.
- Added missing client calls (all standard request are not available as methods).
- client.mask_write_register() changed parameters.
- server classes no longer accept reuse_port= (the socket do not accept it)


API changes 3.0.0
-----------------
Base for recording changes.
