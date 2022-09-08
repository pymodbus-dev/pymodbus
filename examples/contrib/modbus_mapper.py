# pylint: disable=missing-type-doc
"""This is used to generate decoder blocks.

so that non-programmers can define the
register values and then decode a modbus device all
without having to write a line of code for decoding.

Currently supported formats are:

* csv
* json
* xml

Here is an example of generating and using a mapping decoder
(note that this is still in the works and will be greatly
simplified in the final api; it is just an example of the
requested functionality)::

    CSV:
    address,type,size,name,function
    1,int16,2,Comm. count PLC,hr
    2,int16,2,Comm. count PLC,hr

    from modbus_mapper_updated import csv_mapping_parser
    from modbus_mapper_updated import mapping_decoder
    from pymodbus.client.sync import ModbusTcpClient
    from pymodbus.payload import BinaryPayloadDecoder
    from pymodbus.constants import Endian

    from pprint import pprint
    import logging

    FORMAT = "%(asctime)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
    logging.basicConfig(format=FORMAT)
    _logger = logging.getLogger()
    _logger.setLevel(logging.DEBUG)
    
    template = ["address", "type", "size", "name", "function"]

    raw_mapping = csv_mapping_parser("simple_mapping_client.csv", template)
    mapping = mapping_decoder(raw_mapping)
    
    client = ModbusTcpClient(host="localhost", port=5020)
    response = client.read_holding_registers(address=index, count=size)
    decoder = BinaryPayloadDecoder.fromRegisters(
        response.registers, byteorder=Endian.Big, wordorder=Endian.Big
    )

    for block in mapping.items():
        for mapping in block:
            if type(mapping) == dict:
                print( "[{}]\t{}".format(mapping["address"], mapping["type"]()(decoder)))



Also, using the same input mapping parsers, we can generate
populated slave contexts that can be run behind a modbus server::

    CSV:
    address,value,function,name,description
    1,100,hr,Comm. count PLC,Comm. count PLC
    2,200,hr,Comm. count PLC,Comm. count PLC

    from modbus_mapper_updated import csv_mapping_parser
    from modbus_mapper_updated import modbus_context_decoder

    from pymodbus.server.sync import StartTcpServer
    from pymodbus.datastore.context import ModbusServerContext
    from pymodbus.device import ModbusDeviceIdentification
    from pymodbus.version import version

    from pprint import pprint
    import logging

    FORMAT = "%(asctime)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
    logging.basicConfig(format=FORMAT)
    _logger = logging.getLogger()
    _logger.setLevel(logging.DEBUG)

    template = ["address", "value", "function", "name", "description"]
    raw_mapping = csv_mapping_parser("simple_mapping_server.csv", template)

    slave_context = modbus_context_decoder(raw_mapping)
    context = ModbusServerContext(slaves=slave_context, single=True)
    identity = ModbusDeviceIdentification(
        info_name={
            "VendorName": "Pymodbus",
            "ProductCode": "PM",
            "VendorUrl": "https://github.com/riptideio/pymodbus/",
            "ProductName": "Pymodbus Server",
            "ModelName": "Pymodbus Server",
            "MajorMinorRevision": version.short(),
        }
    )
    StartTcpServer(context=context, identity=identity, address=("localhost", 5020))

"""
from collections import defaultdict
import csv
from io import StringIO
import json
from tokenize import generate_tokens

from pymodbus.datastore.context import ModbusSlaveContext

from pymodbus.datastore import (
    ModbusSlaveContext,
    ModbusSparseDataBlock,
)

# --------------------------------------------------------------------------- #
# raw mapping input parsers
# --------------------------------------------------------------------------- #
# These generate the raw mapping_blocks from some form of input
# which can then be passed to the decoder in question to supply
# the requested output result.
# --------------------------------------------------------------------------- #


def csv_mapping_parser(path, template):
    """Given a csv file of the the mapping data for a modbus device,

    return a mapping layout that can be used to decode an new block.

    .. note:: For the template, a few values are required
    to be defined: address, size, function, and type. All the remaining
    values will be stored, but not formatted by the application.
    So for example::

        template = ["address", "type", "size", "name", "function"]
        mappings = json_mapping_parser("mapping.json", template)

    :param path: The path to the csv input file
    :param template: The row value template
    :returns: The decoded csv dictionary
    """
    mapping_blocks = defaultdict(dict)
    with open(path, "r") as handle:  # pylint: disable=unspecified-encoding
        reader = csv.reader(handle)
        next(reader)  # skip the csv header
        for row in reader:
            mapping = dict(zip(template, row))
            # mapping.pop("function")
            aid = mapping["address"]
            mapping_blocks[aid] = mapping
    return mapping_blocks


def json_mapping_parser(path, template):
    """Given a json file of the the mapping data for a modbus device,

    return a mapping layout that can
    be used to decode an new block.

    .. note:: For the template, a few values are required
    to be mapped: address, size, and type. All the remaining
    values will be stored, but not formatted by the application.
    So for example::

        template = {
            "Start": "address",
            "DataType": "type",
            "Length": "size"
            # the remaining keys will just pass through
        }
        mappings = json_mapping_parser("mapping.json", template)

    :param path: The path to the csv input file
    :param template: The row value template
    :returns: The decoded csv dictionary
    """
    mapping_blocks = {}
    with open(path, "r") as handle:  # pylint: disable=unspecified-encoding
        for tid, rows in json.load(handle).iteritems():
            mappings = {}
            for key, values in rows.iteritems():
                mapping = {template.get(k, k): v for k, v in values.iteritems()}
                mappings[int(key)] = mapping
            mapping_blocks[tid] = mappings
    return mapping_blocks


