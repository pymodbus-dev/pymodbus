================================
PyModbus - A Python Modbus Stack
================================

.. image:: https://travis-ci.org/riptideio/pymodbus.svg?branch=master
   :target: https://travis-ci.org/riptideio/pymodbus 
.. image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/pymodbus_dev/Lobby 
.. image:: https://readthedocs.org/projects/pymodbus/badge/?version=latest
   :target: http://pymodbus.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. image:: http://pepy.tech/badge/pymodbus
   :target: http://pepy.tech/project/pymodbus 
   :alt: Downloads
   
.. important::
   **Note This is a Major release and might affect your existing Async client implementation. Refer examples on how to use the latest async clients.**

------------------------------------------------------------
Summary
------------------------------------------------------------

Pymodbus is a full Modbus protocol implementation using twisted/torndo/asyncio for its
asynchronous communications core.  It can also be used without any third
party dependencies (aside from pyserial) if a more lightweight project is
needed.  Furthermore, it should work fine under any python version > 2.7
(including python 3+)


------------------------------------------------------------
Features
------------------------------------------------------------

~~~~~~~~~~~~~~~~~~~~
Client Features
~~~~~~~~~~~~~~~~~~~~

  * Full read/write protocol on discrete and register
  * Most of the extended protocol (diagnostic/file/pipe/setting/information)
  * TCP, UDP, Serial ASCII, Serial RTU, and Serial Binary
  * asynchronous(powered by twisted/tornado/asyncio) and synchronous versions
  * Payload builder/decoder utilities
  * Pymodbus REPL for quick tests

~~~~~~~~~~~~~~~~~~~~
Server Features
~~~~~~~~~~~~~~~~~~~~

  * Can function as a fully implemented modbus server
  * TCP, UDP, Serial ASCII, Serial RTU, and Serial Binary
  * asynchronous(powered by twisted) and synchronous versions
  * Full server control context (device information, counters, etc)
  * A number of backing contexts (database, redis, sqlite, a slave device)

------------------------------------------------------------
Use Cases
------------------------------------------------------------

Although most system administrators will find little need for a Modbus
server on any modern hardware, they may find the need to query devices on
their network for status (PDU, PDR, UPS, etc).  Since the library is written
in python, it allows for easy scripting and/or integration into their existing
solutions.

Continuing, most monitoring software needs to be stress tested against
hundreds or even thousands of devices (why this was originally written), but
getting access to that many is unwieldy at best.  The pymodbus server will allow
a user to test as many devices as their base operating system will allow (*allow*
in this case means how many Virtual IP addresses are allowed).

For more information please browse the project documentation:

http://riptideio.github.io/pymodbus/ 
or
http://readthedocs.org/docs/pymodbus/en/latest/index.html

------------------------------------------------------------
Example Code
------------------------------------------------------------

For those of you that just want to get started fast, here you go::

    from pymodbus.client.sync import ModbusTcpClient
    
    client = ModbusTcpClient('127.0.0.1')
    client.write_coil(1, True)
    result = client.read_coils(1,1)
    print(result.bits[0])
    client.close()

For more advanced examples, check out the `Examples <https://pymodbus.readthedocs.io/en/dev/source/example/modules.html>`_ included in the
repository. If you have created any utilities that meet a specific
need, feel free to submit them so others can benefit.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Examples Directory structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   examples
   ├── common.      -> Common examples for clients and server (sync/async), Payload encoders and decoders.
   ├── contrib.     -> Examples contributed by contributors. Serial Forwarder, Database contexts etc.
   ├── functional.  -> Not actively maintained.
   ├── gui.         -> Not actively maintained. If you are looking for UI,checkout `Modbus Simulator <https://github.com/riptideio/modbus-simulator>`_ or `Modbus Cli <https://github.com/dhoomakethu/modbus_sim_cli>`_
   ├── tools.       -> Not actively maintained.
   └── twisted.     -> Not actively maintained.

