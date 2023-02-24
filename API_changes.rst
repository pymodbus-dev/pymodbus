=======================
PyModbus - API changes.
=======================

-------------
Version 3.2.0
-------------
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
