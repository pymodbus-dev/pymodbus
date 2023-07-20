================================
PyModbus - A Python Modbus Stack
================================
We are constantly working the modernize pymodbus and add new features, and we look for people who want to help a bit.
There are challenges small and large not only programming but also documentation and testing.

.. image:: https://github.com/pymodbus-dev/pymodbus/actions/workflows/ci.yml/badge.svg?branch=dev
   :target: https://github.com/pymodbus-dev/pymodbus/actions/workflows/ci.yml
 .. image:: https://readthedocs.org/projects/pymodbus/badge/?version=latest
   :target: https://pymodbus.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. image:: https://pepy.tech/badge/pymodbus
   :target: https://pepy.tech/project/pymodbus
   :alt: Downloads
.. image:: https://ghcr-badge.deta.dev/pymodbus-dev/pymodbus/tags?label=Docker
   :target: https://github.com/pymodbus-dev/pymodbus/pkgs/container/pymodbus
   :alt: Docker Tags

------------------------------------------------------------
Supported versions
------------------------------------------------------------

Version `2.5.3 <https://github.com/pymodbus-dev/pymodbus/releases/tag/v2.5.3>`_ is the last 2.x release (python >= 2.7, no longer supported).

Version `3.4.0 <https://github.com/pymodbus-dev/pymodbus/releases/tag/v3.4.0>`_ is the current release (Tested with Python >= 3.8).

.. important::
   All API changes after 3.0.0 are documented in `API_changes.rst <https://github.com/pymodbus-dev/pymodbus/blob/dev/API_changes.rst>`_


------------------------------------------------------------
Summary
------------------------------------------------------------

Pymodbus is a full Modbus protocol implementation using a synchronous or asynchronous (using asyncio) core.

The modbus protocol documentation can be found `here <https://github.com/pymodbus-dev/pymodbus/blob/dev/doc/source/_static/Modbus_Application_Protocol_V1_1b3.pdf>`_

Supported modbus communication modes: tcp, rtu-over-tcp, udp, serial, tls

Pymodbus can be used without any third party dependencies (aside from pyserial) and is a very lightweight project.

Pymodbus also provides a lot of ready to use examples as well as a server/client simulator which can be controlled via a REST API and can be easily integrated into test suites.

Requires Python >= 3.8

The tests are run against Python 3.8, 3.9, 3.10, 3.11 on Windows, Linux and MacOS.

------------------------------------------------------------
Features
------------------------------------------------------------

~~~~~~~~~~~~~~~~~~~~
Client Features
~~~~~~~~~~~~~~~~~~~~

  * Full read/write protocol on discrete and register
  * Most of the extended protocol (diagnostic/file/pipe/setting/information)
  * TCP, RTU-OVER-TCP, UDP, TLS, Serial ASCII, Serial RTU, and Serial Binary
  * asynchronous(powered by asyncio) and synchronous versions
  * Payload builder/decoder utilities
  * Pymodbus REPL for quick tests
  * Customizable framer to allow for custom implementations

~~~~~~~~~~~~~~~~~~~~
Server Features
~~~~~~~~~~~~~~~~~~~~

  * Can function as a fully implemented modbus server
  * TCP, RTU-OVER-TCP, UDP, TLS, Serial ASCII, Serial RTU, and Serial Binary
  * asynchronous and synchronous versions
  * Full server control context (device information, counters, etc)
  * A number of backend contexts as datastore

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

https://readthedocs.org/docs/pymodbus/en/latest/index.html

------------------------------------------------------------
Example Code
------------------------------------------------------------

For those of you that just want to get started fast, here you go::

    from pymodbus.client import ModbusTcpClient

    client = ModbusTcpClient('127.0.0.1')
    client.connect()
    client.write_coil(1, True)
    result = client.read_coils(1,1)
    print(result.bits[0])
    client.close()

For more advanced examples, check out the `Examples <https://pymodbus.readthedocs.io/en/dev/source/examples.html>`_ included in the
repository. If you have created any utilities that meet a specific
need, feel free to submit them so others can benefit.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Examples Directory structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   examples      -> Essential examples guaranteed to work (tested with our CI)
   ├── v2.5.3    -> Examples not updated to version 3.0.0.
   ├── contrib   -> Examples contributed by contributors.

Also, if you have a question, please `create a post in discussions q&a topic <https://github.com/pymodbus-dev/pymodbus/discussions/new?category=q-a>`_,
so that others can benefit from the results.

