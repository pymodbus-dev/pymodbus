"""
Pymodbus REPL Entry point.

Copyright (c) 2018 Riptide IO, Inc. All Rights Reserved.

"""
from __future__ import absolute_import, unicode_literals
try:
    import click
except ImportError:
    print("click not installed!! Install with 'pip install click'")
    exit(1)
try:
    from prompt_toolkit import PromptSession, print_formatted_text
except ImportError:
    print("prompt toolkit is not installed!! "
          "Install with 'pip install prompt_toolkit --upgrade'")
    exit(1)

from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings

from pygments.lexers.python import PythonLexer
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from pymodbus.version import version
from pymodbus.repl.client.completer import CmdCompleter, has_selected_completion
from pymodbus.repl.client.helper import Result, CLIENT_ATTRIBUTES

click.disable_unicode_literals_warning = True

TITLE = """
----------------------------------------------------------------------------
__________          _____             .___  __________              .__   
\______   \___.__. /     \   ____   __| _/  \______   \ ____ ______ |  |  
 |     ___<   |  |/  \ /  \ /  _ \ / __ |    |       _// __ \\\____ \|  |  
 |    |    \___  /    Y    (  <_> ) /_/ |    |    |   \  ___/|  |_> >  |__
 |____|    / ____\____|__  /\____/\____ | /\ |____|_  /\___  >   __/|____/
           \/            \/            \/ \/        \/     \/|__|
                                        v{} - {}         
----------------------------------------------------------------------------
""".format("1.3.0", version)

log = None

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})


def bottom_toolbar():
    """
    Console toolbar.
    :return:
    """
    return HTML('Press <b><style bg="ansired">CTRL+D or exit </style></b>'
                ' to exit! Type "help" for list of available commands')


class CaseInsenstiveChoice(click.Choice):
    """
    Case Insensitive choice for click commands and options
    """
    def convert(self, value, param, ctx):
        """
        Convert args to uppercase for evaluation.

        """
        if value is None:
            return None
        return super(CaseInsenstiveChoice, self).convert(
            value.strip().upper(), param, ctx)


class NumericChoice(click.Choice):
    """
    Numeric choice for click arguments and options.
    """
    def __init__(self, choices, typ):
        self.typ = typ
        super(NumericChoice, self).__init__(choices)

    def convert(self, value, param, ctx):
        # Exact match
        if value in self.choices:
            return self.typ(value)

        if ctx is not None and ctx.token_normalize_func is not None:
            value = ctx.token_normalize_func(value)
            for choice in self.casted_choices:
                if ctx.token_normalize_func(choice) == value:
                    return choice

        self.fail('invalid choice: %s. (choose from %s)' %
                  (value, ', '.join(self.choices)), param, ctx)


def cli(client):
    kb = KeyBindings()

    @kb.add('c-space')
    def _(event):
        """
        Initialize autocompletion, or select the next completion.
        """
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_next()
        else:
            buff.start_completion(select_first=False)

    @kb.add('enter', filter=has_selected_completion)
    def _(event):
        """
        Makes the enter key work as the tab key only when showing the menu.
        """

        event.current_buffer.complete_state = None
        b = event.cli.current_buffer
        b.complete_state = None

    def _process_args(args, string=True):
        kwargs = {}
        execute = True
        skip_index = None
        for i, arg in enumerate(args):
            if i == skip_index:
                continue
            arg = arg.strip()
            if "=" in arg:
                a, val = arg.split("=")
                if not string:
                    if "," in val:
                        val = val.split(",")
                        val = [int(v) for v in val]
                    else:
                        val = int(val)
                kwargs[a] = val
            else:
                a, val = arg, args[i + 1]
                try:
                    if not string:
                        if "," in val:
                            val = val.split(",")
                            val = [int(v) for v in val]
                        else:
                            val = int(val)
                    kwargs[a] = val
                    skip_index = i + 1
                except TypeError:
                    click.secho("Error parsing arguments!",
                                fg='yellow')
                    execute = False
                    break
                except ValueError:
                    click.secho("Error parsing argument",
                                fg='yellow')
                    execute = False
                    break
        return kwargs, execute

    session = PromptSession(lexer=PygmentsLexer(PythonLexer),
                            completer=CmdCompleter(client), style=style,
                            complete_while_typing=True,
                            bottom_toolbar=bottom_toolbar,
                            key_bindings=kb,
                            history=FileHistory('../.pymodhis'),
                            auto_suggest=AutoSuggestFromHistory())
    click.secho("{}".format(TITLE), fg='green')
    result = None
    while True:
        try:

            text = session.prompt('> ', complete_while_typing=True)
            if text.strip().lower() == 'help':
                print_formatted_text(HTML("<u>Available commands:</u>"))
                for cmd, obj in sorted(session.completer.commands.items()):
                    if cmd != 'help':
                        print_formatted_text(
                            HTML("<skyblue>{:45s}</skyblue>"
                                 "<seagreen>{:100s}"
                                 "</seagreen>".format(cmd, obj.help_text)))

                continue
            elif text.strip().lower() == 'exit':
                raise EOFError()
            elif text.strip().lower().startswith("client."):
                try:
                    text = text.strip().split()
                    cmd = text[0].split(".")[1]
                    args = text[1:]
                    kwargs, execute = _process_args(args, string=False)
                    if execute:
                        if text[0] in CLIENT_ATTRIBUTES:
                            result = Result(getattr(client, cmd))
                        else:
                            result = Result(getattr(client, cmd)(**kwargs))
                        result.print_result()
                except Exception as e:
                    click.secho(repr(e), fg='red')
            elif text.strip().lower().startswith("result."):
                if result:
                    words = text.lower().split()
                    if words[0] == 'result.raw':
                        result.raw()
                    if words[0] == 'result.decode':
                        args = words[1:]
                        kwargs, execute = _process_args(args)
                        if execute:
                            result.decode(**kwargs)
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.
        except Exception as e:  # Handle all other exceptions
            click.secho(str(e), fg='red')

    click.secho('GoodBye!', fg='blue')