def xml_mapping_parser():
    """Given an xml file of the the mapping data for a modbus device,

    return a mapping layout that can be used to decode an new block.

    :returns: The decoded csv dictionary
    """


# --------------------------------------------------------------------------- #
# modbus context decoders
# --------------------------------------------------------------------------- #
# These are used to decode a raw mapping_block into a slave context with
# populated function data blocks.
# --------------------------------------------------------------------------- #
def modbus_context_decoder(mapping_blocks):
    """Generate a backing slave context with initialized data blocks.

    .. note:: This expects the following for each block:
    address, value, and function where function is one of
    di (discretes), co (coils), hr (holding registers), or
    ir (input registers).

    :param mapping_blocks: The mapping blocks
    :returns: The initialized modbus slave context
    """
    sparse = ModbusSparseDataBlock()
    sparse.create()
    for block in mapping_blocks.items():
        for mapping in block:
            if type(mapping) == dict:
                value = mapping["value"]
                address = mapping["address"]
                sparse.setValues(address=int(address), values=int(value))
    return ModbusSlaveContext(di=sparse, co=sparse, hr=sparse, ir=sparse)


# --------------------------------------------------------------------------- #
# modbus mapping decoder
# --------------------------------------------------------------------------- #
# These are used to decode a raw mapping_block into a request decoder.
# So this allows one to simply grab a number of registers, and then
# pass them to this decoder which will do the rest.
# --------------------------------------------------------------------------- #
class ModbusTypeDecoder:
    """This is a utility to determine the correct decoder to use given a type name.

    By default this supports all the types available in the default modbus
    decoder, however this can easily be extended this class
    and adding new types to the mapper::

        class CustomTypeDecoder(ModbusTypeDecoder):
            def __init__(self):
                ModbusTypeDecode.__init__(self)
                self.mapper["type-token"] = self.callback

            def parse_my_bitfield(self, tokens):
                return lambda d: d.decode_my_type()

    """

    def __init__(self):
        """Initialize a new instance of the decoder"""
        self.default = lambda m: self.parse_16bit_uint
        self.parsers = {
            "uint": self.parse_16bit_uint,
            "uint8": self.parse_8bit_uint,
            "uint16": self.parse_16bit_uint,
            "uint32": self.parse_32bit_uint,
            "uint64": self.parse_64bit_uint,
            "int": self.parse_16bit_int,
            "int8": self.parse_8bit_int,
            "int16": self.parse_16bit_int,
            "int32": self.parse_32bit_int,
            "int64": self.parse_64bit_int,
            "float": self.parse_32bit_float,
            "float32": self.parse_32bit_float,
            "float64": self.parse_64bit_float,
            "string": self.parse_32bit_int,
            "bits": self.parse_bits,
        }

    # ------------------------------------------------------------ #
    # Type parsers
    # ------------------------------------------------------------ #
    @staticmethod
    def parse_string(tokens):
        """Parse value."""
        _ = next(tokens)
        size = int(next(tokens))
        return lambda d: d.decode_string(size=size)

    @staticmethod
    def parse_bits():
        """Parse value."""
        return lambda d: d.decode_bits()

    @staticmethod
    def parse_8bit_uint():
        """Parse value."""
        return lambda d: d.decode_8bit_uint()

    @staticmethod
    def parse_16bit_uint():
        """Parse value."""
        return lambda d: d.decode_16bit_uint()

    @staticmethod
    def parse_32bit_uint():
        """Parse value."""
        return lambda d: d.decode_32bit_uint()

    @staticmethod
    def parse_64bit_uint():
        """Parse value."""
        return lambda d: d.decode_64bit_uint()

    @staticmethod
    def parse_8bit_int():
        """Parse value."""
        return lambda d: d.decode_8bit_int()

    @staticmethod
    def parse_16bit_int():
        """Parse value."""
        return lambda d: d.decode_16bit_int()

    @staticmethod
    def parse_32bit_int():
        """Parse value."""
        return lambda d: d.decode_32bit_int()

    @staticmethod
    def parse_64bit_int():
        """Parse value."""
        return lambda d: d.decode_64bit_int()

    @staticmethod
    def parse_32bit_float():
        """Parse value."""
        return lambda d: d.decode_32bit_float()

    @staticmethod
    def parse_64bit_float():
        """Parse value."""
        return lambda d: d.decode_64bit_float()

    # ------------------------------------------------------------
    # Public Interface
    # ------------------------------------------------------------
    def tokenize(self, value):
        """Return the tokens

        :param value: The value to tokenize
        :returns: A token generator
        """
        tokens = generate_tokens(StringIO(value).readline)
        for _, tokval, _, _, _ in tokens:
            yield tokval

    def parse(self, value):
        """Return a function that supplied with a decoder,

        will decode the correct value.

        :param value: The type of value to parse
        :returns: The decoder method to use
        """
        tokens = self.tokenize(value)
        token = next(tokens).lower()  # pylint: disable=no-member
        parser = self.parsers.get(token, self.default)
        return parser


def mapping_decoder(mapping_blocks, decoder=None):
    """Convert them into modbus value decoder map.

    :param mapping_blocks: The mapping blocks
    :param decoder: The type decoder to use
    """
    decoder = decoder or ModbusTypeDecoder()
    map = defaultdict(dict)
    for block in mapping_blocks.items():
        for mapping in block:
            if type(mapping) == dict:
                mapping["address"] = mapping["address"]
                mapping["size"] = mapping["size"]
                mapping["type"] = decoder.parse(mapping["type"])
        map[mapping["address"]] = mapping
    return map