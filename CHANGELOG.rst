version 3.1.3
----------------------------------------------------------
* Solve log problem in payload.
* Fix register type check for size bigger than 3 registers (6 bytes) (#1323)
* Re-add SQL tests. (#1329)
* Central logging. (#1324)
* Skip sqlAlchemy test. (#1325)
* Solve 1319 (#1320)

Thanks to:
  duc996,
  jan iversen

version 3.1.2
----------------------------------------------------------
* Update README.rst
* Correct README link. (#1316)
* More direct readme links for REPL (#1314)
* Add classifier for 3.11 (#1312)
* Update README.rst (#1313)
* Delete ModbusCommonBlock.png (#1311)
* Add modbus standard to README. (#1308)
* fix no auto reconnect after close/connect in TCPclient (#1298)
* Update examples.rst (#1307)
* var name clarification (#1304)
* Bump external libraries. (#1302)
* Reorganize documentation to make it easier accessible (#1299)
* Simulator documentation (first version). (#1296)
* Updated datastore Simulator. (#1255)
* Update links to pydmodbus-dev (#1291)
* Change riptideio to pymodbus-dev. (#1292)
* #1258 Avoid showing unit as a seperate command line argument (#1288)
* Solve docker cache problem. (#1287)

Thanks to:

  Alex,
  Alexandre CUER,
  dhoomakethu,
  jan iversen,
  peufeu2

version 3.1.1
----------------------------------------------------------
* add missing server.start() (#1282)
* small performance improvement on debug log (#1279)
* Fix Unix sockets parsing (#1281)
* client: Allow unix domain socket. (#1274)
* transfer timeout to protocol object. (#1275)
* Add ModbusUnixServer / StartAsyncUnixServer. (#1273)
* Added return in AsyncModbusSerialClient.connect (#1271)
* add connect() to the very first example (#1270)
* Solve docker problem. (#1268)
* Test stop of server task. (#1256)

Thanks to:

  Alex,
  Alexandre CUER,
  Dries,
  jan iversen,
  peufeu2


version 3.1.0
----------------------------------------------------------
* Add xdist pr default. (#1253)
* Create docker-publish.yml (#1250)
* Parallelize pytest with pytest-xdist (#1247)
* Support Python3.11 (#1246)
* Fix reconnectDelay to be within (100ms, 5min) (#1244)
* Fix typos in comments (#1233)
* WEB simulator, first version. (#1226)
* Clean async serial problem. (#1235)
* terminate when using 'randomize' and 'change_rate' at the same time (#1231)
* Used tooled python and OS (#1232)
* add 'change_rate' randomization option (#1229)
* add check_ci.sh (#1225)
* Simplify CI and use cache. (#1217)
* Solve issue 1210, update simulator (#1211)
* Add missing client calls in mixin.py. (#1206)
* Advanced simulator with cross memory. (#1195)
* AsyncModbusTcp/UdpClient honors delay_ms == 0 (#1203) (#1205)
* Fix #1188 and some pylint issues (#1189)
* Serial receive incomplete bytes.issue #1183 (#1185)
* Handle echo (#1186)
* Add updating server example. (#1176)

Thanks to:

  Alex,
  banana-sun,
  Chris Hung,
  dhoomakethu,
  jan iversen,
  Matthias Straka,
  Pavel Kostromitinov,

version 3.0.2
----------------------------------------------------------
* Add pygments as requirement for repl
* Update datastore remote to handle write requests (#1166)
* Allow multiple servers. (#1164)
* Fix typo. (#1162)
* Transfer parms. to connected client. (#1161)
* Repl enhancements 2 (#1141)
* Server simulator with datastore with json data. (#1157)
* Avoid unwanted reconnects (#1154)
* Do not initialize framer twice. (#1153)
* Allow timeout as float. (#1152)
* Improve Docker Support (#1145)
* Fix unreachable code in AsyncModbusTcpClient (#1151)
* Fix type hints for port and timeout (#1147)
* Start/stop multiple servers. (#1138)
* Server/asyncio.py correct logging when disconnecting the socket (#1135)
* Add Docker and container registry support  (#1132)
* Removes undue reported error when forwarding (#1134)
* Obey timeout parameter on connection (#1131)
* Readme typos (#1129)
* Clean noqa directive. (#1125)
* Add isort and activate CI fail for black/isort. (#1124)
* Update examples. (#1117)
* Move logging configuration behind function call (#1120)
* serial2TCP forwarding example (#1116)
* Make serial import dynamic. (#1114)
* Bugfix ModbusSerialServer setup so handler is called correctly. (#1113)
* Clean configurations. (#1111)

Thanks to:

  Alex,
  Alexandre CUER,
  Blaise Thompson,
  dhoomakethu,
  Gao Fang,
  jan Iversen,
  Joe Burmeister,
  Sebastian Machuca,
  Thijs W,
  WouterTuinstra

version 3.0.1
----------------------------------------------------------
* Faulty release!

version 3.0.0
----------------------------------------------------------
* Solve multiple incomming frames. (#1107)
* Up coverage, tests are 100%. (#1098)
* Prepare for rc1. (#1097)
* Prepare 3.0.0dev5 (#1095)
* Adapt serial tests. (#1094)
* Allow windows. (#1093)

version 3.0.0dev5
----------------------------------------------------------
* Remove server sync code and combine with async code. (#1092)
* Solve test of tls by adding certificates and remove bugs (#1080)
* Simplify server implementation. (#1071)
* Do not filter using unit id in the received response (#1076)
* Hex values for repl arguments (#1075)
* All parameters in class parameter. (#1070)
* Add len parameter to decode_bits. (#1062)
* New combined test for all types of clients. (#1061)
* Dev mixin client (#1056)
* Add/update client documentation, including docstrings etc. (#1055)
* Add unit to arguments (#1041)
* Add timeout to all pytest. (#1037)
* Simplify client parent classes. (#1018)
* Clean copyright statements, to ensure we follow FOSS rules. (#1014)
* Rectify sync/async client parameters. (#1013)
* Clean client directory structure for async. (#1010)
* Remove async_io, simplify AsyncModbus<x>Client. (#1009)
* remove init_<something>_client(). (#1008)
* Remove async factory. (#1001)
* Remove loop parameter from client/server (#999)
* add example async client. (#997)
* Change async ModbusSerialClient to framer= from method=. (#994)
* Add forwarder example with multiple slaves. (#992)
* Remove async get_factory. (#990)
* Remove unused ModbusAccessControl. (#989)
* Solve problem with remote datastore. (#988)
* Remove unused schedulers. (#976)
* Remove twisted (#972)
* Remove/Update tornado/twister tests. (#971)
* remove easy_install and ez_setup (#964)
* Fix mask write register (#961)
* Activate pytest-asyncio. (#949)
* Changed default framer for serial to be ModbusRtuFramer. (#948)
* Remove tornado. (#935)
* Pylint, check method parameter documentation. (#909)
* Add get_response_pdu_size to mask read/write. (#922)
* Minimum python version is 3.8. (#921)
* Ensure make doc fails on warnings and/or errors. (#920)
* Remove central makefile. (#916)
* Re-organize examples (#914)
* Documentation cleanup and clarification (#689)
* Update doc for repl. (#910)
* Include package and tests in coverage measurement (#912)
* Use response byte length if available (#880)
* better fix for rtu incomplete frames (#511)
* Remove twisted/tornado from doc. (#904)
* Update classifiers for pypi. (#907)

version 3.0.0dev4
----------------------------------------------------------
* Documentation updates
* PEP8 compatibale code
* More tooling and CI updates

version 3.0.0dev3
----------------------------------------------------------
* Remove python2 compatibility code (#564)
* Remove Python2 checks and Python2 code snippets
* Misc co-routines related fixes
* Fix CI for python3 and remove PyPI from CI

version 3.0.0dev2
----------------------------------------------------------
* Fix mask_write_register call. (#685)
* Add support for byte strings in the device information fields (#693)
* Catch socket going away. (#722)
* Misc typo errors (#718)

version 3.0.0dev1
----------------------------------------------------------
* Support python3.10
* Implement asyncio ModbusSerialServer
* ModbusTLS updates (tls handshake, default framer)
* Support broadcast messages with asyncio client
* Fix for lazy loading serial module with asyncio clients.
* Updated examples and tests

version 3.0.0dev0
----------------------------------------------------------
* Support python3.7 and above
* Support creating asyncio clients from with in coroutines.

version 2.5.3
----------------------------------------------------------
* Fix retries on tcp client failing randomly.
* Fix Asyncio client timeout arg not being used.
* Treat exception codes as valid responses
* Fix examples (modbus_payload)
* Add missing identity argument to async ModbusSerialServer

version 2.5.2
----------------------------------------------------------
* Add kwarg `reset_socket` to control closing of the socket on read failures (set to `True` by default).
* Add `--reset-socket/--no-reset-socket` to REPL client.

version 2.5.1
----------------------------------------------------------
* Bug fix TCP Repl server.
* Support multiple UID's with REPL server.
* Support serial for URL (sync serial client)
* Bug fix/enhancements, close socket connections only on empty or invalid response

version 2.5.0
----------------------------------------------------------
* Support response types `stray` and `empty` in repl server.
* Minor updates in asyncio server.
* Update reactive server to send stray response of given length.
* Transaction manager updates on retries for empty and invalid packets.
* Test fixes for asyncio client and transaction manager.
* Fix sync client and processing of incomplete frames with rtu framers
* Support synchronous diagnostic client (TCP)
* Server updates (REPL and async)
* Handle Memory leak in sync servers due to socketserver memory leak

version 2.5.0rc3
----------------------------------------------------------
* Minor fix in documentations
* Travis fix for Mac OSX
* Disable unnecessary deprecation warning while using async clients.
* Use Github actions for builds in favor of travis.


version 2.5.0rc2
----------------------------------------------------------
* Documentation updates
* Disable `strict` mode by default.
* Fix `ReportSlaveIdRequest` request
* Sparse datablock initialization updates.

version 2.5.0rc1
----------------------------------------------------------
* Support REPL for modbus server (only python3 and asyncio)
* Fix REPL client for write requests
* Fix examples
  * Asyncio server
  * Asynchronous server (with custom datablock)
  * Fix version info for servers
* Fix and enhancements to Tornado clients (seril and tcp)
* Fix and enhancements to Asyncio client and server
* Update Install instructions
* Synchronous client retry on empty and error enhancments
* Add new modbus state `RETRYING`
* Support runtime response manipulations for Servers
* Bug fixes with logging module in servers
* Asyncio modbus serial server support

Version 2.4.0
----------------------------------------------------------
* Support async moduls tls server/client
* Add local echo option
* Add exponential backoffs on retries.
* REPL - Support broadcasts.
* Fix framers using wrong unit address.
* Update documentation for serial_forwarder example
* Fix error with rtu client for `local_echo`
* Fix asyncio client not working with already running loop
* Fix passing serial arguments to async clients
* Support timeouts to break out of responspe await when server goes offline
* Misc updates and bugfixes.

Version 2.3.0
-----------------------------------------------------------
* Support Modbus TLS (client / server)
* Distribute license with source
* BinaryPayloadDecoder/Encoder now supports float16 on python3.6 and above
* Fix asyncio UDP client/server
* Minor cosmetic updates

Version 2.3.0rc1
-----------------------------------------------------------
* Asyncio Server implementation (Python 3.7 and above only)
* Bug fix for DiagnosticStatusResponse when odd sized response is received
* Remove Pycrypto from dependencies and include cryptodome instead
* Remove `SIX` requirement pinned to exact version.
* Minor bug-fixes in documentations.


Version 2.2.0
-----------------------------------------------------------
**NOTE: Supports python 3.7, async client is now moved to pymodbus/client/asynchronous**


.. code-block:: python

    from pymodbus.client.asynchronous import ModbusTcpClient


* Support Python 3.7
* Fix to task cancellations and CRC errors for async serial clients.
* Fix passing serial settings to asynchronous serial server.
* Fix `AttributeError` when setting `interCharTimeout` for serial clients.
* Provide an option to disable inter char timeouts with Modbus RTU.
* Add support to register custom requests in clients and server instances.
* Fix read timeout calculation in ModbusTCP.
* Fix SQLDbcontext always returning InvalidAddress error.
* Fix SQLDbcontext update failure
* Fix Binary payload example for endianess.
* Fix BinaryPayloadDecoder.to_coils and BinaryPayloadBuilder.fromCoils methods.
* Fix tornado async serial client `TypeError` while processing incoming packet.
* Fix erroneous CRC handling in Modbus RTU framer.
* Support broadcasting in Modbus Client and Servers (sync).
* Fix asyncio examples.
* Improved logging in Modbus Server .
* ReportSlaveIdRequest would fetch information from Device identity instead of hardcoded `Pymodbus`.
* Fix regression introduced in 2.2.0rc2 (Modbus sync client transaction failing)
* Minor update in factory.py, now server logs prints received request instead of only function code

.. code-block:: bash

   # Now
   # DEBUG:pymodbus.factory:Factory Request[ReadInputRegistersRequest: 4]
   # Before
   # DEBUG:pymodbus.factory:Factory Request[4]



Version 2.1.0
-----------------------------------------------------------
* Fix Issues with Serial client where in partial data was read when the response size is unknown.
* Fix Infinite sleep loop in RTU Framer.
* Add pygments as extra requirement for repl.
* Add support to modify modbus client attributes via repl.
* Update modbus repl documentation.
* More verbose logs for repl.

Version 2.0.1
-----------------------------------------------------------
* Fix unicode decoder error with BinaryPayloadDecoder in some platforms
* Avoid unnecessary import of deprecated modules with dependencies on twisted

Version 2.0.0
-----------------------------------------------------------
**Note This is a Major release and might affect your existing Async client implementation. Refer examples on how to use the latest async clients.**

* Async client implementation based on Tornado, Twisted and asyncio with backward compatibility support for twisted client.
* Allow reusing existing[running] asyncio loop when creating async client based on asyncio.
* Allow reusing address for Modbus TCP sync server.
* Add support to install tornado as extra requirement while installing pymodbus.
* Support Pymodbus REPL
* Add support to python 3.7.
* Bug fix and enhancements in examples.


Version 2.0.0rc1
-----------------------------------------------------------
**Note This is a Major release and might affect your existing Async client implementation. Refer examples on how to use the latest async clients.**

* Async client implementation based on Tornado, Twisted and asyncio


Version 1.5.2
------------------------------------------------------------
* Fix serial client `is_socket_open` method

Version 1.5.1
------------------------------------------------------------
* Fix device information selectors
* Fixed behaviour of the MEI device information command as a server when an invalid object_id is provided by an external client.
* Add support for repeated MEI device information Object IDs (client/server)
* Added support for encoding device information when it requires more than one PDU to pack.
* Added REPR statements for all syncchronous clients
* Added `isError` method to exceptions, Any response received can be tested for success before proceeding.

.. code-block:: python

    res = client.read_holding_registers(...)
    if not res.isError():

        # proceed

    else:
        # handle error or raise

    """

* Add examples for MEI read device information request

Version 1.5.0
------------------------------------------------------------
* Improve transaction speeds for sync clients (RTU/ASCII), now retry on empty happens only when retry_on_empty kwarg is passed to client during intialization

`client = Client(..., retry_on_empty=True)`

* Fix tcp servers (sync/async) not processing requests with transaction id > 255
* Introduce new api to check if the received response is an error or not (response.isError())
* Move timing logic to framers so that irrespective of client, correct timing logics are followed.
* Move framers from transaction.py to respective modules
* Fix modbus payload builder and decoder
* Async servers can now have an option to defer `reactor.run()` when using `Start<Tcp/Serial/Udo>Server(...,defer_reactor_run=True)`
* Fix UDP client issue while handling MEI messages (ReadDeviceInformationRequest)
* Add expected response lengths for WriteMultipleCoilRequest and WriteMultipleRegisterRequest
* Fix _rtu_byte_count_pos for GetCommEventLogResponse
* Add support for repeated MEI device information Object IDs
* Fix struct errors while decoding stray response
* Modbus read retries works only when empty/no message is received
* Change test runner from nosetest to pytest
* Fix Misc examples

Version 1.4.0
------------------------------------------------------------
* Bug fix Modbus TCP client reading incomplete data
* Check for slave unit id before processing the request for serial clients
* Bug fix serial servers with Modbus Binary Framer
* Bug fix header size for ModbusBinaryFramer
* Bug fix payload decoder with endian Little
* Payload builder and decoder can now deal with the wordorder as well of 32/64 bit data.
* Support Database slave contexts (SqlStore and RedisStore)
* Custom handlers could be passed to Modbus TCP servers
* Asynchronous Server could now be stopped when running on a seperate thread (StopServer)
* Signal handlers on Asynchronous servers are now handled based on current thread
* Registers in Database datastore could now be read from remote clients
* Fix examples in contrib (message_parser.py/message_generator.py/remote_server_context)
* Add new example for SqlStore and RedisStore (db store slave context)
* Fix minor comaptibility issues with utilities.
* Update test requirements
* Update/Add new unit tests
* Move twisted requirements to extra so that it is not installed by default on pymodbus installtion

Version 1.3.2
------------------------------------------------------------
* ModbusSerialServer could now be stopped when running on a seperate thread.
* Fix issue with server and client where in the frame buffer had values from previous unsuccesful transaction
* Fix response length calculation for ModbusASCII protocol
* Fix response length calculation ReportSlaveIdResponse, DiagnosticStatusResponse
* Fix never ending transaction case when response is received without header and CRC
* Fix tests

Version 1.3.1
------------------------------------------------------------
* Recall socket recv until get a complete response
* Register_write_message.py: Observe skip_encode option when encoding a single register request
* Fix wrong expected response length for coils and discrete inputs
* Fix decode errors with ReadDeviceInformationRequest and  ReportSlaveIdRequest on Python3
* Move MaskWriteRegisterRequest/MaskWriteRegisterResponse  to register_write_message.py from file_message.py
* Python3 compatible examples [WIP]
* Misc updates with examples

Version 1.3.0.rc2
------------------------------------------------------------
* Fix encoding problem for ReadDeviceInformationRequest method on python3
* Fix problem with the usage of ord in python3 while cleaning up receive buffer
* Fix struct unpack errors with BinaryPayloadDecoder on python3 - string vs bytestring error
* Calculate expected response size for ReadWriteMultipleRegistersRequest
* Enhancement for ModbusTcpClient, ModbusTcpClient can now accept connection timeout as one of the parameter
* Misc updates

Version 1.3.0.rc1
------------------------------------------------------------
* Timing improvements over MODBUS Serial interface
* Modbus RTU use 3.5 char silence before and after transactions
* Bug fix on FifoTransactionManager , flush stray data before transaction
* Update repository information
* Added ability to ignore missing slaves
* Added ability to revert to ZeroMode
* Passed a number of extra options through the stack
* Fixed documenation and added a number of examples

Version 1.2.0
------------------------------------------------------------

* Reworking the transaction managers to be more explicit and
  to handle modbus RTU over TCP.
* Adding examples for a number of unique requested use cases
* Allow RTU framers to fail fast instead of staying at fault
* Working on datastore saving and loading

Version 1.1.0
------------------------------------------------------------

* Fixing memory leak in clients and servers (removed __del__)
* Adding the ability to override the client framers
* Working on web page api and GUI
* Moving examples and extra code to contrib sections
* Adding more documentation

Version 1.0.0
------------------------------------------------------------

* Adding support for payload builders to form complex encoding
  and decoding of messages.
* Adding BCD and binary payload builders
* Adding support for pydev
* Cleaning up the build tools
* Adding a message encoding generator for testing.
* Now passing kwargs to base of PDU so arguments can be used
  correctly at all levels of the protocol.
* A number of bug fixes (see bug tracker and commit messages)

Version 0.9.0
------------------------------------------------------------

Please view the git commit log