If you think, that something in the code is broken/not running well, please `open an issue <https://github.com/pymodbus-dev/pymodbus/issues/new>`_, read the Template-text first and then post your issue with your setup information.

------------------------------------------------------------
Pymodbus REPL (Read Evaluate Print Loop)
------------------------------------------------------------

**Warning** The Pymodbus REPL documentation is not updated.

~~~~~~~~~~~~~~~~~~~~~
Pymodbus REPL Client
~~~~~~~~~~~~~~~~~~~~~

Pymodbus REPL comes with many handy features such as payload decoder
to directly retrieve the values in desired format and supports all
the diagnostic function codes directly .

For more info on REPL Client refer  `Pymodbus REPL Client <https://github.com/pymodbus-dev/pymodbus/blob/dev/pymodbus/repl/client/README.md>`_

.. image:: https://asciinema.org/a/y1xOk7lm59U1bRBE2N1pDIj2o.png
   :target: https://asciinema.org/a/y1xOk7lm59U1bRBE2N1pDIj2o

~~~~~~~~~~~~~~~~~~~~~
Pymodbus REPL Server
~~~~~~~~~~~~~~~~~~~~~

Pymodbus also comes with a REPL server to quickly run an asynchronous server with additional capabilities out of the box like simulating errors, delay, mangled messages etc.

For more info on REPL Server refer `Pymodbus REPL Server <https://github.com/pymodbus-dev/pymodbus/blob/dev/pymodbus/repl/server/README.md>`_

.. image:: https://img.youtube.com/vi/OutaVz0JkWg/maxresdefault.jpg
   :target: https://youtu.be/OutaVz0JkWg

------------------------------------------------------------
Installing
------------------------------------------------------------

You can install using pip or easy install by issuing the following
commands in a terminal window (make sure you have correct
permissions or a virtualenv currently running):

    pip install -U pymodbus

This will install a base version of pymodbus.

To install pymodbus with options run:

    pip install -U pymodbus[<option>,...]

Available options are:

- **repl**, installs pymodbus REPL.

- **serial**, installs serial drivers.

- **documentation**, installs tools to generate documentation.

- **development**, installs development tools needed to enable test/check of pymodbus changes.


Or to install a specific release:

    pip install -U pymodbus==X.Y.Z

Otherwise you can pull the trunk source and install from there::

    git clone git://github.com/pymodbus-dev/pymodbus.git
    cd pymodbus
    pip install -r requirements.txt

Before cloning the repo, you need to install python3 (preferable 3.10)
and make a virtual environment::

   python3 -m venv /path/to/new/virtual/environment

To activeate the virtual environment please do::

   source .venv/bin/activate


To get latest release (for now v3.0.0 with Python 3.8 support)::

    git checkout master

To get bleeding edge::

    git checkout dev

To get a specific version:

    git checkout tags/vX.Y.Z -b vX.Y.Z

Then:

   pip install -r requirements.txt

   pip install -e .

   pre-commit --install

This installs pymodbus in your virtual environment with pointers directly to the pymodbus directory, so any change you make is immediately available as if installed.  It will also install `pre-commit` git hooks.

Either method will install all the required dependencies
(at their appropriate versions) for your current python distribution.


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

  * Fixing bugs/feature requests
  * Architecture documentation
  * Functional testing against any reference we can find
  * The remaining edges of the protocol (that we think no one uses)

------------------------------------------------------------
Development Instructions
------------------------------------------------------------
The current code base is compatible python >= 3.8.
Here are some of the common commands to perform a range of activities

   pip install -r requirements.txt   install all requirements

   pip install -e .                  source directory is "release", useful for testing

   ./check_ci                        run the same checks as CI runs on a pull request.

   OBS: tox is no longer supported.

------------------------------------------------------------
Generate documentation
------------------------------------------------------------

   cd doc
   make clean
   make html

------------------------------------------------------------
Contributing
------------------------------------------------------------
Just fork the repo and raise your PR against `dev` branch.

We always have more work than time, so feel free to open a discussion / issue on a theme you want to solve.

------------------------------------------------------------
License Information
------------------------------------------------------------

Pymodbus is built on top of code developed from/by:
  * Copyright (c) 2001-2005 S.W.A.C. GmbH, Germany.
  * Copyright (c) 2001-2005 S.W.A.C. Bohemia s.r.o., Czech Republic.

  * Hynek Petrak, https://github.com/HynekPetrak

Released under the `BSD License <LICENSE>`_
