"""Pymodbus REPL Entry point."""
# pylint: disable=anomalous-backslash-in-string
# flake8: noqa
import logging
import pathlib
import sys


try:
    import click
except ImportError:
    print('click not installed!! Install with "pip install click"')
    sys.exit(1)
try:
    from prompt_toolkit import PromptSession, print_formatted_text
except ImportError:
    print(
        "prompt toolkit is not installed!! "
        'Install with "pip install prompt_toolkit --upgrade"'
    )
    sys.exit(1)

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.python import PythonLexer

from pymodbus.exceptions import ParameterException
from pymodbus.repl.client.completer import (
    CmdCompleter,
    has_selected_completion,
)
from pymodbus.repl.client.helper import CLIENT_ATTRIBUTES, Result
from pymodbus.repl.client.mclient import ModbusSerialClient, ModbusTcpClient
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
)
from pymodbus.version import version


_logger = logging.getLogger()

click.disable_unicode_literals_warning = True

TITLE = f"""
----------------------------------------------------------------------------
__________          _____             .___  __________              .__
\______   \___.__. /     \   ____   __| _/  \______   \ ____ ______ |  |
 |     ___<   |  |/  \ /  \ /  _ \ / __ |    |       _// __ \\\____ \|  |
 |    |    \___  /    Y    (  <_> ) /_/ |    |    |   \  ___/|  |_> >  |__
 |____|    / ____\____|__  /\____/\____ | /\ |____|_  /\___  >   __/|____/
           \/            \/            \/ \/        \/     \/|__|
                                        v1.3.0 - {version}
----------------------------------------------------------------------------
"""


style = Style.from_dict(
    {
        "completion-menu.completion": "bg:#008888 #ffffff",
        "completion-menu.completion.current": "bg:#00aaaa #000000",
        "scrollbar.background": "bg:#88aaaa",
        "scrollbar.button": "bg:#222222",
    }
)


def bottom_toolbar():
    """Do console toolbar.

    :return:
    """
    return HTML(
        'Press <b><style bg="ansired">CTRL+D or exit </style></b>'
        ' to exit! Type "help" for list of available commands'
    )


class CaseInsenstiveChoice(click.Choice):
    """Do case Insensitive choice for click commands and options."""

    def convert(self, value, param, ctx):
        """Convert args to uppercase for evaluation."""
        if value is None:
            return None
        return super().convert(value.strip().upper(), param, ctx)


class NumericChoice(click.Choice):
    """Do numeric choice for click arguments and options."""

    def __init__(self, choices, typ):
        """Initialize."""
        self.typ = typ
        super().__init__(choices)

    def convert(self, value, param, ctx):
        """Convert."""
        # Exact match
        if value in self.choices:
            return self.typ(value)

        if ctx is not None and ctx.token_normalize_func is not None:
            value = ctx.token_normalize_func(value)
            for choice in self.casted_choices:  # pylint: disable=no-member
                if ctx.token_normalize_func(choice) == value:
                    return choice

        self.fail(
            "invalid choice: %s. (choose from %s)"  # pylint: disable=consider-using-f-string
            % (
                value,
                ", ".join(self.choices),
            ),
            param,
            ctx,
        )
        return None


def process_args(args: list, string: bool = True):
    """Internal function to parse arguments provided on command line.

    :param args: Array of argument values
    :param string: True if arguments values are strings, false if argument values are integers

    :return Tuple, where the first member is hash of parsed values, and second is boolean flag
        indicating if parsing succeeded.
    """
    kwargs = {}
    execute = True
    skip_index = None

    def _parse_val(arg_name, val):
        if not string:
            if "," in val:
                val = val.split(",")
                val = [int(v, 0) for v in val]
            else:
                val = int(val, 0)
        kwargs[arg_name] = val

    for i, arg in enumerate(args):
        if i == skip_index:
            continue
        arg = arg.strip()
        if "=" in arg:
            arg_name, val = arg.split("=")
            _parse_val(arg_name, val)
        else:
            arg_name, val = arg, args[i + 1]
            try:
                _parse_val(arg_name, val)
                skip_index = i + 1
            except TypeError:
                click.secho("Error parsing arguments!", fg="yellow")
                execute = False
                break
            except ValueError:
                click.secho("Error parsing argument", fg="yellow")
                execute = False
                break
    return kwargs, execute


