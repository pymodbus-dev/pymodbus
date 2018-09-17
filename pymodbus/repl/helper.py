"""
Copyright (c) 2018 Riptide IO, Inc. All Rights Reserved.

"""
from __future__ import absolute_import, unicode_literals
import json
import pygments
import inspect
from collections import OrderedDict
from pymodbus.repl.client import ExtendedRequestSupport
from pygments.lexers.data import JsonLexer
from prompt_toolkit.formatted_text import PygmentsTokens, HTML
from prompt_toolkit import print_formatted_text

from pymodbus.payload import BinaryPayloadDecoder, Endian
from pymodbus.compat import PYTHON_VERSION, IS_PYTHON2, string_types, izip

if IS_PYTHON2 or PYTHON_VERSION < (3, 3):
    predicate = inspect.ismethod
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


class Command(object):

    def __init__(self, name, signature, doc):
        self.name = name
        self.doc = doc.split("\n") if doc else " ".join(name.split("_"))
        self.help_text = self._create_help()
        self.param_help = self._create_arg_help()
        if IS_PYTHON2:
            self._params = signature
        else:
            self._params = signature.parameters
        self.args = self.create_completion()
        if self.name.startswith("client."):
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
        return self.args.keys()

    def get_meta(self, cmd):
        cmd = cmd.strip()
        cmd = cmd.split("=")[0].strip()
        return cmd, self.param_help.get(cmd, '')

    def __str__(self):
        if self.doc:
            return "Command {0:>50}{:<20}".format(self.name, self.doc)
        return "Command {}".format(self.name)


def get_commands():
    commands = inspect.getmembers(ExtendedRequestSupport, predicate=predicate)
    commands = {
        "client.{}".format(c[0]):
            Command("client.{}".format(c[0]),
                    argspec(c[1]), inspect.getdoc(c[1]))
        for c in commands if not c[0].startswith("_")
    }
    result_commands = inspect.getmembers(Result, predicate=predicate)
    result_commands = {
        "result.{}".format(c[0]):
            Command("result.{}".format(c[0]), argspec(c[1]),
                    inspect.getdoc(c[1]))
        for c in result_commands if (not c[0].startswith("_")
                                     and c[0] != "print_result")
    }
    commands.update(result_commands)
    return commands


class Result(object):
    def __init__(self, result):
        self.function_code = result.pop('function_code', None)
        self.data = dict(result)

    def decode(self, formatters, byte_order='big', word_order='big'):
        """
        Decode the register response to known formatters
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
        Return raw result dict
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
