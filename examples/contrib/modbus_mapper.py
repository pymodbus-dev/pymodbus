"""
Given a modbus mapping file, this is used to generate
decoder blocks so that non-programmers can define the
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

    from modbus_mapper import csv_mapping_parser
    from modbus_mapper import mapping_decoder
    from pymodbus.client.sync import ModbusTcpClient
    from pymodbus.payload import BinaryModbusDecoder

    template = ['address', 'size', 'function', 'name', 'description']
    raw_mapping = csv_mapping_parser('input.csv', template)
    mapping = mapping_decoder(raw_mapping)
    
    index, size = 1, 100
    client = ModbusTcpClient('localhost')
    response = client.read_holding_registers(index, size)
    decoder = BinaryModbusDecoder.fromRegisters(response.registers)
    while index < size:
        print "[{}]\t{}".format(i, mapping[i]['type'](decoder))
        index += mapping[i]['size']

Also, using the same input mapping parsers, we can generate
populated slave contexts that can be run behing a modbus server::

    from modbus_mapper import csv_mapping_parser
    from modbus_mapper import modbus_context_decoder
    from pymodbus.client.ssync import StartTcpServer
    from pymodbus.datastore.context import ModbusServerContext

    template = ['address', 'value', 'function', 'name', 'description']
    raw_mapping = csv_mapping_parser('input.csv', template)
    slave_context = modbus_context_decoder(raw_mapping)
    context = ModbusServerContext(slaves=slave_context, single=True)
    StartTcpServer(context)
"""
import csv
import json
from collections import defaultdict

from tokenize import generate_tokens
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.datastore.store import ModbusSparseDataBlock
from pymodbus.compat import IS_PYTHON3
from pymodbus.datastore.context import ModbusSlaveContext
if IS_PYTHON3:
    from io import StringIO
else:
    from StringIO import StringIO

# --------------------------------------------------------------------------- # 
# raw mapping input parsers
# --------------------------------------------------------------------------- # 
# These generate the raw mapping_blocks from some form of input
# which can then be passed to the decoder in question to supply
# the requested output result.
# --------------------------------------------------------------------------- #


def csv_mapping_parser(path, template):
    """ Given a csv file of the the mapping data for
    a modbus device, return a mapping layout that can
    be used to decode an new block.

    .. note:: For the template, a few values are required
    to be defined: address, size, function, and type. All the remaining
    values will be stored, but not formatted by the application.
    So for example::

        template = ['address', 'type', 'size', 'name', 'function']
        mappings = json_mapping_parser('mapping.json', template)

    :param path: The path to the csv input file
    :param template: The row value template
    :returns: The decoded csv dictionary
    """
    mapping_blocks = defaultdict(dict)
    with open(path, 'r') as handle:
        reader = csv.reader(handle)
        reader.next() # skip the csv header
        for row in reader:
            mapping = dict(zip(template, row))
            fid = mapping.pop('function')
            aid = int(mapping['address'])
            mapping_blocks[aid] = mapping
    return mapping_blocks


def json_mapping_parser(path, template):
    """ Given a json file of the the mapping data for
    a modbus device, return a mapping layout that can
    be used to decode an new block.

    .. note:: For the template, a few values are required
    to be mapped: address, size, and type. All the remaining
    values will be stored, but not formatted by the application.
    So for example::

        template = {
            'Start': 'address',
            'DataType': 'type',
            'Length': 'size'
            # the remaining keys will just pass through
        }
        mappings = json_mapping_parser('mapping.json', template)

    :param path: The path to the csv input file
    :param template: The row value template
    :returns: The decoded csv dictionary
    """
    mapping_blocks = {}
    with open(path, 'r') as handle:
        for tid, rows in json.load(handle).iteritems():
            mappings = {}
            for key, values in rows.iteritems():
                mapping = {template.get(k, k) : v for k, v in values.iteritems()}
                mappings[int(key)] = mapping
            mapping_blocks[tid] = mappings
    return mapping_blocks


def xml_mapping_parser(path):
    """ Given an xml file of the the mapping data for
    a modbus device, return a mapping layout that can
    be used to decode an new block.

    .. note:: The input of the xml file is defined as
    follows::

    :param path: The path to the xml input file
    :returns: The decoded csv dictionary
    """
    pass


# --------------------------------------------------------------------------- # 
# modbus context decoders
# --------------------------------------------------------------------------- # 
# These are used to decode a raw mapping_block into a slave context with
# populated function data blocks.
# --------------------------------------------------------------------------- # 
def modbus_context_decoder(mapping_blocks):
    """ Given a mapping block input, generate a backing
    slave context with initialized data blocks.

    .. note:: This expects the following for each block:
    address, value, and function where function is one of
    di (discretes), co (coils), hr (holding registers), or
    ir (input registers).

    :param mapping_blocks: The mapping blocks
    :returns: The initialized modbus slave context
    """
    blocks = defaultdict(dict)
    for block in mapping_blocks.itervalues():
        for mapping in block.itervalues():
            value    = int(mapping['value'])
            address  = int(mapping['address'])
            function = mapping['function']
            blocks[function][address] = value
    return ModbusSlaveContext(**blocks)


