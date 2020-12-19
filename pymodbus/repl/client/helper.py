"""
Helper Module for REPL actions.

Copyright (c) 2018 Riptide IO, Inc. All Rights Reserved.

"""
from __future__ import absolute_import, unicode_literals
import json
import pygments
import inspect
from collections import OrderedDict
from pygments.lexers.data import JsonLexer
from prompt_toolkit.formatted_text import PygmentsTokens, HTML
from prompt_toolkit import print_formatted_text

from pymodbus.payload import BinaryPayloadDecoder, Endian
from pymodbus.compat import PYTHON_VERSION, IS_PYTHON2, string_types, izip

predicate = inspect.ismethod
if IS_PYTHON2 or PYTHON_VERSION < (3, 3):
    argspec = inspect.getargspec
else:
    predicate = inspect.isfunction
    argspec = inspect.signature


FORMATTERS = {
    'int8': 'decode_8bit_int',
    'int16': 'decode_16bit_int',
    'int32': 'decode_32bit_int',
    'int64': 'decode_64bit_int',
    'uint8': 'decode_8bit_uint',
    'uint16': 'decode_16bit_uint',
    'uint32': 'decode_32bit_uint',
    'uint64': 'decode_64bit_int',
    'float16': 'decode_16bit_float',
    'float32': 'decode_32bit_float',
    'float64': 'decode_64bit_float',
}


DEFAULT_KWARGS = {
    'unit': 'Slave address'
}

OTHER_COMMANDS = {
    "result.raw": "Show RAW Result",
    "result.decode": "Decode register response to known formats",
}
EXCLUDE = ['execute', 'recv', 'send', 'trace', 'set_debug']
CLIENT_METHODS = [
    'connect', 'close', 'idle_time', 'is_socket_open', 'get_port', 'set_port',
    'get_stopbits', 'set_stopbits', 'get_bytesize', 'set_bytesize',
    'get_parity', 'set_parity', 'get_baudrate', 'set_baudrate', 'get_timeout',
    'set_timeout', 'get_serial_settings'

]
CLIENT_ATTRIBUTES = []


class Command(object):
    """
    Class representing Commands to be consumed by Completer.
    """
    def __init__(self, name, signature, doc, unit=False):
        """

        :param name: Name of the command
        :param signature: inspect object
        :param doc: Doc string for the command
        :param unit: Use unit as additional argument in the command .
        """
        self.name = name
        self.doc = doc.split("\n") if doc else " ".join(name.split("_"))
        self.help_text = self._create_help()
        self.param_help = self._create_arg_help()
        if signature:
            if IS_PYTHON2:
                self._params = signature
            else:
                self._params = signature.parameters
            self.args = self.create_completion()
        else:
            self._params = ''

        if self.name.startswith("client.") and unit:
            self.args.update(**DEFAULT_KWARGS)

    def _create_help(self):
        doc = filter(lambda d: d, self.doc)
        cmd_help = list(filter(
            lambda x: not x.startswith(":param") and not x.startswith(
                ":return"), doc))
        return " ".join(cmd_help).strip()

    def _create_arg_help(self):
        param_dict = {}
        params = list(filter(lambda d: d.strip().startswith(":param"),
                             self.doc))
        for param in params:
            param, help = param.split(":param")[1].strip().split(":")
            param_dict[param] = help
        return param_dict

    def create_completion(self):
        """
        Create command completion meta data.

        :return:
        """
        words = {}

        def _create(entry, default):
            if entry not in ['self', 'kwargs']:
                if isinstance(default, (int, string_types)):
                    entry += "={}".format(default)
                return entry

        if IS_PYTHON2:
            if not self._params.defaults:
                defaults = [None]*len(self._params.args)
            else:
                defaults = list(self._params.defaults)
                missing = len(self._params.args) - len(defaults)
                if missing > 1:
                    defaults.extend([None]*missing)
            defaults.insert(0, None)
            for arg, default in izip(self._params.args, defaults):
                entry = _create(arg, default)
                if entry:
                    entry, meta = self.get_meta(entry)
                    words[entry] = help
        else:
            for arg in self._params.values():
                entry = _create(arg.name, arg.default)
                if entry:
                    entry, meta = self.get_meta(entry)
                    words[entry] = meta

        return words

    def get_completion(self):
        """
        Gets a list of completions.

        :return:
        """
        return self.args.keys()

    def get_meta(self, cmd):
        """
        Get Meta info of a given command.

        :param cmd: Name of command.
        :return: Dict containing meta info.
        """
        cmd = cmd.strip()
        cmd = cmd.split("=")[0].strip()
        return cmd, self.param_help.get(cmd, '')

    def __str__(self):
        if self.doc:
            return "Command {0:>50}{:<20}".format(self.name, self.doc)
        return "Command {}".format(self.name)


