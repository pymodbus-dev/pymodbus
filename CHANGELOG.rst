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
**NOTE: Supports python 3.7, async client is now moved to pymodbus/client/asychronous**


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
* Signal handlers on Asyncronous servers are now handled based on current thread
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
* Fix never ending transaction case when response is recieved without header and CRC
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
