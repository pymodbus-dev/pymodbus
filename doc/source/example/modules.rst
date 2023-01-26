=========
Examples.
=========

The examples are divived in 3 (4) parts:

   - v2.5.3 examples

      these examples have not been upgraded to v3.0.0 but are still
      relevant.

   - v.2.5.3 tornado_twisted examples

      these examples uses the tornado/twisted frameworks which no longer
      are supported in pymodbus.

      These examples are only available in the repository.

   - contrib examples

      these examples are supplied by users of pymodbus. The pymodbus sends
      thanks for making the examples available to the community.

   - examples

      these examples are considered essential usage examples, and are
      guarenteed to work, because they are tested automatilly with each
      commit using CI.


Examples version 3.x
--------------------

Asynchronous Client Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/client_async.py

Asynchronous Client basic calls example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/client_calls.py

Modbus Payload Example
^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/client_payload.py

Synchronous Client Example
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/client_sync.py

Forwarder Example
^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/modbus_forwarder.py

Asynchronous server example
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/server_async.py

Modbus Payload Server example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/server_payload.py

Synchronous server example
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/server_sync.py

Updating server example
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/server_updating.py

Modbus Simulator example
^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/v2.5.3/modbus_simulator.py


Examples contributions
----------------------

Serial Forwarder example
^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/contrib/serial_forwarder.py



Examples version 2.5.3
----------------------

Asynchronous Asyncio Modbus TLS Client example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/v2.5.3/asynchronous_asyncio_modbus_tls_client.py

Bcd Payload example
^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/v2.5.3/bcd_payload.py

Callback Server example
^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/v2.5.3/callback_server.py

Changing Framers example
^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/v2.5.3/changing_framers.py

Concurrent Client example
^^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/v2.5.3/concurrent_client.py

Custom Datablock example
^^^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/v2.5.3/custom_datablock.py

Custom Message example
^^^^^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/v2.5.3/custom_message.py


.. toctree::
   :maxdepth: 4

   dbstore_update_server
   deviceinfo_showcase_client
   deviceinfo_showcase_server
   libmodbus_client
   message_generator
   message_parser
   modbus_logging
   modbus_mapper
   modbus_saver
   modbus_tls_client
   modicon_payload
   performance
   remote_server_context
   thread_safe_datastore
