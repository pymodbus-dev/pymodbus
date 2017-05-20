.. image:: https://travis-ci.org/riptideio/pymodbus.svg?branch=master
   :target: https://travis-ci.org/riptideio/pymodbus
============================================================
Summary
============================================================

Pymodbus is a full Modbus protocol implementation using twisted for its
asynchronous communications core.  It can also be used without any third
party dependencies (aside from pyserial) if a more lightweight project is
needed.  Furthermore, it should work fine under any python version > 2.3
with a python 3.0 branch currently being maintained as well.

============================================================
Features
============================================================

------------------------------------------------------------
Client Features
------------------------------------------------------------

  * Full read/write protocol on discrete and register
  * Most of the extended protocol (diagnostic/file/pipe/setting/information)
  * TCP, UDP, Serial ASCII, Serial RTU, and Serial Binary
  * asynchronous(powered by twisted) and synchronous versions
  * Payload builder/decoder utilities

------------------------------------------------------------
Server Features
------------------------------------------------------------

  * Can function as a fully implemented modbus server
  * TCP, UDP, Serial ASCII, Serial RTU, and Serial Binary
  * asynchronous(powered by twisted) and synchronous versions
  * Full server control context (device information, counters, etc)
  * A number of backing contexts (database, redis, a slave device)

============================================================
Use Cases
============================================================

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
    print result.bits[0]
    client.close()

For more advanced examples, check out the examples included in the
respository. If you have created any utilities that meet a specific
need, feel free to submit them so others can benefit.

Also, if you have questions, please ask them on the mailing list
so that others can benefit from the results and so that I can
trace them. I get a lot of email and sometimes these requests
get lost in the noise: http://groups.google.com/group/pymodbus or 
at gitter:  https://gitter.im/pymodbus_dev/Lobby

------------------------------------------------------------
Installing
------------------------------------------------------------

You can install using pip or easy install by issuing the following
commands in a terminal window (make sure you have correct
permissions or a virtualenv currently running)::

    easy_install -U pymodbus
    pip install  -U pymodbus

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

  * Add CI support
  * Make PEP-8 compatible and flake8 ready
  * Fixing bugs/feature requests
  * Architecture documentation
  * Functional testing against any reference I can find
  * The remaining edges of the protocol (that I think no one uses)

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
License Information
------------------------------------------------------------

Pymodbus is built on top of code developed from/by:
  * Copyright (c) 2001-2005 S.W.A.C. GmbH, Germany.
  * Copyright (c) 2001-2005 S.W.A.C. Bohemia s.r.o., Czech Republic.

  * Hynek Petrak, https://github.com/HynekPetrak
  * Twisted Matrix

Released under the BSD License
