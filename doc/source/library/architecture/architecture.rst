Architecture
=============

The internal structure of pymodbus is a bit complicated, mostly due to the mixture of sync and async.

The overall architecture can be viewed as:


    Client classes (interface to applications)
    mixin (interface with all requests defined as methods)
    Lower levels are Common

    Server classes (interface to applications)
    datastores (handles registers/values to be returned)
    Lower levels are Common

    pdu (build/create response/request class)
    transaction (handles transactions and allow concurrent calls)
    framers (add pre/post headers to make a valid package)
    transport (handles actual transportation)

In detail the packages can viewed as:

.. image:: packages.png


In detail the classes can be viewed as:

.. image:: classes.png
