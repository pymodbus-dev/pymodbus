============================================================
Contributed Implementations
============================================================

There are a few example implementations of custom utilities
interacting with the pymodbus library just to show what is
possible.

------------------------------------------------------------
SqlAlchemy Database Datastore Backend
------------------------------------------------------------

This module allows one to use any database available through
the sqlalchemy package as a datastore for the modbus server.
This could be useful to have many servers who have data they
agree upon and is transactional.

------------------------------------------------------------
Redis Datastore Backend
------------------------------------------------------------

This module allows one to use redis as a modbus server
datastore backend. This achieves the same thing as the
sqlalchemy backend, however, it is much more lightweight and
easier to set up.

------------------------------------------------------------
Binary Coded Decimal Payload
------------------------------------------------------------

This module allows one to write binary coded decimal data to
the modbus server using the payload encoder/decoder
interfaces.
