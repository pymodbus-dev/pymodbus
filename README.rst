PyModbus - A Python Modbus Stack
================================
.. image:: https://github.com/pymodbus-dev/pymodbus/actions/workflows/ci.yml/badge.svg?branch=dev
   :target: https://github.com/pymodbus-dev/pymodbus/actions/workflows/ci.yml
.. image:: https://readthedocs.org/projects/pymodbus/badge/?version=latest
   :target: https://pymodbus.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. image:: https://pepy.tech/badge/pymodbus
   :target: https://pepy.tech/project/pymodbus
   :alt: Downloads

Pymodbus is a full Modbus protocol implementation offering client/server with synchronous/asynchronous API a well as simulators.

Current release is `3.6.6 <https://github.com/pymodbus-dev/pymodbus/releases/tag/v3.6.6>`_.

Bleeding edge (not released) is `dev <https://github.com/pymodbus-dev/pymodbus/tree/dev>`_.

All changes are described in `release notes <https://pymodbus.readthedocs.io/en/latest/source/changelog.html>`_
and all API changes are `documented <https://pymodbus.readthedocs.io/en/latest/source/api_changes.html>`_

A big thanks to all the `volunteers <https://pymodbus.readthedocs.io/en/latest/source/authors.html>`_ that helps make pymodbus a great project.

Source code on `github <https://pymodbus.readthedocs.io/en/latest/source/authors.html>`_

Pymodbus in a nutshell
----------------------
Pymodbus consist of 5 parts:

- **client**, connect to your favorite device(s)
- **server**, simulate your favorite device(s)
- **repl**, a commandline text based client/server simulator
- **simulator**, an html based server simulator
- **examples**, showing both simple and advances usage

Common features
^^^^^^^^^^^^^^^
* Full modbus standard protocol implementation
* Support for custom function codes
* support serial (rs-485), tcp, tls and udp communication
* support all standard frames: socket, rtu, rtu-over-tcp, tcp and ascii
* does not have third party dependencies, apart from pyserial (optional)
* very lightweight project
* requires Python >= 3.8
* thorough test suite, that test all corners of the library
* automatically tested on Windows, Linux and MacOS combined with python 3.8 - 3.12
* strongly typed API (py.typed present)

The modbus protocol specification: Modbus_Application_Protocol_V1_1b3.pdf can be found on
`modbus org <https://modbus.org>`_


Client Features
^^^^^^^^^^^^^^^
* asynchronous API and synchronous API for applications
* very simple setup and call sequence (just 6 lines of code)
* utilities to convert int/float to/from multiple registers
* payload builder/decoder to help with complex data

`Client documentation <https://pymodbus.readthedocs.io/en/latest/source/client.html>`_


Server Features
^^^^^^^^^^^^^^^
* asynchronous implementation for high performance
* synchronous API classes for convenience
* simulate real life devices
* full server control context (device information, counters, etc)
* different backend datastores to manage register values
* callback to intercept requests/responses
* work on RS485 in parallel with other devices

`Server documentation <https://pymodbus.readthedocs.io/en/latest/source/library/server.html>`_


REPL Features
^^^^^^^^^^^^^
- server/client commandline emulator
- easy test of real device (client)
- easy test of client app (server)
- simulation of broken requests/responses
- simulation of error responses (hard to provoke in real devices)

`REPL documentation <https://github.com/pymodbus-dev/repl>`_


Simulator Features
^^^^^^^^^^^^^^^^^^
- server simulator with WEB interface
- configure the structure of a real device
- monitor traffic online
- allow distributed team members to work on a virtual device using internet
- simulation of broken requests/responses
- simulation of error responses (hard to provoke in real devices)

`Simulator documentation <https://pymodbus.readthedocs.io/en/dev/source/simulator.html>`_

Use Cases
---------
The client is the most typically used. It is embedded into applications,
where it abstract the modbus protocol from the application by providing an
easy to use API. The client is integrated into some well known projects like
`home-assistant <https://www.home-assistant.io>`_.

Although most system administrators will find little need for a Modbus
server, the server is handy to verify the functionality of an application.

The simulator and/or server is often used to simulate real life devices testing
applications. The server is excellent to perform high volume testing (e.g.
houndreds of devices connected to the application). The advantage of the server is
that it runs not only a "normal" computers but also on small ones like Raspberry PI.

Since the library is written in python, it allows for easy scripting and/or integration into their existing
solutions.

For more information please browse the project documentation:

https://readthedocs.org/docs/pymodbus/en/latest/index.html



Install
-------
The library is available on pypi.org and github.com to install with

- :code:`pip` for those who just want to use the library
- :code:`git clone` for those who wants to help or just are curious

Be aware that there are a number of project, who have forked pymodbus and

- seems just to provide a version frozen in time
- extended pymodbus with extra functionality

