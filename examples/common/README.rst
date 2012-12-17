============================================================
Modbus Implementations
============================================================

There are a few reference implementations that you can use
to test modbus serial

------------------------------------------------------------
pymodbus
------------------------------------------------------------

You can use pymodbus as a testing server by simply modifying
one of the run scripts supplied here. There is an
asynchronous version and a synchronous version (that really
differ in how mnay dependencies you are willing to have).
Regardless of which one you choose, they can be started
quite easily::

    ./asynchronous-server.py
    ./synchronous-server.py

Currently, each version has implementations of the following:

- modbus tcp
- modbus udp
- modbus udp binary
- modbus ascii serial
- modbus ascii rtu

------------------------------------------------------------
Modbus Driver
------------------------------------------------------------

Included are reference implementations of a modbus client
and server using the modbus driver library (as well as
the relevant source code). Both programs have a wealth of
options and can be used to test either side of your
application::

    tools/reference/diagslave -h # (server)
    tools/reference/modpoll -h # (client)

------------------------------------------------------------
jamod
------------------------------------------------------------

Jamod is a complete modbus implementation for the java jvm.
Included are a few simple reference servers using the
library, however, a great deal more can be produced using
it. I have not tested it, however, it may even be possible
to use this library in conjunction with jython to interop
between your python code and this library:

* http://jamod.sourceforge.net/

------------------------------------------------------------
nmodbus
------------------------------------------------------------

Although there is not any code included in this package,
nmodbus is a complete implementation of the modbus protocol
for the .net clr. The site has a number of examples that can
be tuned for your testing needs:

* http://code.google.com/p/nmodbus/

============================================================
Serial Loopback Testing
============================================================

In order to test the serial implementations, one needs to
create a loopback connection (virtual serial port). This can
be done in a number of ways.

------------------------------------------------------------
Linux
------------------------------------------------------------

For linux, there are three ways that are included with this
distribution.

One is to use the socat utility. The following will get one
going quickly::

    sudo apt-get install socat
    sudo socat PTY,link=/dev/pts/13, PTY,link=/dev/pts/14
    # connect the master to /dev/pts/13
    # connect the client to /dev/pts/14

Next, you can include the loopback kernel driver included in
the tools/nullmodem/linux directory::

    sudo ./run

------------------------------------------------------------
Windows
------------------------------------------------------------

For Windows, simply use the com2com application that is in
the directory tools/nullmodem/windows. Instructions are
included in the Readme.txt.

------------------------------------------------------------
Generic
------------------------------------------------------------

For most unix based systems, there is a simple virtual serial
forwarding application in the tools/nullmodem/ directory::

    make run
    # connect the master to the master output
    # connect the client to the client output

Or for a tried and true method, simply connect a null modem
cable between two of your serial ports and then simply reference
those.
