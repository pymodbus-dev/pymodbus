API changes
===========
Versions (X.Y.Z) where Z > 0 e.g. 3.0.1 do NOT have API changes!

API changes 3.11.0
------------------
- Revert wrong byte handling in v3.10.0
  bit handling order is LSB-> MSB for each byte
  REMARK: word are ordered depending on big/little endian
  readCoils and other bit functions now return bit in logical order (NOT byte order)

  Example:
  Hex bytes: 0x00 0x01
  delivers False * 8 True False * 7

  Hex bytes: 0x01 0x03
  delivers True False * 7 True True False * 6

API changes 3.10.0
------------------
- ModbusSlaveContext replaced by ModbusDeviceContext
- payload removed (replaced by "convert_to/from_registers")
- slave=, slaves= replaced by device_id=, device_ids=
- slave request names changed to device
- bit handling order is LSB (last byte) -> MSB (first byte)
  readCoils and other bit functions now return bit in logical order (NOT byte order)

  Older versions had LSB -> MSB pr byte
  V3.10 have LSB -> MSB across bytes.

  Example:
  Hex bytes: 0x00 0x01
  Older versions would deliver False * 8 True False * 7
  V3.10 deliver True False * 15

  Hex bytes: 0x01 0x03
  Older versions would deliver True False * 7 True True False * 6
  V3.10 deliver True True False * 6 True False * 7

API changes 3.9.0
-----------------
- Python 3.9 is reaching end of life, and no longer supported.
  Depending on the usage the code might still work
- Start*Server, custom_functions -> custom_pdu (handled by Modbus<x>Server)
- Bit handling (e.g. read_coils) was not handling the bits in the correct order

API changes 3.8.0
-----------------
- ModbusSlaveContext, removed zero_mode parameter.
- Removed skip_encode parameter.
- renamed ModbusExceptions enums to legal constants.
- enforced client keyword only parameters (positional not allowed).
- added trace_packet/pdu/connect to client/server.
- removed on_connect_callback from client.
- removed response_manipulator, request_tracer from server.

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
