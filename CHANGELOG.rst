Changelog
=========
All these version would not be possible without a lot of work from volunteers!

We, the maintainers, are greatful for each pull requests small or big, that
helps make pymodbus a better product.

:ref:`Authors`: contains a complete list of volunteers have contributed to each major version.

Version 3.11.3
--------------
* Coverage 100% (using no cover, when needed). (#2783)
* Create pypi alias for home-assistant. (#2782)
* Bump utilities in pyproject.toml. (#2780)
* Fix pymodbus.simulator. (#2773)

Version 3.11.2
--------------
* Clarify documentation on reconnect_delay (#2769)
* Solve CI complaints. (#2766)
* Coverage not allowed below 99.5%. (#2765)
* Test coverage global 100%. (#2764)
* Test coverage simulator 100%. (#2763)
* Test coverage server 100%. (#2760)
* Fix python3.14 deprecation. (#2759)
* Test coverage datastore 100%. (#2757)
* Context test failed due to function code overwritten. (#2758)
* Test coverage transaction 100%. (#2756)
* Test coverage pdu 100%. (#2755)
* Framer test 100%. (#2754)
* llow sub_function_code is custom PDU. (#2753)
* Generate pdu table direct. (#2752)
* Clean pdu lookup in simulator. (#2751)
* diag sub_function_code is 2 bytes. (#2750)
* Requesthandler ignore missing devices logging (#2749)
* Simplify pdu lookup. (#2745)
* Missing coma in string representation of ModbusPDU (#2748)
* Correct "install uv". (#2744)
* Suppress aiohttp missing. (#2743)
* Remove garbage bytes in serial comm. (#2741)
* Test now included python 3.14.
* Stricter types with pyright (#2731)

Version 3.11.1
--------------
* Auto debug in case of an error. (#2738)
* Remove duplicate log lines. (#2736)
* Remove unused callback in ServerRequestHandler (#2737)
* test on Python 3.14 (#2735)
* Validate address in all datastores. (#2733)
* Use asyncio.Event to deterministically ensure simulator start (#2734)
* Ignore lockfile (#2730)
* Link api_changes/changelog to README.
* Add note about semver.org.
* Datastore, add typing to set/get. (#2729)
* Move exception codes to constants. (#2728)
* Move ExceptionResponse to proper file. (#2727)
* make base frame signature match subclasses (#2726)
* Switch from venv+pip to uv (#2723)
* Cleanup CI configuration (#2724)
* Simplify code flow for broadcast requests (#2720)
* Fix serial_forwarder.py from examples/contrib (#2715)
* Remove discord. (#2714)

Version 3.11.0
--------------
 * Correct bit handling (each byte is LSB->MSB). (#2707)
 * read_input_registers docstring change count to regs (#2704)
 * Add dev_id/tid check in clients (#2711)

Version 3.10.0
--------------
* Raise runtimeerror if listen() fails. (#2697)
* Correct values parameter in setValues. (#2696)
* Correct return from getValues. (#2695)
* Add request fc to exceptionResponse. (#2694)
* DummyProtocol is not async (#2686)
* Handle "little" for multiple values in to_registers (#2678)
* Remove unused const. (#2676)
* Add retries to ModbusPDU class (#2672)
* Don't invoke `trace_connect` callback twice (#2670)
* ensure unpacking of proper length during decoding (#2664) (#2665)
* README clean-up (#2659)
* Bump coverage to 95,5% (#2658)
* Simplify response rejection. (#2657)
* Bump coverage to 93%. (#2656)
* Solve ModbusDeviceContext bug. (#2653)
* Bit handling LSB -> MSB across bytes. (#2634)
* Change slave to device_id and slave= to device_id=. (#2600)
* Remove payload. (#2524)

Version 3.9.2
-------------
* Reactivate simulator validate. (#2643)
* Don't bool-test explicit datastores (#2638)
* Test and hard delayed response test. (#2636)
* Update simulator doc. (#2635)
* SimData update
* Officially working towards 4.0.0

Version 3.9.1
-------------
* Correct byte order in bits. (#2631)

Version 3.9.0
-------------
* Correct bit handling internally and in API. (#2627)
* default argument  ModbusSequentialDataBlock (#2622)
* Fix exception error message for decoding response (#2618)
* Expose exception_code to API. (#2615)
* Simplify ruff config (#2611)
* Documentation dont fixed. (#2605)
* sum() can operate on an Iterator directly (#2610)
* SimData update. (#2601)
* Start<x>Server custom_functions -> custom_pdu.
* Update pyproject.toml to remove python 3.9.
* Remove validate() from datastores. (#2595)
* Python 3.9 is EOL, not supported actively. (#2596)
* correct handle_local_echo for sync client. (#2593)
* devcontainer, automatic install. (#2583)
* Don't set_result on completed futures. (#2582)
* Flush recv_buffer before each transaction write. (#2581)
* Add missing trace. (#2578)
* Update github actions. (#2579)

Version 3.8.6
-------------
* Allow id=0 and check if response.id == request.id. (#2572)

Version 3.8.5
-------------
* New simulator is WIP, not to be used. (#2568)
* dev_id=0 no response expected (returns ExceptionResponse(0xff)). (#2567)
* New simulator datastore. (#2535)

Version 3.8.4
-------------
* Parameterize string encoding in convert_to_registers and convert_from_registers (#2558)
* Fix client modbus function calls in remote by adding count as keyword argument (#2563)
* Fix exception text in ModbusPDU.validateAddress (#2551)
* Typo arround `no_response_expected` (#2550)
* Trace new connection in server. (#2549)
* Add trace to server.
* Update misleading DATATYPE text. (#2547)
* Fix pylint.
* Clarify server usage.
* Solve instable transaction testing. (#2538)

Version 3.8.3
-------------
* Remove deprecate from payload. (#2532)
* Add background parameter to servers. (#2529)
* Split async_io.py and simplify server start/stop. (#2528)
* Update custom_msg example to include server. (#2527)
* Move repl doc to repl repo. (#2522)
* Add API to set max until disconnect. (#2521)

Version 3.8.2
-------------
* Asyncio future removed from sync client. (#2514)

Version 3.8.1
-------------
* Convert endianness (#2506)
* Fix sync serial client, loop. (#2510)
* Correct future. (#2507)
* Correct #2501 (#2504)
* Raise exception on no response in async client. (#2502)
* re-instatiate Future on reconnect (#2501)
* Remove all trailing zeroes during string decoding (#2493)
* Fix too many sync client log messages. (#2491)

Version 3.8.0
-------------
* slave_id -> dev_id (internally). (#2486)
* Pin python 3.13.0 and update ruff. (#2487)
* Add documentation link to README. (#2483)
* Add datatype bits to convert_to/from_registers. (#2480)
* Add trace API to server. (#2479)
* Add trace API for client. (#2478)
* Integrate TransactionManager in server. (#2475)
* Rename test/sub. (#2473)
* Check server closes file descriptors. (#2472)
* Update http_server.py (#2471)
* Restrict write_registers etc to list[int]. (#2469)
* Write_registers/pdu typing again. (#2468)
* Remove ModbusExceptions enum. (#2467)
* Add special ssl socket handling of "no data". (#2466)
* Add tip that values= will be modified to list[int]. (#2465)
* client 100% test coverage (#2396)
* Extend TransactionManager to handle sync. (#2457)
* Add convert_from to simple examples. (#2458)
* New async transaction manager. (#2453)
* Deprecate BinaryPayloadDecoder / BinaryPayloadBuilder. (#2456)
* Correct close for server transport. (#2455)
* RTU frame problem, when received split. (#2452)
* pdu, 100% coverage. (#2450)
* Refactor PDU, add strong typing to base classes. (#2438)
* Enforce keyword only parameters. (#2448)
* Fix read_device_information with sync client. (#2441)
* Simplify syncTransactionManager. (#2443)
* Import examples direct. (#2442)
* rename ModbusExceptions enums to legal constants. (#2436)
* Add typing to examples. (#2435)
* Refactor PDU diag. (#2421)
* Fix client lock, Parallel API calls are not permitted. (#2434)
* Ensure accept_no_response_limit > retries. (#2433)
* Check client and frametype. (#2426)
* Add MDAP to TLS frame. (#2425)
* Clean/Finalize testing for bit functions. (#2420)
* Simplify pdu bit, remove skip_encode. (#2417)
* remove zero_mode parameter. (#2354)
* Prepare refactor messages. (#2416)
* Fixed handle local echo in serialserver (#2415)
* Correct minor framer/pdu errors. (#2407)
* Rtu decode frames without byte count. (#2412)
* Improve type of parameter values of write_registers (#2411)
* PDU lookupClass work with sub function code. (#2410)
* Correct wait_next_api link in README. (#2406)

Version 3.7.4
-------------
* Clean PDU init. (#2399)
* Wrong close, when transaction do not match. (#2401)
* Remove unmaintained (not working) example contributions. (#2400)
* All pdu (incl. function code) tests to pdu directory. (#2397)
* Add `no_response_expected` argument to requests (#2385)
* Resubmit: Don't close/reopen tcp connection on single modbus message timeout (#2350)
* 100% test coverage for PDU. (#2394)
* Type DecodePDU. (#2392)
* Update to use DecodePDU. (#2391)
* Client/Server decoder renamed and moved to pdu. (#2390)
* Move client/server decoder to pdu. (#2388)
* Introducing PyModbus Guru on Gurubase.io (#2387)
* Remove IllegalFunctionRequest. (#2384)
* remove ModbusResponse. (#2383)
* Add typing to pdu base classes. (#2380)
* Updated roadmap.
* remove databuffer from framer. (#2379)
* Improve retries for sync client. (#2377)
* Move process test to framer tests (#2376)
* Framer do not check ids (#2375)
* Remove callback from framer. (#2374)
* Auto fill device ids for clients. (#2372)
* Reenable multidrop tests. (#2370)
* write_register/s accept bytes or int. (#2369)
* roadmap corrections.
* Added roadmap (not written in stone). (#2367)
* Update README to show python 3.13.
* Test on Python 3.13 (#2366)
* Use @abstractmethod (#2365)
* Corrected smaller documentation bugs. (#2364)
* README as landing page in readthedocs. (#2363)

Version 3.7.3
-------------
* 100% test coverage of framers (#2359)
* Framer, final touches. (#2360)
* Readme file renamed (#2357)
* Remove old framers (#2358)
* frameProcessIncomingPacket removed (#2355)
* Cleanup framers (reduce old_framers) (#2342)
* Run CI on PR targeted at wait_next_api.
* Sync client, allow unknown recv msg size. (#2353)
* integrate old rtu framer in new framer (#2344)
* Update README.rst (#2351)
* Client.close should not allow reconnect= (#2347)
* Remove async client.idle_time(). (#2349)
* Client doc, add common methods (base). (#2348)
* Reset receive buffer with send(). (#2343)
* Remove unused protocol_id from pdu (#2340)
* CI run on demand on non-protected branches. (#2339)
* Server listener and client connections have is_server set. (#2338)
* Reopen listener in server if disconnected. (#2337)
* Regroup test. (#2335)
* Improve docs around sync clients and reconnection (#2321)
* transport 100% test coverage (again) (#2333)
* Update actions to new node.js. (#2332)
* Bump 3rd party (#2331)
* Documentation on_connect_callback (#2324)
* Fixes the unexpected implementation of the ModbusSerialClient.connected property (#2327)
* Forward error responses instead of timing out. (#2329)
* Add `stacklevel=2` to logging functions (#2330)
* Fix encoding & decoding of ReadFileRecordResponse (#2319)
* Improvements for example/contib/solar (#2318)
* Update solar.py (#2316)
* Remove double conversion in int (#2315)
* Complete pull request #2310 (#2312)
* fixed type hints for write_register and write_registers (#2309)
* Remove _header from framers. (#2305)

Version 3.7.2
-------------
* Correct README
* Rename branch wait3.8.0 to wait_next_API


Version 3.7.1
-------------
* Better error message, when pyserial is missing.
* Slave=0 will return first response, used to identify device address. (#2298)
* Feature/add simulator api skeleton (#2274)
* Correct max. read size for registers. (#2295)
* Ruff complains, due to upgrade. (#2296)
* Properly process 'slaves' argument (#2292)
* Update repl requirement to >= 2.0.4 (#2291)
* Fix aiohttp < 3.9.0 (#2289)
* Simplify framer test setup (#2290)
* Clean up ModbusControlBlock (#2288)
* example docstrings diag_message -> pdu.diag_message (#2286)
* Explain version schema (#2284)
* Add more testing for WriteRegisters. (#2280)
* Proof for issue 2273. (#2277)
* Update simulator tests. (#2276)


Version 3.7.0
-------------
* Remove unneeded client parameters. (#2272)
* simulator: Fix context single parameter (#2264)
* buildPacket can be used for Request and Response (#2262)
* More descriptive decoder exceptions (#2260)
* Cleanup ReadWriteMultipleRegistersResponse and testing (#2261)
* Feature/simulator addressing (#2258)
* Framer optimization (apart from RTU). (#2146)
* Use mock.patch.object to avoid protected access errors. (#2251)
* Fix some mypy type checking errors in test_transaction.py (#2250)
* Update check for windows platform (#2247)
* Logging 100% coverage. (#2248)
* CI, Block draft PRs to use CPU minutes. (#2245, #2246)
* Remove kwargs client. (#2243, #2244, #2257)
* remove kwargs PDU messagees. (#2240)
* Remove message_generator example (not part of API). (#2239)
* Update dev dependencies (#2241)
* Fix ruff check in CI (#2242)
* Remove kwargs. (#2236, #2237)
* Simulator config, kwargs -> parameters. (#2235)
* Refactor transaction handling to better separate async and sync code. (#2232)
* Simplify some BinaryPayload pack operations (#2224)
* Fix writing to serial (rs485) on windows os. (#2191)
* Remember to remove serial writer. (#2209)
* Transaction_id for serial == 0. (#2208)
* Solve pylint error.
* Sync TLS needs time before reading frame (#2186)
* Update transaction.py (#2174)
* PDU classes --> pymodbus/pdu. (#2160)
* Speed up no data detection. (#2150)
* RTU decode hunt part. (#2138)
* Dislodge client classes from modbusProtocol. (#2137)
* Merge new message layer and old framer directory. (#2135)
* Coverage == 91%. (#2132)
* Remove binary_framer. (#2130)
* on_reconnect_callback --> on_connect_callback. (#2122)
* Remove certfile,keyfile,password from TLS client. (#2121)
* Drop support for python 3.8 (#2112)


Version 3.6.9
-------------
* Remove python 3.8 from CI
* Log comm retries. (#2220)
* Solve serial unrequested frame. (#2219)
* test convert registers with 1234.... (#2217)
* Fix writing to serial (rs485) on windows os. (#2191)
* Remember to remove serial writer. (#2209)
* Update client.rst (#2199)
* Fix usage file names (#2194)
* Show error if example is run without support files. (#2189)
* Solve pylint error.
* Describe zero_mode in ModbusSlaveContext.__init__ (#2187)
* Datastore will not return ExceptionResponse. (#2175)
* call async datastore from modbus server (#2144)
* Transaction id overrun.
* Add minimal devcontainer. (#2172)
* Sphinx: do not turn warnings into errors.
* Fix usage of AsyncModbusTcpClient in client docs page (#2169)
* Bump actions CI. (#2166)
* Request/Response: change execute to be async method (#2142)
* datastore: add async_setValues/getValues methods (#2165)
* fixed kwargs not being expanded for actions on bit registers, adjusted tests to catch this issue (#2161)
* Clean datastore setValues. (#2145)
* modbus_server: call execute in a way that those can be either coroutines or normal methods (#2139)
* Streamline message class. (#2133)
* Fix decode for wrong mdap len.
* SOCKET/TLS framer using message decode(). (#2129)
* ASCII framer using message decode() (#2128)
* Add generate_ssl() to TLS client as helper. (#2120)
* add _legacy_decoder to message rtu (#2119)


Version 3.6.8
-------------
* Allow socket exception response with wrong length


Version 3.6.7
-------------
* Add lock to async requests, correct logging and length calc. (FIX, not on dev)
* test_simulator: use unused_tcp_port fixture (#2141)
* streamline imports in Factory.py (#2140)
* Secure testing is done with pymodbus in PR. (#2136)
* Fix link to github in README (#2134)
* Wildcard exception catch from pyserial. (#2125)
* Problem with stale CI. (#2117)
* Add connection exception to list of exceptions catpured in retries (#2113)
* Move on_reconnect to client level (#2111)
* Bump github stale. (#2110)
* update package_test_tool (add 4 test scenarios) (#2107)
* Bump dependencies. (#2108)
* Cancel send if no connection. (#2103)


Version 3.6.6
-------------
* Solve transport close() as not inherited method. (#2098)
* enable `mypy --check-untyped-defs` (#2096)
* Add get_expected_response_length to transaction.
* Remove control encode in framersRemove control encode in framers. (#2095)
* Bump codeql in CI to v3. (#2093)
* Improve server types (#2092)
* Remove pointless try/except (#2091)
* Improve transport types (#2090)
* Use explicit ValueError when called with incorrect function code (#2089)
* update message tests (incorporate all old tests). (#2088)
* Improve simulator type hints (#2084)
* Cleanup dead resetFrame code (#2082)
* integrate message.encode() into framer.buildPacket. (#2062)
* Repair client close() (intern= is needed for ModbusProtocol). (#2080)
* Updated Message_Parser example (#2079)
* Fix #2069 use released repl from pypi (#2077)
* Fix field encoding of Read File Record Response (#2075)
* Improve simulator types (#2076)
* Bump actions. (#2071)


Version 3.6.5
-------------
* Update framers to ease message integration (only decode/encode) (#2064)
* Add negtive acknowledge to modbus exceptions (#2065)
* add Message Socket/TLS and amend tests. (#2061)
* Improve factory types (#2060)
* ASCII. (#2054)
* Improve datastore documentation (#2056)
* Improve types for messages (#2058)
* Improve payload types (#2057)
* Reorganize datastore inheritance (#2055)
* Added new message (framer) raw + 100%coverage. (#2053)
* message classes, first step (#1932)
* Use AbstractMethod in transport. (#2051)
* A datastore for each slave. (#2050)
* Only run coverage in ubuntu / python 3.12 (#2049)
* Replace lambda with functools.partial in transport. (#2047)
* Move self.loop in transport to init() (#2046)
* Fix decoder bug (#2045)
* Add support for server testing in package_test_tool. (#2044)
* DictTransactionManager -> ModbusTransactionManager (#2042)
* eliminate redundant server_close() (#2041)
* Remove reactive server (REPL server). (#2038)
* Improve types for client (#2032)
* Improve HTTP server type hints (#2035)
* eliminate asyncio.sleep() and replace time.sleep() with a timeout (#2034)
* Use "new" inter_byte_timeout and is_open for pyserial (#2031)
* Add more type hints to datastore (#2028)
* Add more framer tests, solve a couple of framer problems. (#2024)
* Rework slow tests (use NULL_MODEM) (#1995)
* Allow slave=0 in serial communication. (#2023)
* Client package test tool. (#2022)
* Add REPL documentation back with links to REPL repo (#2017)
* Move repl to a seperate repo (#2009)
* solve more mypy issues with client (#2013)
* solve more mypy issues with datastore (#2010)
* Remove useless. (#2011)
* streamline transport tests. (#2004)
* Improve types for REPL (#2007)
* Specify more types in base framer (#2005)
* Move htmlcov -> build/cov (#2003)
* Avoid pylint complain about lambda. (#1999)
* Improve client types (#1997)
* Fix setblocking call (#1996)
* Actívate warnings in pytest. (#1994)
* Add profile option to pytest. (#1991)
* Simplify message tests (#1990)
* Upgrade pylint and ruff (#1989)
* Add first architecture document. (#1988)
* Update CONTRIBUTING.rst.
* Return None for broadcast. (#1987)
* Make ModbusClientMixin Generic to fix type issues for sync and async (#1980)
* remove strange None default (#1984)
* Fix incorrect bytearray type hint in diagnostics query (#1983)
* Fix URL to CHANGELOG (#1979)
* move server_hostname to be local in tls client. (#1978)
* Parameter "strict" is and was only used for serial server/client. (#1975)
* Removed unused parameter close_comm_on_error. (#1974)


Version 3.6.4
-------------
* Update datastore_simulator example with client (#1967)
* Test and correct receiving more than one packet (#1965)
* Remove unused FifoTransactionManager. (#1966)
* Always set exclusive serial port access. (#1964)
* Add server/client network stub, to allow test of network packets. (#1963)
* Combine conftest to a central file (#1962)
* Call on_reconnect_callback. (#1959)
* Readd ModbusBaseClient to external API.
* Update README.rst
* minor fix for typo and consistency (#1946)
* More coverage. (#1947)
* Client coverage 100%. (#1943)
* Run coverage in CI with % check of coverage. (#1945)
* transport 100% coverage. (#1941)
* contrib example: TCP drainage simulator with two devices (#1936)
* Remove "pragma no cover". (#1935)
* transport_serial -> serialtransport. (#1933)
* Fix behavior after Exception response (#1931)
* Correct expected length for udp sync client. (#1930)

Version 3.6.3
-------------
* solve Socket_framer problem with Exception response (#1925)
* Allow socket frames to be split in multiple packets (#1923)
* Reset frame for serial connections.
* Source address None not 0.0.0.0 for IPv6
* Missing Copyright in License file
* Correct wrong url to modbus protocol spec.
* Fix serial port in TestComm.

Version 3.6.2
-------------
* Set documentation to v3.6.2.

Version 3.6.1
-------------
* Solve pypi upload error.

Version 3.6.0
-------------
* doc: Fix a code mismatch in client.rst
* Update README.
* truncated duration to milliseconds
* Update examples for current dev.
* Ignore all remaining implicit optional (#1888)
* docstring
* Remove unnecessary abort() call
* Enable RUF013 (implicit optional) (#1882)
* Support aiohttp 3.9.0b1 (#1886)
* Actually perform aiohttp runner teardown
* Pin to working aiohttp (#1884)
* Docstring typo cleanup (#1879)
* Clean client API imports. (#1819)
* Update issue template.
* Eliminiate implicit optional in reconnect_delay* (#1874)
* Split client base in sync/async version (#1878)
* Rework host/port and listener setup (#1866)
* use baudrate directly (#1872)
* Eliminate more implicit optional (#1871)
* Fix serial server args order (#1870)
* Relax test task/thread checker. (#1867)
* Make doc link references version dependent. (#1864)
* Remove pre-commit (#1860)
* Ruff reduce ignores. (#1862)
* Bump ruff to 0.1.3 and remove ruff.toml (#1861)
* More elegant noop. (#1859)
* Cache (#1829)
* Eliminate more implicit optional (#1858)
* Ignore files downloaded by pytest (#1857)
* Avoid malicious user path input (#1855)
* Add more return types to transport (#1852)
* Do not attempt to close an already-closed serial connection (#1853)
* Fix stopbits docstring typo (#1850)
* Convert type hints to PEP585 (#1846)
* Eliminate even more implicit optional (#1845)
* Eliminate more implicit optionals in client (#1844)
* Eliminate implicit optional in transport_serial (#1843)
* Make client type annotations compatible with async client usage (#1842)
* Merge pull request #1838 from pymodbus-dev/ruff
* Eliminate implicit optional in simulator (#1841)
* eliminate implicit optional for callback_disconnected (#1840)
* pre-commit run --all-files
* Update exclude paths
* Replace black with ruff
* Use other dependency groups for 'all' (#1834)
* Cleanup author/maintainer fields (#1833)
* Consistent messages if imports fail (#1831)
* Client/Server framer as enum. (#1822)
* Solve relative path in examples. (#1828)
* Eliminate implicit optional for CommParams types (#1825)
* Add 3.12 classifier (#1826)
* Bump actions/stale to 8.0.0 (#1824)
* Cleanup paths included in mypy/pylint (#1823)
* Client documentation amended and updated. (#1820)
* Import aiohttp in way pleasing mypy. (#1818)
* Update doc, remove md files. (#1814)
* Bump dependencies. (#1816)
* Solve pylint / pytest.
* fix pylint.
* Examples are without parent module.
* Wrong zip of examples.
* Serial delay (#1810)
* Add python 3.12. (#1800)
* Release errors (pyproject.toml changes). (#1811)


Version 3.5.4
-------------
* Release errors (pyproject.toml changes). (#1811)


Version 3.5.3
-------------
* Simplify transport_serial (modbus use) (#1808)
* Reduce transport_serial (#1807)
* Change to pyproject.toml. (#1805)
* fixes access to asyncio loop via loop property of SerialTransport (#1804)
* Bump aiohttp to support python 3.12. (#1802)
* README wrong links. (#1801)
* CI caching. (#1796)
* Solve pylint unhappy. (#1799)
* Clean except last 7 days. (#1798)
* Reconect_delay == 0, do not reconnect. (#1795)
* Update simulator.py method docstring (#1793)
* add type to isError. (#1781)
* Allow repr(ModbusException) to return complete information (#1779)
* Update docs. (#1777)


Version 3.5.2
-------------
* server tracer example. (#1773)
* sync connect missing. (#1772)
* simulator future problem. (#1771)


Version 3.5.1
-------------
* Always close socket on error (reset_sock). (#1767)
* Revert reset_socket change.
* add close_comm_on_error to example.
* Test long term (HomeAsistant problem). (#1765)
* Update ruff to 0.0.287 (#1764)
* Remove references to ModbusSerialServer.start (#1759) (#1762)
* Readd test to get 100% coverage.
* transport: Don't raise a RunTimeError in ModbusProtocol.error_received() (#1758)


Version 3.5.0
-------------
* Async retry (#1752)
* test_client: Fix test_client_protocol_execute() (#1751)
* Use enums for constants (#1743)
* Local Echo Broadcast with Async Clients (#1744)
* Fix #1746 . Return missing result (#1748)
* Document nullmodem. (#1739)
* Add system health check to all tests. (#1736)
* Handle partial message in ReadDeviceInformationResponse (#1738)
* Broadcast with Handle Local Echo (#1737)
* transport_emulator, part II. (#1710)
* Added file AUTHORS, to list all Volunteers. (#1734)
* Fix #1702 and #1728 (#1733)
* Clear retry count when success. (#1732)
* RFC: Reduce parameters for REPL server classes (#1714)
* retries=1, solved. (#1731)
* Impoved the example "server_updating.py" (#1720)
* pylint 3.11 (#1730)
* Correct retry loop. (#1729)
* Fix faulty not check (#1725)
* bugfix local echo handling on sync clients (#1723)
* Updated copyright in LICENSE.
* Correct README pre-commit.
* Fix custom message parsing in RTU framer (#1716)
* Request tracer (#1715)
* pymodbus.server: allow strings for "-p" paramter (#1713)
* New nullmodem and transport. (#1696)
* xdist loadscope (test is not split). (#1708)
* Add client performance example. (#1707)


Version 3.4.1
-------------
* Fix serial startup problems. (#1701)
* pass source_address in tcp client. (#1700)
* serial server use source_address[0]. (#1699)
* Examples coverage nearly 100%. (#1694)
* new async serial (#1681)
* Docker is not supported (lack of maintainer). (#1693)
* Forwarder write_coil --> write_coil. (#1691)
* Change default source_address to (0.0.0.0, 502) (#1690)
* Update ruff to 0.0.277 (#1689)
* Fix dict comprehension (#1687)
* Removed `requests` dependency from `contrib/explain.py`  (#1688)
* Fix broken test (#1685)
* Fix readme badges (#1682)
* Bump aiohttp from 3.8.3 to 3.8.5 (#1680)
* pygments from 2.14.0 to 2.15.0 (#1677)


Version 3.4.0
-------------
* Handle partial local echo. (#1675)
* clarify handle_local_echo. (#1674)
* async_client: add retries/reconnect. (#1672)
* Fix 3.11 problem. (#1673)
* Add new example simulator server/client. (#1671)
* `examples/contrib/explain.py` leveraging Rapid SCADA (#1665)
* _logger missed basicConfig. (#1670)
* Bug fix for #1662 (#1663)
* Bug fix for #1661 (#1664)
* Fix typo in config.rst (#1660)
* test action_increment. (#1659)
* test codeql (#1655)
* mypy complaints. (#1656)
* Remove self.params from async client (#1640)
* Drop test of pypy with python 3.8.
* repair server_async.py (#1644)
* move common framer to base. (#1639)
* Restrict Return diag call to bytes. (#1638)
* use slave= in diag requests. (#1636)
* transport listen in server. (#1628)
* CI test.
* Integrate transport in server. (#1617)
* fix getFrameStart for ExceptionResponse (#1627)
* Add min/min to simulator actions.
* Change to "sync client" in forwarder example (#1625)
* Remove docker (lack of maintenance). (#1623)
* Clean defaults (#1618)
* Reduce CI log with no debug. (#1616)
* prepare server to use transport. (#1607)
* Fix RemoteSlaveContext (#1599)
* Combine stale and lock. (#1608)
* update pytest + extensions. (#1610)
* Change version follow PEP 440. (#1609)
* Fix regression with REPL server not listening (#1604)
* Remove handler= for server classes. (#1602)
* Fix write function codes (#1598)
* transport nullmodem (#1591)
* move test of examples to subdirectory. (#1592)
* transport as object, not base class. (#1572)
* Simple examples. (#1590)
* transport_connect as bool. (#1587)
* Prepare dev (#1588)
* Release corrections. (#1586)


Version 3.3.2
-------------
* Fix RemoteSlaveContext (#1599)
* Change version follow PEP 440. (#1609)
* Fix regression with REPL server not listening (#1604)
* Fix write function codes (#1598)
* Release corrections. (#1586)


Version 3.3.1
-------------
* transport fixes and 100% test coverage. (#1580)
* Delay self.loop until connect(). (#1579)
* Added mechanism to determine if server did not start cleanly (#1539)
* Proof transport reconnect works. (#1577)
* Fix non-shared block doc in config.rst. (#1573)


Version 3.3.0
-------------
* Stabilize windows tests. (#1567)
* Bump mypy 1.3.0 (#1568)
* Transport integrated in async clients. (#1541)
* Client async corrections (due to 3.1.2) (#1565)
* Server_async[udp], solve 3.1.1 problem. (#1564)
* Remove ModbusTcpDiagClient. (#1560)
* Remove old method from Python2/3 transition (#1559)
* Switch to ruff's version of bandit (#1557)
* Allow reading/writing address 0 in the simulator (#1552)
* Remove references to "defer_start". (#1548)
* Client more robust against faulty response. (#1547)
* Fix missing package_data directives for simulator web (#1544)
* Fix installation instructions (#1543)
* Solve pytest timeout problem. (#1540)
* DiagnosticStatus encode missing tuple check. (#1533)
* test SparseDataStore. (#1532)
* BinaryPayloadBuilder.to_string to BinaryPayloadBuilder.encode (#1526)
* Adding flake8-pytest-style` to ruff (#1520)
* Simplify version management. (#1522)
* pylint and pre-commit autoupdate (#1519)
* Add type hint (#1512)
* Add action to lock issues/PR. (#1508)
* New common transport layer. (#1492)
* Solve serial close raise problem.
* Remove old config values (#1503)
* Document pymodbus.simulator. (#1502)
* Refactor REPL server to reduce complexity (#1499)
* Don't catch KeyboardInterrupt twice for REPL server (#1498)
* Refactor REPL client to reduce complexity (#1489)
* pymodbus.server: listen on ID 1 by default (#1496)
* Clean framer/__init__.py (#1494)
* Duplicate transactions in UDP. (#1486)
* clean ProcessIncommingPacket. (#1491)
* Enable pyupgrade (U) rules in ruff (#1484)
* clean_workflow.yaml solve parameter problem.
* Correct wrong import in test. (#1483)
* Implement pyflakes-simplify (#1480)
* Test case for UDP duplicate msg issue (#1470)
* Test of write_coil. (#1479)
* Test reuse of client object. (#1475)
* Comment about addressing when shared=false (#1474)
* Remove old aliases to OSError (#1473)
* pymodbus.simulator fixes (#1463)
* Fix wrong error message with pymodbus console (#1456)
* update modbusrtuframer (#1435)
* Server multidrop test.: (#1451)
* mypy problem ModbusResponse.


Version 3.2.2
-------------
* Add forgotten await


Version 3.2.1
-------------
* add missing server.start(). (#1443)
* Don't publish univeral (Python2 / Python 3) wheels (#1423)
* Remove unneccesary custom LOG_LEVEL check (#1424)
* Include py.typed in package (#1422)


Version 3.2.0
-------------
* Add value <-> registers converter helpers. (#1413)
* Add pre-commit config (#1406)
* Make baud rate configurable for examples (#1410)
* Clean __init_ and update log module. (#1411)
* Simulator add calls functionality. (#1390)
* Add note about not being thread safe. (#1404)
* Update docker-publish.yml
* Forward retry_on_empty and retries by calling transaction (#1401)
* serial sync recv interval (#1389)
* Add tests for writing multiple writes with a single value (#1402)
* Enable mypy in CI (#1388)
* Limit use of Singleton. (#1397)
* Cleanup interfaces (#1396)
* Add request names. (#1391)
* Simulator, register look and feel. (#1387)
* Fix enum for REPL server (#1384)
* Remove unneeded attribute (#1383)
* Fix mypy errors in reactive server (#1381)
* remove nosec (#1379)
* Fix type hints for http_server (#1369)
* Merge pull request #1380 from pymodbus-dev/requirements
* remove second client instance in async mode. (#1367)
* Pin setuptools to prevent breakage with Version including "X" (#1373)
* Lint and type hints for REPL (#1364)
* Clean mixin execute (#1366)
* Remove unused setup_commands.py. (#1362)
* Run black on top-level files and /doc (#1361)
* repl config path (#1359)
* Fix NoReponse -> NoResponse (#1358)
* Make whole main async. (#1355)
* Fix more typing issues (#1351)
* Test sync task (#1341)
* Fixed text in ModbusClientMixin's writes (#1352)
* lint /doc (#1345)
* Remove unused linters (#1344)
* Allow log level as string or integer. (#1343)
* Sync serial, clean recv. (#1340)
* Test server task, async completed (#1318)
* main() should be sync (#1339)
* Bug: Fixed caused by passing wrong arg (#1336)


Version 3.1.3
-------------
* Solve log problem in payload.
* Fix register type check for size bigger than 3 registers (6 bytes) (#1323)
* Re-add SQL tests. (#1329)
* Central logging. (#1324)
* Skip sqlAlchemy test. (#1325)
* Solve 1319 (#1320)


Version 3.1.2
-------------
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


Version 3.1.1
-------------
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


Version 3.1.0
-------------
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


Version 3.0.2
-------------
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


Version 3.0.1
-------------
* Faulty release!


Version 3.0.0
-------------
* Solve multiple incomming frames. (#1107)
* Up coverage, tests are 100%. (#1098)
* Prepare for rc1. (#1097)
* Prepare 3.0.0dev5 (#1095)
* Adapt serial tests. (#1094)
* Allow windows. (#1093)
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
* Documentation updates
* PEP8 compatibale code
* More tooling and CI updates
* Remove python2 compatibility code (#564)
* Remove Python2 checks and Python2 code snippets
* Misc co-routines related fixes
* Fix CI for python3 and remove PyPI from CI
* Fix mask_write_register call. (#685)
* Add support for byte strings in the device information fields (#693)
* Catch socket going away. (#722)
* Misc typo errors (#718)
* Support python3.10
* Implement asyncio ModbusSerialServer
* ModbusTLS updates (tls handshake, default framer)
* Support broadcast messages with asyncio client
* Fix for lazy loading serial module with asyncio clients.
* Updated examples and tests
* Support python3.7 and above
* Support creating asyncio clients from with in coroutines.


Version 2.5.3
-------------
* Fix retries on tcp client failing randomly.
* Fix Asyncio client timeout arg not being used.
* Treat exception codes as valid responses
* Fix examples (modbus_payload)
* Add missing identity argument to async ModbusSerialServer


Version 2.5.2
-------------
* Add kwarg `reset_socket` to control closing of the socket on read failures (set to `True` by default).
* Add `--reset-socket/--no-reset-socket` to REPL client.


Version 2.5.1
-------------
* Bug fix TCP Repl server.
* Support multiple UID's with REPL server.
* Support serial for URL (sync serial client)
* Bug fix/enhancements, close socket connections only on empty or invalid response


Version 2.5.0
-------------
* Support response types `stray` and `empty` in repl server.
* Minor updates in asyncio server.
* Update reactive server to send stray response of given length.
* Transaction manager updates on retries for empty and invalid packets.
* Test fixes for asyncio client and transaction manager.
* Fix sync client and processing of incomplete frames with rtu framers
* Support synchronous diagnostic client (TCP)
* Server updates (REPL and async)
* Handle Memory leak in sync servers due to socketserver memory leak
* Minor fix in documentations
* Travis fix for Mac OSX
* Disable unnecessary deprecation warning while using async clients.
* Use Github actions for builds in favor of travis.
* Documentation updates
* Disable `strict` mode by default.
* Fix `ReportSlaveIdRequest` request
* Sparse datablock initialization updates.
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
-------------
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
-------------
* Support Modbus TLS (client / server)
* Distribute license with source
* BinaryPayloadDecoder/Encoder now supports float16 on python3.6 and above
* Fix asyncio UDP client/server
* Minor cosmetic updates
* Asyncio Server implementation (Python 3.7 and above only)
* Bug fix for DiagnosticStatusResponse when odd sized response is received
* Remove Pycrypto from dependencies and include cryptodome instead
* Remove `SIX` requirement pinned to exact version.
* Minor bug-fixes in documentations.


Version 2.2.0
-------------
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


Version 2.1.0
-------------
* Fix Issues with Serial client where in partial data was read when the response size is unknown.
* Fix Infinite sleep loop in RTU Framer.
* Add pygments as extra requirement for repl.
* Add support to modify modbus client attributes via repl.
* Update modbus repl documentation.
* More verbose logs for repl.


Version 2.0.1
-------------
* Fix unicode decoder error with BinaryPayloadDecoder in some platforms
* Avoid unnecessary import of deprecated modules with dependencies on twisted


Version 2.0.0
-------------
* Async client implementation based on Tornado, Twisted and asyncio with backward compatibility support for twisted client.
* Allow reusing existing[running] asyncio loop when creating async client based on asyncio.
* Allow reusing address for Modbus TCP sync server.
* Add support to install tornado as extra requirement while installing pymodbus.
* Support Pymodbus REPL
* Add support to python 3.7.
* Bug fix and enhancements in examples.
* Async client implementation based on Tornado, Twisted and asyncio


Version 1.5.2
-------------
* Fix serial client `is_socket_open` method

Version 1.5.1
-------------
* Fix device information selectors
* Fixed behaviour of the MEI device information command as a server when an invalid object_id is provided by an external client.
* Add support for repeated MEI device information Object IDs (client/server)
* Added support for encoding device information when it requires more than one PDU to pack.
* Added REPR statements for all syncchronous clients
* Added `isError` method to exceptions, Any response received can be tested for success before proceeding.
* Add examples for MEI read device information request


Version 1.5.0
-------------
* Improve transaction speeds for sync clients (RTU/ASCII), now retry on empty happens only when retry_on_empty kwarg is passed to client during intialization
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
-------------
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
-------------
* ModbusSerialServer could now be stopped when running on a seperate thread.
* Fix issue with server and client where in the frame buffer had values from previous unsuccesful transaction
* Fix response length calculation for ModbusASCII protocol
* Fix response length calculation ReportSlaveIdResponse, DiagnosticStatusResponse
* Fix never ending transaction case when response is received without header and CRC
* Fix tests


Version 1.3.1
-------------
* Recall socket recv until get a complete response
* Register_write_message.py: Observe skip_encode option when encoding a single register request
* Fix wrong expected response length for coils and discrete inputs
* Fix decode errors with ReadDeviceInformationRequest and  ReportSlaveIdRequest on Python3
* Move MaskWriteRegisterRequest/MaskWriteRegisterResponse  to register_write_message.py from file_message.py
* Python3 compatible examples [WIP]
* Misc updates with examples
* Fix encoding problem for ReadDeviceInformationRequest method on python3
* Fix problem with the usage of ord in python3 while cleaning up receive buffer
* Fix struct unpack errors with BinaryPayloadDecoder on python3 - string vs bytestring error
* Calculate expected response size for ReadWriteMultipleRegistersRequest
* Enhancement for ModbusTcpClient, ModbusTcpClient can now accept connection timeout as one of the parameter
* Misc updates
* Timing improvements over MODBUS Serial interface
* Modbus RTU use 3.5 char silence before and after transactions
* Bug fix on FifoTransactionManager , flush stray data before transaction
* Update repository information
* Added ability to ignore missing slaves
* Added ability to revert to ZeroMode
* Passed a number of extra options through the stack
* Fixed documenation and added a number of examples


Version 1.2.0
-------------
* Reworking the transaction managers to be more explicit and
  to handle modbus RTU over TCP.
* Adding examples for a number of unique requested use cases
* Allow RTU framers to fail fast instead of staying at fault
* Working on datastore saving and loading


Version 1.1.0
-------------
* Fixing memory leak in clients and servers (removed __del__)
* Adding the ability to override the client framers
* Working on web page api and GUI
* Moving examples and extra code to contrib sections
* Adding more documentation


Version 1.0.0
-------------
* Adding support for payload builders to form complex encoding
  and decoding of messages.
* Adding BCD and binary payload builders
* Adding support for pydev
* Cleaning up the build tools
* Adding a message encoding generator for testing.
* Now passing kwargs to base of PDU so arguments can be used
  correctly at all levels of the protocol.
* A number of bug fixes (see bug tracker and commit messages)
