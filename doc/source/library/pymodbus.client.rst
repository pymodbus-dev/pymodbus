pymodbus\.client package
========================

Pymodbus offers a :mod:`synchronous client <pymodbus.client.sync>`, and async clients based on :mod:`asyncio <pymodbus.client.asynchronous.async_io>`, :mod:`Tornado <pymodbus.client.asynchronous.tornado>`, and :mod:`Twisted <pymodbus.client.asynchronous.Twisted>`.

Each client shares a :mod:`common client mixin <pymodbus.client.common>` which offers simple methods for reading and writing.

Subpackages
-----------

.. toctree::

    pymodbus.client.asynchronous

Submodules
----------

pymodbus\.client\.common module
-------------------------------

.. automodule:: pymodbus.client.common
    :members:
    :undoc-members:
    :show-inheritance:

pymodbus\.client\.sync module
-----------------------------

.. automodule:: pymodbus.client.sync
    :members:
    :undoc-members:
    :show-inheritance:


