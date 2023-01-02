#!/usr/bin/env python3
# pylint: disable=missing-type-doc,missing-param-doc,differing-param-doc,missing-raises-doc
"""Libmodbus Protocol Wrapper.

What follows is an example wrapper of the libmodbus library
(https://libmodbus.org/documentation/) for use with pymodbus.
There are two utilities involved here:

* LibmodbusLevel1Client

  This is simply a python wrapper around the c library. It is
  mostly a clone of the pylibmodbus implementation, but I plan
  on extending it to implement all the available protocol using
  the raw execute methods.

* LibmodbusClient

  This is just another modbus client that can be used just like
  any other client in pymodbus.

For these to work, you must have `cffi` and `libmodbus-dev` installed:

    sudo apt-get install libmodbus-dev
    pip install cffi
"""
# -------------------------------------------------------------------------- #
# import system libraries
# -------------------------------------------------------------------------- #
from cffi import FFI  # pylint: disable=import-error

from pymodbus.bit_read_message import (
    ReadCoilsResponse,
    ReadDiscreteInputsResponse,
)
from pymodbus.bit_write_message import (
    WriteMultipleCoilsResponse,
    WriteSingleCoilResponse,
)
from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.constants import Defaults
from pymodbus.exceptions import ModbusException
from pymodbus.register_read_message import (
    ReadHoldingRegistersResponse,
    ReadInputRegistersResponse,
    ReadWriteMultipleRegistersResponse,
)
from pymodbus.register_write_message import (
    WriteMultipleRegistersResponse,
    WriteSingleRegisterResponse,
)


# -------------------------------------------------------------------------- #
# import pymodbus libraries
# -------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# create the C interface
# --------------------------------------------------------------------------- #
# * TODO add the protocol needed for the servers
# --------------------------------------------------------------------------- #

compiler = FFI()
compiler.cdef(
    """
    typedef struct _modbus modbus_t;

    int modbus_connect(modbus_t *ctx);
    int modbus_flush(modbus_t *ctx);
    void modbus_close(modbus_t *ctx);

    const char *modbus_strerror(int errnum);
    int modbus_set_slave(modbus_t *ctx, int slave);

    void modbus_get_response_timeout(modbus_t *ctx, uint32_t *to_sec, uint32_t *to_usec);
    void modbus_set_response_timeout(modbus_t *ctx, uint32_t to_sec, uint32_t to_usec);

    int modbus_read_bits(modbus_t *ctx, int addr, int nb, uint8_t *dest);
    int modbus_read_input_bits(modbus_t *ctx, int addr, int nb, uint8_t *dest);
    int modbus_read_registers(modbus_t *ctx, int addr, int nb, uint16_t *dest);
    int modbus_read_input_registers(modbus_t *ctx, int addr, int nb, uint16_t *dest);

    int modbus_write_bit(modbus_t *ctx, int coil_addr, int status);
    int modbus_write_bits(modbus_t *ctx, int addr, int nb, const uint8_t *data);
    int modbus_write_register(modbus_t *ctx, int reg_addr, int value);
    int modbus_write_registers(modbus_t *ctx, int addr, int nb, const uint16_t *data);
    int modbus_write_and_read_registers(modbus_t *ctx, int write_addr, int write_nb,
                                        const uint16_t *src, int read_addr, int read_nb, uint16_t *dest);

    int modbus_mask_write_register(modbus_t *ctx, int addr, uint16_t and_mask, uint16_t or_mask);
    int modbus_send_raw_request(modbus_t *ctx, uint8_t *raw_req, int raw_req_length);

    float modbus_get_float(const uint16_t *src);
    void modbus_set_float(float f, uint16_t *dest);

    modbus_t* modbus_new_tcp(const char *ip_address, int port);
    modbus_t* modbus_new_rtu(const char *device, int baud, char parity, int data_bit, int stop_bit);
    void modbus_free(modbus_t *ctx);

    int modbus_receive(modbus_t *ctx, uint8_t *req);
    int modbus_receive_from(modbus_t *ctx, int sockfd, uint8_t *req);
    int modbus_receive_confirmation(modbus_t *ctx, uint8_t *rsp);
"""
)
LIB = compiler.dlopen("modbus")  # create our bindings

# -------------------------------------------------------------------------- #
# helper utilities
# -------------------------------------------------------------------------- #


def get_float(data):
    """Get float."""
    return LIB.modbus_get_float(data)


def set_float(value, data):
    """Set float."""
    LIB.modbus_set_float(value, data)


def cast_to_int16(data):
    """Cast to int16."""
    return int(compiler.cast("int16_t", data))


def cast_to_int32(data):
    """Cast to int32."""
    return int(compiler.cast("int32_t", data))


class NotImplementedException(Exception):
    """Not implemented exception."""


# -------------------------------------------------------------------------- #
# level1 client
# -------------------------------------------------------------------------- #


class LibmodbusLevel1Client:
    """A raw wrapper around the libmodbus c library.

    Feel free to use it if you want increased performance and don't mind the
    entire protocol not being implemented.
    """

    @classmethod
    def create_tcp_client(cls, my_host="127.0.0.1", my_port=Defaults.TcpPort):
        """Create a TCP modbus client for the supplied parameters.

        :param host: The host to connect to
        :param port: The port to connect to on that host
        :returns: A new level1 client
        """
        my_client = LIB.modbus_new_tcp(my_host.encode(), my_port)
        return cls(my_client)

    @classmethod
    def create_rtu_client(cls, **kwargs):
        """Create a TCP modbus client for the supplied parameters.

        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :returns: A new level1 client
        """
        my_port = kwargs.get("port", "/dev/ttyS0")
        baudrate = kwargs.get("baud", Defaults.Baudrate)
        parity = kwargs.get("parity", Defaults.Parity)
        bytesize = kwargs.get("bytesize", Defaults.Bytesize)
        stopbits = kwargs.get("stopbits", Defaults.Stopbits)
        my_client = LIB.modbus_new_rtu(my_port, baudrate, parity, bytesize, stopbits)
        return cls(my_client)

    def __init__(self, my_client):
        """Initialize a new instance of the LibmodbusLevel1Client.

        This method should not be used, instead new instances should be created
        using the two supplied factory methods:

        * LibmodbusLevel1Client.create_rtu_client(...)
        * LibmodbusLevel1Client.create_tcp_client(...)

        :param client: The underlying client instance to operate with.
        """
        self.client = my_client
        self.slave = Defaults.Slave

    def set_slave(self, slave):
        """Set the current slave to operate against.

        :param slave: The new slave to operate against
        :returns: The resulting slave to operate against
        """
        self.slave = self._execute(  # pylint: disable=no-member
            LIB.modbus_set_slave, slave
        )
        return self.slave

    def connect(self):
        """Attempt to connect to the client target.

        :returns: True if successful, throws otherwise
        """
        return not self.__execute(LIB.modbus_connect)

    def flush(self):
        """Discard the existing bytes on the wire.

        :returns: The number of flushed bytes, or throws
        """
        return self.__execute(LIB.modbus_flush)

    def close(self):
        """Close and frees the underlying connection and context structure.

        :returns: Always True
        """
        LIB.modbus_close(self.client)
        LIB.modbus_free(self.client)
        return True

    def __execute(self, command, *args):
        """Run the supplied command against the currently instantiated client with the supplied arguments.

        This will make sure to correctly handle resulting errors.

        :param command: The command to execute against the context
        :param *args: The arguments for the given command
        :returns: The result of the operation unless -1 which throws
        """
        if (result := command(self.client, *args)) == -1:
            message = LIB.modbus_strerror(compiler.errno)
            raise ModbusException(compiler.string(message))
        return result

    def read_bits(self, address, count=1):
        """Read bits.

        :param address: The starting address to read from
        :param count: The number of coils to read
        :returns: The resulting bits
        """
        result = compiler.new("uint8_t[]", count)
        self.__execute(LIB.modbus_read_bits, address, count, result)
        return result

    def read_input_bits(self, address, count=1):
        """Read input bits.

        :param address: The starting address to read from
        :param count: The number of discretes to read
        :returns: The resulting bits
        """
        result = compiler.new("uint8_t[]", count)
        self.__execute(LIB.modbus_read_input_bits, address, count, result)
        return result

    def write_bit(self, address, value):
        """Write bit.

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :returns: The number of written bits
        """
        return self.__execute(LIB.modbus_write_bit, address, value)

    def write_bits(self, address, values):
        """Write bits.

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :returns: The number of written bits
        """
        count = len(values)
        return self.__execute(LIB.modbus_write_bits, address, count, values)

    def write_register(self, address, value):
        """Write register.

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :returns: The number of written registers
        """
        return self.__execute(LIB.modbus_write_register, address, value)

    def write_registers(self, address, values):
        """Write registers.

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :returns: The number of written registers
        """
        count = len(values)
        return self.__execute(LIB.modbus_write_registers, address, count, values)

    def read_registers(self, address, count=1):
        """Read registers.

        :param address: The starting address to read from
        :param count: The number of registers to read
        :returns: The resulting read registers
        """
        result = compiler.new("uint16_t[]", count)
        self.__execute(LIB.modbus_read_registers, address, count, result)
        return result

    def read_input_registers(self, address, count=1):
        """Read input registers.

        :param address: The starting address to read from
        :param count: The number of registers to read
        :returns: The resulting read registers
        """
        result = compiler.new("uint16_t[]", count)
        self.__execute(LIB.modbus_read_input_registers, address, count, result)
        return result

    def read_and_write_registers(
        self, read_address, read_count, write_address, write_registers
    ):
        """Read/write registers.

        :param read_address: The address to start reading from
        :param read_count: The number of registers to read from address
        :param write_address: The address to start writing to
        :param write_registers: The registers to write to the specified address
        :returns: The resulting read registers
        """
        write_count = len(write_registers)
        read_result = compiler.new("uint16_t[]", read_count)
        self.__execute(
            LIB.modbus_write_and_read_registers,
            write_address,
            write_count,
            write_registers,
            read_address,
            read_count,
            read_result,
        )
        return read_result


# -------------------------------------------------------------------------- #
# level2 client
# -------------------------------------------------------------------------- #


class LibmodbusClient(ModbusClientMixin):
    """A facade around the raw level 1 libmodbus client.

    that implements the pymodbus protocol on top of the lower level client.
    """

    # ----------------------------------------------------------------------- #
    # these are used to convert from the pymodbus request types to the
    # libmodbus operations (overloaded operator).
    # ----------------------------------------------------------------------- #

    __methods = {
        "ReadCoilsRequest": lambda c, r: c.read_bits(r.address, r.count),
        "ReadDiscreteInputsRequest": lambda c, r: c.read_input_bits(r.address, r.count),
        "WriteSingleCoilRequest": lambda c, r: c.write_bit(r.address, r.value),
        "WriteMultipleCoilsRequest": lambda c, r: c.write_bits(r.address, r.values),
        "WriteSingleRegisterRequest": lambda c, r: c.write_register(r.address, r.value),
        "WriteMultipleRegistersRequest": lambda c, r: c.write_registers(
            r.address, r.values
        ),
        "ReadHoldingRegistersRequest": lambda c, r: c.read_registers(
            r.address, r.count
        ),
        "ReadInputRegistersRequest": lambda c, r: c.read_input_registers(
            r.address, r.count
        ),
        "ReadWriteMultipleRegistersRequest": lambda c, r: c.read_and_write_registers(
            r.read_address, r.read_count, r.write_address, r.write_registers
        ),
    }

    # ----------------------------------------------------------------------- #
    # these are used to convert from the libmodbus result to the
    # pymodbus response type
    # ----------------------------------------------------------------------- #

    __adapters = {
        "ReadCoilsRequest": lambda tx, rx: ReadCoilsResponse(list(rx)),
        "ReadDiscreteInputsRequest": lambda tx, rx: ReadDiscreteInputsResponse(
            list(rx)
        ),
        "WriteSingleCoilRequest": lambda tx, rx: WriteSingleCoilResponse(
            tx.address, rx
        ),
        "WriteMultipleCoilsRequest": lambda tx, rx: WriteMultipleCoilsResponse(
            tx.address, rx
        ),
        "WriteSingleRegisterRequest": lambda tx, rx: WriteSingleRegisterResponse(
            tx.address, rx
        ),
        "WriteMultipleRegistersRequest": lambda tx, rx: WriteMultipleRegistersResponse(
            tx.address, rx
        ),
        "ReadHoldingRegistersRequest": lambda tx, rx: ReadHoldingRegistersResponse(
            list(rx)
        ),
        "ReadInputRegistersRequest": lambda tx, rx: ReadInputRegistersResponse(
            list(rx)
        ),
        "ReadWriteMultipleRegistersRequest": lambda tx, rx: ReadWriteMultipleRegistersResponse(
            list(rx)
        ),
    }

    def __init__(self, my_client):
        """Initialize a new instance of the LibmodbusClient.

        This should be initialized with one of the LibmodbusLevel1Client instances:

        * LibmodbusLevel1Client.create_rtu_client(...)
        * LibmodbusLevel1Client.create_tcp_client(...)
        :param client: The underlying client instance to operate with.
        """
        self.client = my_client

    # ----------------------------------------------------------------------- #
    # We use the client mixin to implement the api methods which are all
    # forwarded to this method. It is implemented using the previously
    # defined lookup tables. Any method not defined simply throws.
    # ----------------------------------------------------------------------- #

    def execute(self, request):
        """Execute the supplied request against the server.

        :param request: The request to process
        :returns: The result of the request execution
        """
        if self.client.slave != request.unit_id:
            self.client.set_slave(request.unit_id)

        method = request.__class__.__name__
        operation = self.__methods.get(method, None)
        adapter = self.__adapters.get(method, None)

        if not operation or not adapter:
            raise NotImplementedException("Method not implemented: " + operation)

        response = operation(self.client, request)
        return adapter(request, response)

    # ----------------------------------------------------------------------- #
    # Other methods can simply be forwarded using the decorator pattern
    # ----------------------------------------------------------------------- #

    def connect(self):
        """Connect."""
        return self.client.connect()

    def close(self):
        """Close."""
        return self.client.close()

    # ----------------------------------------------------------------------- #
    # magic methods
    # ----------------------------------------------------------------------- #

    def __enter__(self):
        """Implement the client with enter block

        :returns: The current instance of the client
        """
        self.client.connect()
        return self

    def __exit__(self, klass, value, traceback):
        """Implement the client with exit block"""
        self.client.close()


# -------------------------------------------------------------------------- #
# main example runner
# -------------------------------------------------------------------------- #


if __name__ == "__main__":

    # create our low level client
    host = "127.0.0.1"  # pylint: disable=invalid-name
    port = 502  # pylint: disable=invalid-name
    protocol = LibmodbusLevel1Client.create_tcp_client(host, port)

    # operate with our high level client
    with LibmodbusClient(protocol) as client:
        registers = client.write_registers(0, [13, 12, 11])
        print(registers)
        registers = client.read_holding_registers(0, 10)
        print(registers.registers)