Also, if you have questions, please ask them on the mailing list
so that others can benefit from the results and so that I can
trace them. I get a lot of email and sometimes these requests
get lost in the noise: http://groups.google.com/group/pymodbus or 
at gitter:  https://gitter.im/pymodbus_dev/Lobby

.. important::
   **Note For async clients, it is recommended to use `asyncio` as the async facilitator (Python 3.6 and above).**
   **If using tornado make sure the tornado version is `4.5.3`.Other versions of tornado can break the implementation**


------------------------------------------------------------
Pymodbus REPL (Read Evaluate Print Loop)
------------------------------------------------------------
Starting with Pymodbus 2.x, pymodbus library comes with handy
Pymodbus REPL to quickly run the modbus clients in tcp/rtu modes.

Pymodbus REPL comes with many handy features such as payload decoder 
to directly retrieve the values in desired format and supports all
the diagnostic function codes directly .

For more info on REPL refer  `Pymodbus REPL <https://github.com/riptideio/pymodbus/tree/master/pymodbus/repl>`_

.. image:: https://asciinema.org/a/y1xOk7lm59U1bRBE2N1pDIj2o.png
   :target: https://asciinema.org/a/y1xOk7lm59U1bRBE2N1pDIj2o

------------------------------------------------------------
Installing
------------------------------------------------------------

You can install using pip or easy install by issuing the following
commands in a terminal window (make sure you have correct
permissions or a virtualenv currently running)::

    easy_install -U pymodbus
    pip install  -U pymodbus

To Install pymodbus with twisted support run::

    pip install -U pymodbus[twisted]

To Install pymodbus with tornado support run::

    pip install -U pymodbus[tornado]

To Install pymodbus REPL::

    pip install -U pymodbus[repl]

Otherwise you can pull the trunk source and install from there::

    git clone git://github.com/bashwork/pymodbus.git
    cd pymodbus
    python setup.py install

Either method will install all the required dependencies
(at their appropriate versions) for your current python distribution.

If you would like to install pymodbus without the twisted dependency,
simply edit the setup.py file before running easy_install and comment
out all mentions of twisted.  It should be noted that without twisted,
one will only be able to run the synchronized version as the
asynchronous versions uses twisted for its event loop.

------------------------------------------------------------
Current Work In Progress
------------------------------------------------------------

Since I don't have access to any live modbus devices anymore
it is a bit hard to test on live hardware. However, if you would
like your device tested, I accept devices via mail or by IP address.

That said, the current work mainly involves polishing the library as
I get time doing such tasks as:

  * Make PEP-8 compatible and flake8 ready
  * Fixing bugs/feature requests
  * Architecture documentation
  * Functional testing against any reference I can find
  * The remaining edges of the protocol (that I think no one uses)
  * Asynchronous clients with support to tornado , asyncio  

------------------------------------------------------------
Development Instructions
------------------------------------------------------------
The current code base is compatible with both py2 and py3.
Use make to perform a range of activities

::

    $ make
       Makefile for pymodbus

    Usage:

     make install    install the package in a virtual environment
     make reset      recreate the virtual environment
     make check      check coding style (PEP-8, PEP-257)
     make test       run the test suite, report coverage
     make tox        run the tests on all Python versions
     make clean      cleanup all temporary files 

------------------------------------------------------------
Contributing
------------------------------------------------------------
Just fork the repo and raise your PR against `dev` branch.

------------------------------------------------------------
License Information
------------------------------------------------------------

Pymodbus is built on top of code developed from/by:
  * Copyright (c) 2001-2005 S.W.A.C. GmbH, Germany.
  * Copyright (c) 2001-2005 S.W.A.C. Bohemia s.r.o., Czech Republic.

  * Hynek Petrak, https://github.com/HynekPetrak
  * Twisted Matrix

Released under the `BSD License <LICENSE>`_