def cli(client):  # pylint: disable=too-complex
    """Run client definition."""
    use_keys = KeyBindings()
    history_file = pathlib.Path.home().joinpath(".pymodhis")

    @use_keys.add("c-space")
    def _(event):
        """Initialize autocompletion, or select the next completion."""
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_next()
        else:
            buff.start_completion(select_first=False)

    @use_keys.add("enter", filter=has_selected_completion)
    def _(event):
        """Make the enter key work as the tab key only when showing the menu."""
        event.current_buffer.complete_state = None
        buffer = event.cli.current_buffer
        buffer.complete_state = None

    session = PromptSession(
        lexer=PygmentsLexer(PythonLexer),
        completer=CmdCompleter(client),
        style=style,
        complete_while_typing=True,
        bottom_toolbar=bottom_toolbar,
        key_bindings=use_keys,
        history=FileHistory(history_file),
        auto_suggest=AutoSuggestFromHistory(),
    )
    click.secho(TITLE, fg="green")
    result = None
    while True:  # pylint: disable=too-many-nested-blocks
        try:

            text = session.prompt("> ", complete_while_typing=True)
            if text.strip().lower() == "help":
                print_formatted_text(HTML("<u>Available commands:</u>"))
                for cmd, obj in sorted(session.completer.commands.items()):
                    if cmd != "help":
                        print_formatted_text(
                            HTML(
                                "<skyblue>{:45s}</skyblue>"  # pylint: disable=consider-using-f-string
                                "<seagreen>{:100s}"
                                "</seagreen>".format(cmd, obj.help_text)
                            )
                        )

                continue
            if text.strip().lower() == "exit":
                raise EOFError()
            if text.strip().lower().startswith("client."):
                try:
                    text = text.strip().split()
                    cmd = text[0].split(".")[1]
                    args = text[1:]
                    kwargs, execute = process_args(args, string=False)
                    if execute:
                        if text[0] in CLIENT_ATTRIBUTES:
                            result = Result(getattr(client, cmd))
                        else:
                            result = Result(getattr(client, cmd)(**kwargs))
                        result.print_result()
                except Exception as exc:  # pylint: disable=broad-except
                    click.secho(repr(exc), fg="red")
            elif text.strip().lower().startswith("result."):
                if result:
                    words = text.lower().split()
                    if words[0] == "result.raw":
                        result.raw()
                    if words[0] == "result.decode":
                        args = words[1:]
                        kwargs, execute = process_args(args)
                        if execute:
                            result.decode(**kwargs)
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.
        except Exception as exc:  # Handle all other exceptions pylint: disable=broad-except
            click.secho(str(exc), fg="red")

    click.secho("GoodBye!", fg="blue")


@click.group("pymodbus-repl")
@click.version_option(version, message=TITLE)
@click.option("--verbose", is_flag=True, default=False, help="Verbose logs")
@click.option(
    "--broadcast-support",
    is_flag=True,
    default=False,
    help="Support broadcast messages",
)
@click.option(
    "--retry-on-empty", is_flag=True, default=False, help="Retry on empty response"
)
@click.option(
    "--retry-on-error", is_flag=True, default=False, help="Retry on error response"
)
@click.option("--retries", default=3, help="Retry count")
@click.option(
    "--reset-socket/--no-reset-socket",
    default=True,
    help="Reset client socket on error",
)
@click.pass_context
def main(
    ctx,
    verbose,
    broadcast_support,
    retry_on_empty,
    retry_on_error,
    retries,
    reset_socket,
):
    """Run Main."""
    if verbose:
        use_format = (
            "%(asctime)-15s %(threadName)-15s "
            "%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
        )
        logging.basicConfig(format=use_format)
        _logger.setLevel(logging.DEBUG)
    ctx.obj = {
        "broadcast": broadcast_support,
        "retry_on_empty": retry_on_empty,
        "retry_on_invalid": retry_on_error,
        "retries": retries,
        "reset_socket": reset_socket,
    }


