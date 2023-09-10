Examples
========

Examples are divided in 2 parts:

The first part are some simple client examples which can be copied and run directly.
These examples show the basic functionality of the library.

The second part are more advanced examples, but in order to not duplicate code,
this requires you to download the examples directory and run
the examples in the directory.

Ready to run examples:
----------------------

These examples are very basic examples,
showing how a client can communicate with a server.

You need to modify the code to adapt it to your situation.

Simple asynchronous client
^^^^^^^^^^^^^^^^^^^^^^^^^^
Source: `examples/simple_async_client.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/simple_async_client.py>`_

.. literalinclude:: ../../examples/simple_async_client.py

Simple synchronous client
^^^^^^^^^^^^^^^^^^^^^^^^^^
Source: `examples/simple_sync_client.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/simple_sync_client.py>`_

.. literalinclude:: ../../examples/simple_sync_client.py


Client performance sync vs async
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Source: `examples/client_performance.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/client_performance.py>`_

.. literalinclude:: ../../examples/client_performance.py


Advanced examples
-----------------

These examples are considered essential usage examples, and are guaranteed to work,
because they are tested automatilly with each dev branch commit using CI.

.. tip:: The examples needs to be run from within the examples directory, unless you modify them.
    Most examples use helper.py and client_*.py or server_*.py. This is done to avoid maintaining the
    same code in multiple files.

    - :download:`examples.zip <_static/examples.zip>`
    - :download:`examples.tgz <_static/examples.tgz>`


Client asynchronous calls
^^^^^^^^^^^^^^^^^^^^^^^^^
Source: `examples/client_async_calls.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/client_async_calls.py>`_

.. automodule:: examples.client_async_calls
    :undoc-members:
    :noindex:


Client asynchronous
^^^^^^^^^^^^^^^^^^^
Source: `examples/client_async.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/client_async.py>`_

.. automodule:: examples.client_async
    :undoc-members:
    :noindex:


Client calls
^^^^^^^^^^^^
Source: `examples/client_calls.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/client_calls.py>`_

.. automodule:: examples.client_calls
    :undoc-members:
    :noindex:


Client custom message
^^^^^^^^^^^^^^^^^^^^^
Source: `examples/client_custom_msg.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/client_custom_msg.py>`_

.. automodule:: examples.client_custom_msg
    :undoc-members:
    :noindex:


Client payload
^^^^^^^^^^^^^^
Source: `examples/client_payload.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/client_payload.py>`_

.. automodule:: examples.client_payload
    :undoc-members:
    :noindex:

Client synchronous
^^^^^^^^^^^^^^^^^^
Source: `examples/client_sync.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/client_sync.py>`_

.. automodule:: examples.client_sync
    :undoc-members:
    :noindex:


Server asynchronous
^^^^^^^^^^^^^^^^^^^
Source: `examples/server_async.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/server_async.py>`_

.. automodule:: examples.server_async
    :undoc-members:
    :noindex:


Server callback
^^^^^^^^^^^^^^^
Source: `examples/server_callback.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/server_callback.py>`_

.. automodule:: examples.server_callback
    :undoc-members:
    :noindex:


Server tracer
^^^^^^^^^^^^^
Source: `examples/server_hook.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/server_hook.py>`_

.. automodule:: examples.server_hook
    :undoc-members:
    :noindex:


Server payload
^^^^^^^^^^^^^^
Source: `examples/server_payload.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/server_payload.py>`_

.. automodule:: examples.server_payload
    :undoc-members:
    :noindex:


Server synchronous
^^^^^^^^^^^^^^^^^^
Source: `examples/server_sync.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/server_sync.py>`_

.. automodule:: examples.server_sync
    :undoc-members:
    :noindex:


Server updating
^^^^^^^^^^^^^^^
Source: `examples/server_updating.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/server_updating.py>`_

.. automodule:: examples.server_updating
    :undoc-members:
    :noindex:


Simulator example
^^^^^^^^^^^^^^^^^
Source: `examples/simulator.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/simulator.py>`_

.. automodule:: examples.simulator
    :undoc-members:
    :noindex:


Simulator datastore example
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Source: `examples/datastore_simulator.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/datastore_simulator.py>`_

.. automodule:: examples.datastore_simulator
    :undoc-members:
    :noindex:


Message generator
^^^^^^^^^^^^^^^^^
Source: `examples/message_generator.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/message_generator.py>`_

.. automodule:: examples.message_generator
    :undoc-members:
    :noindex:


Message Parser
^^^^^^^^^^^^^^
Source: `examples/message_parser.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/message_parser.py>`_

.. automodule:: examples.message_parser
    :undoc-members:
    :noindex:


Modbus forwarder
^^^^^^^^^^^^^^^^
Source: `examples/modbus_forwarder.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/modbus_forwarder.py>`_

.. automodule:: examples.modbus_forwarder
    :undoc-members:
    :noindex:


Examples contributions
----------------------

These examples are supplied by users of pymodbus.
The pymodbus team thanks for sharing the examples.

Solar
^^^^^
Source: :`examples/contrib/solar.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/contrib/solar.py>`_

.. automodule:: examples.contrib.solar
    :undoc-members:
    :noindex:


Redis datastore
^^^^^^^^^^^^^^^
Source: `examples/contrib/redis_datastore.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/contrib/redis_datastore.py>`_

.. automodule:: examples.contrib.redis_datastore
    :undoc-members:
    :noindex:


Serial Forwarder
^^^^^^^^^^^^^^^^
Source: `examples/contrib/serial_forwarder.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/contrib/serial_forwarder.py>`_

.. automodule:: examples.contrib.serial_forwarder
    :undoc-members:
    :noindex:


Sqlalchemy datastore
^^^^^^^^^^^^^^^^^^^^
Source: `examples/contrib/sql_datastore.py <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/contrib/sql_datastore.py>`_

.. automodule:: examples.contrib.sql_datastore
    :undoc-members:
    :noindex:
