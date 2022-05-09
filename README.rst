================================
PyModbus - A Python Modbus Stack
================================

.. image:: https://github.com/riptideio/pymodbus/actions/workflows/ci.yml/badge.svg?branch=dev
   :target: https://github.com/riptideio/pymodbus/actions/workflows/ci.yml
.. image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/pymodbus_dev/Lobby 
.. image:: https://readthedocs.org/projects/pymodbus/badge/?version=latest
   :target: http://pymodbus.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. image:: http://pepy.tech/badge/pymodbus
   :target: http://pepy.tech/project/pymodbus 
   :alt: Downloads
   
------------------------------------------------------------
Supported versions
------------------------------------------------------------

Version `2.5.3 <https://github.com/riptideio/pymodbus/releases/tag/v2.5.3>`_ is the last 2.x release (Supports python 2.7.x - 3.7).

Version `3.0.0dev3 <https://github.com/riptideio/pymodbus/releases/tag/v3.0.0dev3>`_ is the current prerelease of 3.0.0 (Supports Python >=3.8).

Remark: "Supports" means that we only test with those versions, lower versions (e.g. 3.7) might work depending on the functionality used.

.. important::
   **Note 3.0.0 is a major release with a number of incompatible changes.**

------------------------------------------------------------
Summary
------------------------------------------------------------

Pymodbus is a full Modbus protocol implementation using a synchronous or asynchronous core. The preferred mode for asynchronous communication is asyncio, however for the moment twisted and tornado are also supported (due to be removed or converted to a plugin in a later version).

Supported modbus communication modes: tcp, rtu-over-tcp, udp, serial, tls

Pymodbus can be used without any third party dependencies (aside from pyserial) and is a very lightweight project.

Pymodbus also provides a lot os ready to use examples as well as a server/client simulator which can be controlled via REST Api and can be easily integrated into test suites.

Requires Python >= 3.8

The tests are run against Python 3.8, 3.9, 3.10 on Windows, Linux and MacOS.

------------------------------------------------------------
Features
------------------------------------------------------------

~~~~~~~~~~~~~~~~~~~~
Client Features
~~~~~~~~~~~~~~~~~~~~

  * Full read/write protocol on discrete and register
  * Most of the extended protocol (diagnostic/file/pipe/setting/information)
  * TCP, RTU-OVER-TCP, UDP, TLS, Serial ASCII, Serial RTU, and Serial Binary
  * asynchronous(powered by asyncio/twisted/tornado) and synchronous versions
  * Payload builder/decoder utilities
  * Pymodbus REPL for quick tests
  * Customable framer to allow for custom implementations

~~~~~~~~~~~~~~~~~~~~
Server Features
~~~~~~~~~~~~~~~~~~~~

  * Can function as a fully implemented modbus server
  * TCP, RTU-OVER-TCP, UDP, TLS, Serial ASCII, Serial RTU, and Serial Binary
  * asynchronous(powered by twisted) and synchronous versions
  * Full server control context (device information, counters, etc)
  * A number of backend contexts (database, redis, sqlite, a slave device) as datastore

^^^^^^^^^^^
Use Cases
^^^^^^^^^^^

Although most system administrators will find little need for a Modbus
server on any modern hardware, they may find the need to query devices on
their network for status (PDU, PDR, UPS, etc). Since the library is written
in python, it allows for easy scripting and/or integration into their existing
solutions.

Continuing, most monitoring software needs to be stress tested against
hundreds or even thousands of devices (why this was originally written), but
getting access to that many is unwieldy at best.

The pymodbus server will allow a user to test as many devices as their
base operating system will allow (*allow* in this case means how many Virtual IP addresses are allowed).

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

If you are looking for UI,checkout `Modbus Simulator <https://github.com/riptideio/modbus-simulator>`_ or
`Modbus Cli <https://github.com/dhoomakethu/modbus_sim_cli>`_

Also, if you have a question, please `create a post in discussions q&a topic <https://github.com/riptideio/pymodbus/discussions/new?category=q-a>`_,
so that others can benefit from the results.

If you think, that something in the code is broken/not running well, please `open an issue <https://github.com/riptideio/pymodbus/issues/new>`_, read the Template-text first and then post your issue with your setup informations.

.. important::
   **Note For async clients, it is recommended to use `asyncio` as the async facilitator.**
   **If using tornado make sure the tornado version is `4.5.3` other versions of tornado can break the implementation**


------------------------------------------------------------
Pymodbus REPL (Read Evaluate Print Loop)
------------------------------------------------------------
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

This will install a base version of pymodbus.

To install pymodbus with options run:

    pip install -U pymodbus[<option>,...]
    
Available options are:

- **repl**, installs pymodbus REPL.

- **serial**, installs serial drivers.

- **datastore**, installs databases (SQLAlchemy and Redit) for datastore.

- **twisted**, installs twisted as alternative to asyncio (will be removed in a future version).

- **tornado**, installs tornado as alternative to asyncio (will be removed in a future version).

- **documentation**, installs tools to generate documentation.

- **development**, installs development tools needed to enable test/check of pymodbus changes.


Or to install a specific release::

    pip install  -U pymodbus==X.Y.Z
    easy_install -U pymodbus==X.Y.Z

Otherwise you can pull the trunk source and install from there::

    git clone git://github.com/bashwork/pymodbus.git
    cd pymodbus
    pip install -r requirements.txt
    
    
To get latest release (for now v2.5.3 with python 2.7 support)::

    git checkout master

To get bleeding edge::

    git checkout dev

To get a specific version:

    git checkout tags/vX.Y.Z -b vX.Y.Z    

Then::
   pip install -e .
   
This installs pymodbus in your virtual environment with pointers directly to the pymodbus directory, so any change you make is imidiatly available as if installed.

Either method will install all the required dependencies
(at their appropriate versions) for your current python distribution.

------------------------------------------------------------
Repository structure
------------------------------------------------------------
The repository contains a number of important branches and tags.
  * **dev** is where all development happens, this branch is not always stable.
  * **master** is where are releases are kept.
  * All releases are tagged with **vX.Y.Z** (e.g. v2.5.3)
  * All prereleases are tagged with **vX.Y.ZrcQ** (e.g. v3.0.0.0rc1)
 
If a maintenance release of an old version is needed (e.g. v2.5.4),
the release tag is used to create a branch with the same name,
and maintenance development is merged here.

------------------------------------------------------------
Current Work In Progress
------------------------------------------------------------

The maintenance team is very small with limited capacity
and few modbus devices.

However, if you would like your device tested,
we accept devices via mail or by IP address.

That said, the current work mainly involves polishing the library and
solving issues:

  * Get version 3.0.0 released
  * Make PEP-8 compatible and pylint, flake8, black and mypy ready
  * Fixing bugs/feature requests
  * Architecture documentation
  * Functional testing against any reference we can find
  * The remaining edges of the protocol (that we think no one uses)

------------------------------------------------------------
Development Instructions
------------------------------------------------------------
The current code base is compatible python >= 3.8.
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

Here are some of the items waiting to be done:
   https://github.com/riptideio/pymodbus/blob/3.0.0/doc/TODO

------------------------------------------------------------
License Information
------------------------------------------------------------

Pymodbus is built on top of code developed from/by:
  * Copyright (c) 2001-2005 S.W.A.C. GmbH, Germany.
  * Copyright (c) 2001-2005 S.W.A.C. Bohemia s.r.o., Czech Republic.

  * Hynek Petrak, https://github.com/HynekPetrak
  * Twisted Matrix

Released under the `BSD License <LICENSE>`_
