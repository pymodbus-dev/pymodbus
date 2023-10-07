PyModbus - A Python Modbus Stack
================================
Pymodbus is a full Modbus protocol implementation using a synchronous or asynchronous core.
The library consist of 4 parts:

- **client**, connect to your favorite device
- **server**, simulate your favorite device
- **repl**, a text based client/server simulator
- **simulator**, a html based server simulator

Pymodbus:

- implement the modbus standard protocol, with the possibility to add customizations.
- support serial (rs-485), tcp, tls and udp communication.
- support all standard frames: socket, rtu, rtu-over-tcp, tcp and ascii.
- can be used without any third party dependencies (aside from pyserial)
- is a very lightweight project.
- requires Python >= 3.8.
- provides a lot of ready to use examples.
- provides a server/client simulators.
- have a thorough test suite, that test all corners of the library.
- Tested automatically on Windows, Linux and MacOS with python 3.8 - 3.11

The modbus protocol documentation is available :download:`here <_static/Modbus_Application_Protocol_V1_1b3.pdf>`


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

Supported versions
------------------

Version `3.5.2 <https://github.com/pymodbus-dev/pymodbus/releases/tag/v3.5.2>`_ is the current release.

Each release is `documented <https://pymodbus.readthedocs.io/en/latest/source/changelog.html>`_

A big thanks to all the `volunteers <https://pymodbus.readthedocs.io/en/latest/source/authors.html>`_ that helped make pymodbus a great project.

.. important::
   All API changes after 3.0.0 are documented in `API_changes.rst <https://github.com/pymodbus-dev/pymodbus/blob/dev/CHANGELOG.rst>`_


Common features
---------------
  * Full modbus standard protocol implementation
  * Support for custom function codes
  * Most of the extended protocol (diagnostic/file/pipe/setting/information) also implemented
  * TCP, RTU-OVER-TCP, UDP, TLS, Serial ASCII and Serial RTU

Client Features
---------------
  * asynchronous and synchronous API for applications
  * Payload builder/decoder utilities
  * Pymodbus REPL for quick tests


Server Features
---------------
  * Simulate real life devices
  * asynchronous and synchronous versions
  * Full server control context (device information, counters, etc)
  * A number of backend datastores
  * Pymodbus REPL for quick tests
  * Pymodbus simulator for cloud based testing

Use Cases
---------
The client is the most typically used. It is embedded into applications,
where it abstract the modbus protocol from the application by providing an
easy to use API. The client is integrated into some well known projects like
`home-assistant <https://www.home-assistant.io>`_.

Although most system administrators will find little need for a Modbus
server on any modern hardware, they may find the need to query devices on
their network for status (PDU, PDR, UPS, etc). Since the library is written
in python, it allows for easy scripting and/or integration into their existing
solutions.

Continuing, most monitoring software needs to be stress tested against
hundreds or even thousands of devices (why this was originally written), but
getting access to that many is unwieldy at best.

The pymodbus server will allow a user to test as many devices as their
base operating system will allow.


For more information please browse the project documentation:

https://readthedocs.org/docs/pymodbus/en/latest/index.html


Example Code
------------
For those of you that just want to get started fast, here you go::

    from pymodbus.client import ModbusTcpClient

    client = ModbusTcpClient('MyDevice.lan')
    client.connect()
    client.write_coil(1, True)
    result = client.read_coils(1,1)
    print(result.bits[0])
    client.close()

We provide a couple of simple ready to go clients:

- `async client <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/simple_async_client.py>`_
- `sync client <https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/simple_sync_client.py>`_

For more advanced examples, check out the `Examples <https://pymodbus.readthedocs.io/en/dev/source/examples.html>`_ included in the
repository. If you have created any utilities that meet a specific
need, feel free to submit them so others can benefit.

::

   examples      -> Essential examples guaranteed to work (tested with our CI)
   ├── contrib   -> Examples contributed by contributors.


Also, if you have a question, please `create a post in discussions q&a topic <https://github.com/pymodbus-dev/pymodbus/discussions/new?category=q-a>`_,
so that others can benefit from the results.

If you think, that something in the code is broken/not running well, please `open an issue <https://github.com/pymodbus-dev/pymodbus/issues/new>`_,
read the Template-text first and then post your issue with your setup information.


Installing with pip
-------------------

You can install using pip or easy install by issuing the following
commands in a terminal window (make sure you have correct
permissions or a virtualenv currently running):

    pip install -U pymodbus

If you want to use the serial interface:

    pip install -U pymodbus[serial]

This will install pymodbus, r

To install pymodbus with options run:

    pip install -U pymodbus[<option>,...]

Available options are:

- **repl**, install dependencies needed by pymodbus.repl

- **serial**, installs serial drivers.

- **simulator**, install dependencies needed by pymodbus.simulator

- **documentation**, installs tools to generate documentation.

- **development**, installs development tools needed to enable test/check of pymodbus changes.

- **all**, installs all of the above


Installing with github
----------------------

Before cloning the repo, you need to install python3 (preferable 3.11)
and make and activate a virtual environment::

   python3 -m venv /path/to/new/virtual/environment

   source .venv/bin/activate

Clone the source and install from there::

    git clone git://github.com/pymodbus-dev/pymodbus.git
    cd pymodbus


To get a specific release::

    git checkout v3.5.2

To get bleeding edge::

    git checkout dev


Install required development tools::

   pip install -e ".[development]"

   pre-commit install

This installs pymodbus in your virtual environment
with pointers directly to the pymodbus directory,
so any change you make is immediately available as if installed.
It will also install `pre-commit` git hooks.

The repository contains a number of important branches and tags.
  * **dev** is where all development happens, this branch is not always stable.
  * **master** is where are releases are kept.
  * All releases are tagged with **vX.Y.Z** (e.g. v2.5.3)

If a maintenance release of an old version is needed (e.g. v2.5.4),
the release tag is used to create a branch with the same name,
and maintenance development is merged here.


Current Work In Progress
------------------------
The maintenance team is very small with limited capacity
and few modbus devices.

If your company would like your device tested or have a cloud based device
simulation, feel free to contact us.
We are happy to help your company solve your modbus challenges.

That said, the current work mainly involves polishing the library and
solving issues:

  * Fixing bugs/feature requests
  * Architecture documentation
  * Functional testing against any reference we can find
  * The remaining edges of the protocol (that we think no one uses)

There are 2 bigger projects ongoing:

  * rewriting the internal part of all clients (both sync and async)
  * Make the simulator datastore THE datastore


Development Instructions
------------------------
The current code base is compatible python >= 3.8.
Here are some of the common commands to perform a range of activities

   ./check_ci.sh                     run the same checks as CI runs on a pull request.


Generate documentation
----------------------

**Remark** Assumes that you have installed documentation tools:

   pip install -e ".[documentation]"

to build do:

   cd doc
   ./build_html

The documentation is available in <root>/build/html/html


Contributing
------------
Just fork the repo and raise your PR against `dev` branch.

We always have more work than time, so feel free to open a discussion / issue on a theme you want to solve.


License Information
-------------------

Released under the `BSD License <LICENSE>`_
