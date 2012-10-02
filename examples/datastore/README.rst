============================================================
Custom Datastore Implementations
============================================================

There are a few example implementations of custom datastores
just to show what is possible.

------------------------------------------------------------
SqlAlchemy Backend
------------------------------------------------------------

This module allows one to use any database available through
the sqlalchemy package as a datastore for the modbus server.
This could be useful to have many servers who have data they
agree upon and is transactional.

------------------------------------------------------------
Redis Backend
------------------------------------------------------------

This module allows one to use redis as a modbus server
datastore backend. This achieves the same thing as the
sqlalchemy backend, however, it is much more lightweight and
easier to set up.

