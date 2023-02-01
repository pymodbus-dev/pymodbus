"""Helper Module for REPL actions."""
import inspect

# pylint: disable=missing-type-doc
import json
from collections import OrderedDict

import pygments
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML, PygmentsTokens
from pygments.lexers.data import JsonLexer

from pymodbus.payload import BinaryPayloadDecoder, Endian


predicate = inspect.isfunction
argspec = inspect.signature


FORMATTERS = {
    "int8": "decode_8bit_int",
    "int16": "decode_16bit_int",
    "int32": "decode_32bit_int",
    "int64": "decode_64bit_int",
    "uint8": "decode_8bit_uint",
    "uint16": "decode_16bit_uint",
    "uint32": "decode_32bit_uint",
    "uint64": "decode_64bit_int",
    "float16": "decode_16bit_float",
    "float32": "decode_32bit_float",
    "float64": "decode_64bit_float",
}


DEFAULT_KWARGS = {"unit": "Slave address"}

OTHER_COMMANDS = {
    "result.raw": "Show RAW Result",
    "result.decode": "Decode register response to known formats",
}
EXCLUDE = ["execute", "recv", "send", "trace", "set_debug"]
CLIENT_METHODS = [
    "connect",
    "close",
    "idle_time",
    "is_socket_open",
    "get_port",
    "set_port",
    "get_stopbits",
    "set_stopbits",
    "get_bytesize",
    "set_bytesize",
    "get_parity",
    "set_parity",
    "get_baudrate",
    "set_baudrate",
    "get_timeout",
    "set_timeout",
    "get_serial_settings",
]
CLIENT_ATTRIBUTES = []