The latter is not because we rejected the extra functionality (we welcome all changes),
but because the codeowners made that decision.

In both cases, please understand, we cannot offer support to users of these projects as we do not known
what have been changed nor what status the forked code have.

A growing number of Linux distributions include pymodbus in their standard installation.

You need to have python3 installed, preferable 3.11.

Install with pip
^^^^^^^^^^^^^^^^
You can install using pip by issuing the following
commands in a terminal window::

   pip install pymodbus

If you want to use the serial interface::

   pip install pymodbus[serial]

This will install pymodbus with the pyserial dependency.

Pymodbus offers a number of extra options:

- **repl**, needed by pymodbus.repl
- **serial**, needed for serial communication
- **simulator**, needed by pymodbus.simulator
- **documentation**, needed to generate documentation
- **development**, needed for development
- **all**, installs all of the above

which can be installed as::

   pip install pymodbus[<option>,...]

It is possible to install old releases if needed::

   pip install pymodbus==3.5.4


Install with github
^^^^^^^^^^^^^^^^^^^
On github, fork https://github.com/pymodbus-dev/pymodbus.git

Clone the source, and make a virtual environment::


   git clone git://github.com/<your account>/pymodbus.git
   cd pymodbus
   python3 -m venv .venv

Activate the virtual environment, this command needs repeated in every new terminal::

   source .venv/bin/activate

To get a specific release::

   git checkout v3.5.2

or the bleeding edge::

   git checkout dev

Some distributions have an old pip, which needs to be upgraded:

   pip install --upgrade pip

Install required development tools::

   pip install ".[development]"

Install all (allows creation of documentation etc):

   pip install ".[all]"

Install git hooks, that helps control the commit and avoid errors when submitting a Pull Request:

  cp githooks/* .git/hooks

This installs dependencies in your virtual environment
with pointers directly to the pymodbus directory,
so any change you make is immediately available as if installed.

The repository contains a number of important branches and tags.
  * **dev** is where all development happens, this branch is not always stable.
  * **master** is where are releases are kept.
  * **vX.Y.Z** (e.g. v2.5.3) is a specific release


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

For more advanced examples, check out `Examples <https://pymodbus.readthedocs.io/en/dev/source/examples.html>`_ included in the
repository. If you have created any utilities that meet a specific
need, feel free to submit them so others can benefit.

Also, if you have a question, please `create a post in discussions q&a topic <https://github.com/pymodbus-dev/pymodbus/discussions/new?category=q-a>`_,
so that others can benefit from the results.

If you think, that something in the code is broken/not running well, please `open an issue <https://github.com/pymodbus-dev/pymodbus/issues/new>`_,
read the Template-text first and then post your issue with your setup information.

`Example documentation <https://pymodbus.readthedocs.io/en/dev/source/examples.html>`_


Contributing
------------
Just fork the repo and raise your Pull Request against :code:`dev` branch.

We always have more work than time, so feel free to open a discussion / issue on a theme you want to solve.

If your company would like your device tested or have a cloud based device
simulation, feel free to contact us.
We are happy to help your company solve your modbus challenges.

That said, the current work mainly involves polishing the library and
solving issues:

* Fixing bugs/feature requests
* Architecture documentation
* Functional testing against any reference we can find

There are 2 bigger projects ongoing:

   * rewriting the internal part of all clients (both sync and async)
   * Add features to and simulator, and enhance the web design


Development instructions
------------------------
The current code base is compatible with python >= 3.8.

Here are some of the common commands to perform a range of activities::

   source .venv/bin/activate   <-- Activate the virtual environment
   ./check_ci.sh               <-- run the same checks as CI runs on a pull request.


Make a pull request::

   git checkout dev          <-- activate development branch
   git pull                  <-- update branch with newest changes
   git checkout -b feature   <-- make new branch for pull request
   ... make source changes
   git commit                <-- commit change to git
   git push                  <-- push to your account on github

   on github open a pull request, check that CI turns green and then wait for review comments.

Test your changes::

   cd test
   pytest

you can also do extended testing::

   pytest --cov         <-- Coverage html report in build/html
   pytest --profile     <-- Call profile report in prof

Internals
^^^^^^^^^

There are no documentation of the architecture (help is welcome), but most classes and
methods are documented:

`Pymodbus internals <https://pymodbus.readthedocs.io/en/dev/source/internals.html>`_


Generate documentation
^^^^^^^^^^^^^^^^^^^^^^

**Remark** Assumes that you have installed documentation tools:;

   pip install ".[documentation]"

to build do::

   cd doc
   ./build_html

The documentation is available in <root>/build/html

Remark: this generates a new zip/tgz file of examples which are uploaded.


License Information
-------------------

Released under the `BSD License <https://github.com/pymodbus-dev/pymodbus/blob/dev/LICENSE>`_