@click.group('pymodbus-repl')
@click.version_option(version, message=TITLE)
@click.option("--verbose", is_flag=True, default=False, help="Verbose logs")
@click.option("--broadcast-support", is_flag=True, default=False,
              help="Support broadcast messages")
@click.option("--retry-on-empty", is_flag=True, default=False,
              help="Retry on empty response")
@click.option("--retry-on-error", is_flag=True, default=False,
              help="Retry on error response")
@click.option("--retries", default=3, help="Retry count")
@click.pass_context
def main(ctx, verbose, broadcast_support, retry_on_empty,
         retry_on_error, retries):
    if verbose:
        global log
        import logging
        format = ('%(asctime)-15s %(threadName)-15s '
                  '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
        log = logging.getLogger('pymodbus')
        logging.basicConfig(format=format)
        log.setLevel(logging.DEBUG)
    ctx.obj = {
        "broadcast": broadcast_support,
        "retry_on_empty": retry_on_empty,
        "retry_on_invalid": retry_on_error,
        "retries": retries
    }


@main.command("tcp")
@click.pass_context
@click.option(
    "--host",
    default='localhost',
    help="Modbus TCP IP "
)
@click.option(
    "--port",
    default=502,
    type=int,
    help="Modbus TCP port",
)
@click.option(
    "--framer",
    default='tcp',
    type=str,
    help="Override the default packet framer tcp|rtu",
)
def tcp(ctx, host, port, framer):
    from pymodbus.repl.client.mclient import ModbusTcpClient
    kwargs = dict(host=host, port=port)
    kwargs.update(**ctx.obj)
    if framer == 'rtu':
        from pymodbus.framer.rtu_framer import ModbusRtuFramer
        kwargs['framer'] = ModbusRtuFramer
    client = ModbusTcpClient(**kwargs)
    cli(client)


@main.command("serial")
@click.pass_context
@click.option(
    "--method",
    default='rtu',
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
        type=int
    )
@click.option(
    "--bytesize",
    help="Modbus RTU serial Number of data bits. "
         "Possible values: FIVEBITS, SIXBITS, SEVENBITS, "
         "EIGHTBITS. Defaults to 8",
    type=NumericChoice(["5", "6", "7", "8"], int),
    default="8"
)
@click.option(
    "--parity",
    help="Modbus RTU serial parity. "
         " Enable parity checking. Possible values: "
         "PARITY_NONE, PARITY_EVEN, PARITY_ODD PARITY_MARK, "
         "PARITY_SPACE. Default to 'N'",
    default='N',
    type=CaseInsenstiveChoice(['N', 'E', 'O', 'M', 'S'])
)
@click.option(
    "--stopbits",
    help="Modbus RTU serial stop bits. "
         "Number of stop bits. Possible values: STOPBITS_ONE, "
         "STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO. Default to '1'",
    default="1",
    type=NumericChoice(["1", "1.5", "2"], float),
)
@click.option(
    "--xonxoff",
    help="Modbus RTU serial xonxoff.  Enable software flow control."
         "Defaults to 0",
    default=0,
    type=int
)
@click.option(
    "--rtscts",
    help="Modbus RTU serial rtscts. Enable hardware (RTS/CTS) flow "
         "control. Defaults to 0",
    default=0,
    type=int
)
@click.option(
    "--dsrdtr",
    help="Modbus RTU serial dsrdtr. Enable hardware (DSR/DTR) flow "
         "control. Defaults to 0",
    default=0,
    type=int
)
@click.option(
    "--timeout",
    help="Modbus RTU serial read timeout. Defaults to 0.025 sec",
    default=0.25,
    type=float
)
@click.option(
    "--write-timeout",
    help="Modbus RTU serial write timeout. Defaults to 2 sec",
    default=2,
    type=float
)
def serial(ctx, method, port, baudrate, bytesize, parity, stopbits, xonxoff,
           rtscts, dsrdtr, timeout, write_timeout):
    from pymodbus.repl.client.mclient import ModbusSerialClient
    client = ModbusSerialClient(method=method,
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
                                **ctx.obj)
    cli(client)


if __name__ == "__main__":
    main()