def _get_requests(members):
    commands = list(filter(lambda x: (x[0] not in EXCLUDE
                                      and x[0] not in CLIENT_METHODS
                                      and callable(x[1])),
                           members))
    commands = {
        "client.{}".format(c[0]):
            Command("client.{}".format(c[0]),
                    argspec(c[1]), inspect.getdoc(c[1]), unit=True)
        for c in commands if not c[0].startswith("_")
    }
    return commands


def _get_client_methods(members):
    commands = list(filter(lambda x: (x[0] not in EXCLUDE
                                      and x[0] in CLIENT_METHODS),
                           members))
    commands = {
        "client.{}".format(c[0]):
            Command("client.{}".format(c[0]),
                    argspec(c[1]), inspect.getdoc(c[1]), unit=False)
        for c in commands if not c[0].startswith("_")
    }
    return commands


def _get_client_properties(members):
    global CLIENT_ATTRIBUTES
    commands = list(filter(lambda x: not callable(x[1]), members))
    commands = {
        "client.{}".format(c[0]):
            Command("client.{}".format(c[0]), None, "Read Only!", unit=False)
        for c in commands if (not c[0].startswith("_")
                              and isinstance(c[1], (string_types, int, float)))
    }
    CLIENT_ATTRIBUTES.extend(list(commands.keys()))
    return commands


def get_commands(client):
    """
    Helper method to retrieve all required methods and attributes of a client \
    object and convert it to commands.

    :param client: Modbus Client object.
    :return:
    """
    commands = dict()
    members = inspect.getmembers(client)
    requests = _get_requests(members)
    client_methods = _get_client_methods(members)
    client_attr = _get_client_properties(members)

    result_commands = inspect.getmembers(Result, predicate=predicate)
    result_commands = {
        "result.{}".format(c[0]):
            Command("result.{}".format(c[0]), argspec(c[1]),
                    inspect.getdoc(c[1]))
        for c in result_commands if (not c[0].startswith("_")
                                     and c[0] != "print_result")
    }
    commands.update(requests)
    commands.update(client_methods)
    commands.update(client_attr)
    commands.update(result_commands)
    return commands


class Result(object):
    """
    Represent result command.
    """
    function_code = None
    data = None

    def __init__(self, result):
        """
        :param result: Response of a modbus command.
        """
        if isinstance(result, dict):  # Modbus response
            self.function_code = result.pop('function_code', None)
            self.data = dict(result)
        else:
            self.data = result

    def decode(self, formatters, byte_order='big', word_order='big'):
        """
        Decode the register response to known formatters.

        :param formatters: int8/16/32/64, uint8/16/32/64, float32/64
        :param byte_order: little/big
        :param word_order: little/big
        :return: Decoded Value
        """
        # Read Holding Registers (3)
        # Read Input Registers (4)
        # Read Write Registers (23)
        if not isinstance(formatters, (list, tuple)):
            formatters = [formatters]

        if self.function_code not in [3, 4, 23]:
            print_formatted_text(
                HTML("<red>Decoder works only for registers!!</red>"))
            return
        byte_order = (Endian.Little if byte_order.strip().lower() == "little"
                      else Endian.Big)
        word_order = (Endian.Little if word_order.strip().lower() == "little"
                      else Endian.Big)
        decoder = BinaryPayloadDecoder.fromRegisters(self.data.get('registers'),
                                                     byteorder=byte_order,
                                                     wordorder=word_order)
        for formatter in formatters:
            formatter = FORMATTERS.get(formatter)
            if not formatter:
                print_formatted_text(
                    HTML("<red>Invalid Formatter - {}"
                         "!!</red>".format(formatter)))
                return
            decoded = getattr(decoder, formatter)()
            self.print_result(decoded)

    def raw(self):
        """
        Return raw result dict.

        :return:
        """
        self.print_result()

    def _process_dict(self, d):
        new_dict = OrderedDict()
        for k, v in d.items():
            if isinstance(v, bytes):
                v = v.decode('utf-8')
            elif isinstance(v, dict):
                v = self._process_dict(v)
            elif isinstance(v, (list, tuple)):
                v = [v1.decode('utf-8') if isinstance(v1, bytes) else v1
                     for v1 in v ]
            new_dict[k] = v
        return new_dict

    def print_result(self, data=None):
        """
        Prettu print result object.

        :param data: Data to be printed.
        :return:
        """
        data = data or self.data
        if isinstance(data, dict):
            data = self._process_dict(data)
        elif isinstance(data, (list, tuple)):
            data = [v.decode('utf-8') if isinstance(v, bytes) else v
                    for v in data]
        elif isinstance(data, bytes):
            data = data.decode('utf-8')
        tokens = list(pygments.lex(json.dumps(data, indent=4),
                                   lexer=JsonLexer()))
        print_formatted_text(PygmentsTokens(tokens))