# --------------------------------------------------------------------------- # 
# modbus mapping decoder
# --------------------------------------------------------------------------- # 
# These are used to decode a raw mapping_block into a request decoder.
# So this allows one to simply grab a number of registers, and then
# pass them to this decoder which will do the rest.
# --------------------------------------------------------------------------- # 
class ModbusTypeDecoder(object):
    """ This is a utility to determine the correct
    decoder to use given a type name. By default this
    supports all the types available in the default modbus
    decoder, however this can easily be extended this class
    and adding new types to the mapper::

        class CustomTypeDecoder(ModbusTypeDecoder):
            def __init__(self):
                ModbusTypeDecode.__init__(self)
                self.mapper['type-token'] = self.callback

            def parse_my_bitfield(self, tokens):
                return lambda d: d.decode_my_type()

    """
    def __init__(self):
        """ Initializes a new instance of the decoder
        """
        self.default = lambda m: self.parse_16bit_uint
        self.parsers = {
            'uint':    self.parse_16bit_uint,
            'uint8':   self.parse_8bit_uint,
            'uint16':  self.parse_16bit_uint,
            'uint32':  self.parse_32bit_uint,
            'uint64':  self.parse_64bit_uint,
            'int':     self.parse_16bit_int,
            'int8':    self.parse_8bit_int,
            'int16':   self.parse_16bit_int,
            'int32':   self.parse_32bit_int,
            'int64':   self.parse_64bit_int,
            'float':   self.parse_32bit_float,
            'float32': self.parse_32bit_float,
            'float64': self.parse_64bit_float,
            'string':  self.parse_32bit_int,
            'bits':    self.parse_bits,
        }

    # ------------------------------------------------------------ #
    # Type parsers
    # ------------------------------------------------------------ #
    @staticmethod
    def parse_string(tokens):
        _ = tokens.next()
        size = int(tokens.next())
        return lambda d: d.decode_string(size=size)

    @staticmethod
    def parse_bits(tokens):
        return lambda d: d.decode_bits()

    @staticmethod
    def parse_8bit_uint(tokens):
        return lambda d: d.decode_8bit_uint()

    @staticmethod
    def parse_16bit_uint(tokens):
        return lambda d: d.decode_16bit_uint()

    @staticmethod
    def parse_32bit_uint(tokens):
        return lambda d: d.decode_32bit_uint()

    @staticmethod
    def parse_64bit_uint(tokens):
        return lambda d: d.decode_64bit_uint()

    @staticmethod
    def parse_8bit_int(tokens):
        return lambda d: d.decode_8bit_int()

    @staticmethod
    def parse_16bit_int(tokens):
        return lambda d: d.decode_16bit_int()

    @staticmethod
    def parse_32bit_int(tokens):
        return lambda d: d.decode_32bit_int()

    @staticmethod
    def parse_64bit_int(tokens):
        return lambda d: d.decode_64bit_int()

    @staticmethod
    def parse_32bit_float(tokens):
        return lambda d: d.decode_32bit_float()

    @staticmethod
    def parse_64bit_float(tokens):
        return lambda d: d.decode_64bit_float()

    #------------------------------------------------------------
    # Public Interface
    #------------------------------------------------------------
    def tokenize(self, value):
        """ Given a value, return the tokens
    
        :param value: The value to tokenize
        :returns: A token generator
        """
        tokens = generate_tokens(StringIO(value).readline)
        for toknum, tokval, _, _, _ in tokens:
            yield tokval

    def parse(self, value):
        """ Given a type value, return a function
        that supplied with a decoder, will decode
        the correct value.

        :param value: The type of value to parse
        :returns: The decoder method to use
        """
        tokens = self.tokenize(value)
        token  = tokens.next().lower()
        parser = self.parsers.get(token, self.default)
        return parser(tokens)


def mapping_decoder(mapping_blocks, decoder=None):
    """ Given the raw mapping blocks, convert
    them into modbus value decoder map.

    :param mapping_blocks: The mapping blocks
    :param decoder: The type decoder to use
    """
    decoder = decoder or ModbusTypeDecoder()
    for block in mapping_blocks.itervalues():
        for mapping in block.itervalues():
            mapping['address'] = int(mapping['address'])
            mapping['size'] = int(mapping['size'])
            mapping['type'] = decoder.parse(mapping['type'])
