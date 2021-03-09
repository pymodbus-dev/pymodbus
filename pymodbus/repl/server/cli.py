"""
Copyright (c) 2020 by RiptideIO
All rights reserved.
"""
import json
import click
import shutil
import logging

from prompt_toolkit.shortcuts import clear
from prompt_toolkit.shortcuts.progress_bar import formatters
from prompt_toolkit.styles import Style

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.formatted_text import HTML


logger = logging.getLogger(__name__)

TITLE = """
__________                          .______.                    _________
\______   \___.__. _____   ____   __| _/\_ |__  __ __  ______  /   _____/ ______________  __ ___________
 |     ___<   |  |/     \ /  _ \ / __ |  | __ \|  |  \/  ___/  \_____  \_/ __ \_  __ \  \/ // __ \_  __ \\
 |    |    \___  |  Y Y  (  <_> ) /_/ |  | \_\ \  |  /\___ \   /        \  ___/|  | \/\   /\  ___/|  | \/
 |____|    / ____|__|_|  /\____/\____ |  |___  /____//____  > /_______  /\___  >__|    \_/  \___  >__|
           \/          \/            \/      \/           \/          \/     \/                 \/"""

SMALL_TITLE = "Pymodbus server..."
BOTTOM_TOOLBAR = HTML('(MODBUS SERVER) <b><style bg="ansired">Press Ctrl+C or '
                      'type "exit" to quit</style></b> Type "help" '
                      'for list of available commands')
COMMAND_ARGS = ["response_type", "error_code", "delay_by",
                "clear_after", "data_len"]
RESPONSE_TYPES = ["normal", "error", "delayed", "empty", "stray"]
COMMANDS = {
    "manipulator": {
        "response_type": None,
        "error_code": None,
        "delay_by": None,
        "clear_after": None
    },
    "exit": None,
    "help": None,
    "clear": None
}
USAGE = "manipulator response_type=|normal|error|delayed|empty|stray \n" \
        "\tAdditional parameters\n" \
        "\t\terror_code=&lt;int&gt; \n\t\tdelay_by=&lt;in seconds&gt; \n\t\t" \
        "clear_after=&lt;clear after n messages int&gt;" \
        "\n\t\tdata_len=&lt;length of stray data (int)&gt;\n" \
        "\n\tExample usage: \n\t" \
        "1. Send error response 3 for 4 requests\n\t" \
        "   <ansiblue>manipulator response_type=error error_code=3 clear_after=4</ansiblue>\n\t" \
        "2. Delay outgoing response by 5 seconds indefinitely\n\t" \
        "   <ansiblue>manipulator response_type=delayed delay_by=5</ansiblue>\n\t" \
        "3. Send empty response\n\t" \
        "   <ansiblue>manipulator response_type=empty</ansiblue>\n\t" \
        "4. Send stray response of lenght 12 and revert to normal after 2 responses\n\t" \
        "   <ansiblue>manipulator response_type=stray data_len=11 clear_after=2</ansiblue>\n\t" \
        "5. To disable response manipulation\n\t" \
        "   <ansiblue>manipulator response_type=normal</ansiblue>"
COMMAND_HELPS = {
   "manipulator": "Manipulate response from server.\nUsage: {}".format(USAGE),
    "clear": "Clears screen"

}


STYLE = Style.from_dict({"": "cyan"})
CUSTOM_FORMATTERS = [
        formatters.Label(suffix=": "),
        formatters.Bar(start="|", end="|", sym_a="#", sym_b="#", sym_c="-"),
        formatters.Text(" "),
        formatters.Text(" "),
        formatters.TimeElapsed(),
        formatters.Text("  "),
    ]


def info(message):
    click.secho(str(message), fg="green")


def warning(message):
    click.secho(str(message), fg="yellow")


def error(message):
    click.secho(str(message), fg="red")


def get_terminal_width():
    return shutil.get_terminal_size()[0]


def print_help():
    print_formatted_text(HTML("<u>Available commands:</u>"))
    for cmd, hlp in sorted(COMMAND_HELPS.items()):
        print_formatted_text(
            HTML("<skyblue>{:45s}</skyblue><seagreen>{:100s}</seagreen>".format(cmd, hlp))
        )


async def interactive_shell(server):
    """
    CLI interactive shell
    """
    col = get_terminal_width()
    max_len = max([len(t) for t in TITLE.split("\n")])
    if col > max_len:
        info(TITLE)
    else:
        print_formatted_text(HTML('<u><b><style color="green">{}'
                                  '</style></b></u>'.format(SMALL_TITLE)))
    info("")
    completer = NestedCompleter.from_nested_dict(COMMANDS)
    session = PromptSession("SERVER > ",
                            completer=completer,
                            bottom_toolbar=BOTTOM_TOOLBAR)

    # Run echo loop. Read text from stdin, and reply it back.
    while True:
        try:
            invalid_command = False
            result = await session.prompt_async()
            if result == "exit":
                await server.web_app.shutdown()
                break
            if result == "help":
                print_help()
                continue
            if result == "clear":
                clear()
                continue
            command = result.split()
            if command:
                if command[0] not in COMMANDS:
                    invalid_command = True
                if invalid_command:
                    warning("Invalid command or invalid usage of command - {}".format(command))
                    continue
                if len(command) == 1:
                    warning("Usage: '{}'".format(USAGE))
                else:
                    args = command[1:]
                    skip_next = False
                    val_dict = {}
                    for index, arg in enumerate(args):
                        if skip_next:
                            skip_next = False
                            continue
                        if "=" in arg:
                            arg, value = arg.split("=")
                        else:
                            if arg in COMMAND_ARGS:
                                try:
                                    value = args[index+1]
                                    skip_next = True
                                except IndexError:
                                    error("Missing value "
                                          "for argument - {}".format(arg))
                                    warning("Usage: '{}'".format(USAGE))
                                    break
                        valid = True
                        if arg == "response_type":
                            if value not in RESPONSE_TYPES:
                                warning("Invalid response "
                                        "type request - {}".format(value))
                                warning("Choose from {}".format(RESPONSE_TYPES))
                                valid = False
                        elif arg in ["error_code", "delay_by",
                                     "clear_after", "data_len"]:
                            try:
                                value = int(value)
                            except ValueError:
                                warning("Expected integer "
                                        "value for {}".format(arg))
                                valid = False

                        if valid:
                            val_dict[arg] = value
                    if val_dict:
                        server.update_manipulator_config(val_dict)
                        # server.manipulator_config = val_dict
                # result = await run_command(tester, *command)

        except (EOFError, KeyboardInterrupt):
            return


async def main(server):
    with patch_stdout():
        try:
            await interactive_shell(server)
        finally:
            pass
        warning("Bye Bye!!!")


async def run_repl(server):
    await main(server)