class Command:
    """Class representing Commands to be consumed by Completer."""

    def __init__(self, name, signature, doc, unit=False):
        """Initialize.

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
            self._params = signature.parameters
            self.args = self.create_completion()
        else:
            self._params = ""

        if self.name.startswith("client.") and unit:
            self.args.update(**DEFAULT_KWARGS)

    def _create_help(self):
        """Create help."""
        doc = filter(lambda d: d, self.doc)
        cmd_help = list(
            filter(
                lambda x: not x.startswith(":param") and not x.startswith(":return"),
                doc,
            )
        )
        return " ".join(cmd_help).strip()

    def _create_arg_help(self):
        """Create arg help."""
        param_dict = {}
        params = list(filter(lambda d: d.strip().startswith(":param"), self.doc))
        for param in params:
            param, param_help = param.split(":param")[1].strip().split(":")
            param_dict[param] = param_help
        return param_dict

    def create_completion(self):
        """Create command completion meta data.

        :return:
        """
        words = {}

        def _create(entry, default):
            if entry not in ["self", "kwargs"]:
                if isinstance(default, (int, str)):
                    entry += f"={default}"
                return entry
            return None

        for arg in self._params.values():
            if entry := _create(arg.name, arg.default):
                entry, meta = self.get_meta(entry)
                words[entry] = meta

        return words

    def get_completion(self):
        """Get a list of completions.

        :return:
        """
        return self.args.keys()

    def get_meta(self, cmd):
        """Get Meta info of a given command.

        :param cmd: Name of command.
        :return: Dict containing meta info.
        """
        cmd = cmd.strip()
        cmd = cmd.split("=")[0].strip()
        return cmd, self.param_help.get(cmd, "")

    def __str__(self):
        """Return string representation."""
        if self.doc:
            return "Command {:>50}{:<20}".format(  # pylint: disable=consider-using-f-string
                self.name, self.doc
            )
        return f"Command {self.name}"


def _get_requests(members):
    """Get requests."""
    commands = list(
        filter(
            lambda x: (
                x[0] not in EXCLUDE and x[0] not in CLIENT_METHODS and callable(x[1])
            ),
            members,
        )
    )
    commands = {
        f"client.{c[0]}": Command(
            f"client.{c[0]}", argspec(c[1]), inspect.getdoc(c[1]), unit=False
        )
        for c in commands
        if not c[0].startswith("_")
    }
    return commands


def _get_client_methods(members):
    """Get client methods."""
    commands = list(
        filter(lambda x: (x[0] not in EXCLUDE and x[0] in CLIENT_METHODS), members)
    )
    commands = {
        "client.{c[0]}": Command(
            "client.{c[0]}", argspec(c[1]), inspect.getdoc(c[1]), unit=False
        )
        for c in commands
        if not c[0].startswith("_")
    }
    return commands


def _get_client_properties(members):
    """Get client properties."""
    global CLIENT_ATTRIBUTES  # pylint: disable=global-variable-not-assigned
    commands = list(filter(lambda x: not callable(x[1]), members))
    commands = {
        f"client.{c[0]}": Command(f"client.{c[0]}", None, "Read Only!", unit=False)
        for c in commands
        if (not c[0].startswith("_") and isinstance(c[1], (str, int, float)))
    }
    CLIENT_ATTRIBUTES.extend(list(commands.keys()))
    return commands


def get_commands(client):
    """Retrieve all required methods and attributes.

    Of a client object and convert it to commands.

    :param client: Modbus Client object.
    :return:
    """
    commands = {}
    members = inspect.getmembers(client)
    requests = _get_requests(members)
    client_methods = _get_client_methods(members)
    client_attr = _get_client_properties(members)

    result_commands = inspect.getmembers(Result, predicate=predicate)
    result_commands = {
        f"result.{c[0]}": Command(f"result.{c[0]}", argspec(c[1]), inspect.getdoc(c[1]))
        for c in result_commands
        if (not c[0].startswith("_") and c[0] != "print_result")
    }
    commands.update(requests)
    commands.update(client_methods)
    commands.update(client_attr)
    commands.update(result_commands)
    return commands


class Result:
    """Represent result command."""

    function_code = None
    data = None

    def __init__(self, result):
        """Initialize.

        :param result: Response of a modbus command.
        """
        if isinstance(result, dict):  # Modbus response
            self.function_code = result.pop("function_code", None)
            self.data = dict(result)
        else:
            self.data = result

    def decode(self, formatters, byte_order="big", word_order="big"):
        """Decode the register response to known formatters.

        :param formatters: int8/16/32/64, uint8/16/32/64, float32/64
        :param byte_order: little/big
        :param word_order: little/big
        """
        # Read Holding Registers (3)
        # Read Input Registers (4)
        # Read Write Registers (23)
        if not isinstance(formatters, (list, tuple)):
            formatters = [formatters]

        if self.function_code not in [3, 4, 23]:
            print_formatted_text(HTML("<red>Decoder works only for registers!!</red>"))
            return
        byte_order = (
            Endian.Little if byte_order.strip().lower() == "little" else Endian.Big
        )
        word_order = (
            Endian.Little if word_order.strip().lower() == "little" else Endian.Big
        )
        decoder = BinaryPayloadDecoder.fromRegisters(
            self.data.get("registers"), byteorder=byte_order, wordorder=word_order
        )
        for formatter in formatters:
            if not (formatter := FORMATTERS.get(formatter)):
                print_formatted_text(
                    HTML(f"<red>Invalid Formatter - {formatter}!!</red>")
                )
                return
            decoded = getattr(decoder, formatter)()
            self.print_result(decoded)

    def raw(self):
        """Return raw result dict."""
        self.print_result()

    def _process_dict(self, use_dict):
        """Process dict."""
        new_dict = OrderedDict()
        for k, v_item in use_dict.items():
            if isinstance(v_item, bytes):
                v_item = v_item.decode("utf-8")
            elif isinstance(v_item, dict):
                v_item = self._process_dict(v_item)
            elif isinstance(v_item, (list, tuple)):
                v_item = [
                    v1.decode("utf-8") if isinstance(v1, bytes) else v1 for v1 in v_item
                ]
            new_dict[k] = v_item
        return new_dict

    def print_result(self, data=None):
        """Print result object pretty.

        :param data: Data to be printed.
        """
        data = data or self.data
        if isinstance(data, dict):
            data = self._process_dict(data)
        elif isinstance(data, (list, tuple)):
            data = [v.decode("utf-8") if isinstance(v, bytes) else v for v in data]
        elif isinstance(data, bytes):
            data = data.decode("utf-8")
        tokens = list(pygments.lex(json.dumps(data, indent=4), lexer=JsonLexer()))
        print_formatted_text(PygmentsTokens(tokens))