@main.command("tcp")
@click.pass_context
@click.option("--host", default="localhost", help="Modbus TCP IP ")
@click.option(
    "--port",
    default=502,
    type=int,
    help="Modbus TCP port",
)
@click.option(
    "--framer",
    default="tcp",
    type=str,
    help="Override the default packet framer tcp|rtu",
)
def tcp(ctx, host, port, framer):
    """Define TCP."""
    kwargs = {"host": host, "port": port}
    kwargs.update(**ctx.obj)
    if framer == "rtu":
        kwargs["framer"] = ModbusRtuFramer
    client = ModbusTcpClient(**kwargs)
    cli(client)


@main.command("serial")
@click.pass_context
@click.option(
    "--method",
    default="rtu",
    type=str,
    help="Modbus Serial Mode (rtu/ascii)",
)
@click.option(
    "--port",
    default=None,
    type=str,
    help="Modbus RTU port",
)
@click.option(
    "--baudrate",
    help="Modbus RTU serial baudrate to use. Defaults to 9600",
    default=9600,
    type=int,
)
@click.option(
    "--bytesize",
    help="Modbus RTU serial Number of data bits. "
    "Possible values: FIVEBITS, SIXBITS, SEVENBITS, "
    "EIGHTBITS. Defaults to 8",
    type=NumericChoice(["5", "6", "7", "8"], int),
    default="8",
)
@click.option(
    "--parity",
    help="Modbus RTU serial parity. "
    " Enable parity checking. Possible values: "
    "PARITY_NONE, PARITY_EVEN, PARITY_ODD PARITY_MARK, "
    'PARITY_SPACE. Default to "N"',
    default="N",
    type=CaseInsenstiveChoice(["N", "E", "O", "M", "S"]),
)
@click.option(
    "--stopbits",
    help="Modbus RTU serial stop bits. "
    "Number of stop bits. Possible values: STOPBITS_ONE, "
    'STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO. Default to "1"',
    default="1",
    type=NumericChoice(["1", "1.5", "2"], float),
)
@click.option(
    "--xonxoff",
    help="Modbus RTU serial xonxoff.  Enable software flow control. Defaults to 0",
    default=0,
    type=int,
)
@click.option(
    "--rtscts",
    help="Modbus RTU serial rtscts. Enable hardware (RTS/CTS) flow "
    "control. Defaults to 0",
    default=0,
    type=int,
)
@click.option(
    "--dsrdtr",
    help="Modbus RTU serial dsrdtr. Enable hardware (DSR/DTR) flow "
    "control. Defaults to 0",
    default=0,
    type=int,
)
@click.option(
    "--timeout",
    help="Modbus RTU serial read timeout. Defaults to 0.025 sec",
    default=0.25,
    type=float,
)
@click.option(
    "--write-timeout",
    help="Modbus RTU serial write timeout. Defaults to 2 sec",
    default=2,
    type=float,
)
def serial(  # pylint: disable=too-many-arguments
    ctx,
    method,
    port,
    baudrate,
    bytesize,
    parity,
    stopbits,
    xonxoff,
    rtscts,
    dsrdtr,
    timeout,
    write_timeout,
):
    """Define serial communication."""
    method = method.lower()
    if method == "ascii":
        framer = ModbusAsciiFramer
    elif method == "rtu":
        framer = ModbusRtuFramer
    elif method == "binary":
        framer = ModbusBinaryFramer
    elif method == "socket":
        framer = ModbusSocketFramer
    else:
        raise ParameterException("Invalid framer method requested")
    client = ModbusSerialClient(
        framer=framer,
        port=port,
        baudrate=baudrate,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        xonxoff=xonxoff,
        rtscts=rtscts,
        dsrdtr=dsrdtr,
        timeout=timeout,
        write_timeout=write_timeout,
        **ctx.obj,
    )
    cli(client)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
