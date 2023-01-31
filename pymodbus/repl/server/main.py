"""Repl server main."""
from __future__ import annotations

import asyncio
import json
import sys
from enum import Enum
from pathlib import Path
from typing import List

import typer

from pymodbus import pymodbus_apply_logging_config
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.logging import Log
from pymodbus.repl.server.cli import run_repl
from pymodbus.server.reactive.default_config import DEFAULT_CONFIG
from pymodbus.server.reactive.main import (
    DEFAULT_FRAMER,
    DEFUALT_HANDLERS,
    ReactiveServer,
)


CANCELLED_ERROR = asyncio.exceptions.CancelledError
CONTEXT_SETTING = {"allow_extra_args": True, "ignore_unknown_options": True}


# TBD class ModbusServerConfig:


class ModbusServerTypes(str, Enum):
    """Server types."""

    # ["tcp", "serial", "tls", "udp"]
    tcp = "tcp"  # pylint: disable=invalid-name
    serial = "serial"  # pylint: disable=invalid-name
    tls = "tls"  # pylint: disable=invalid-name
    udp = "udp"  # pylint: disable=invalid-name


class ModbusFramerTypes(str, Enum):
    """Framer types."""

    # ["socket", "rtu", "tls", "ascii", "binary"]
    socket = "socket"  # pylint: disable=invalid-name
    rtu = "rtu"  # pylint: disable=invalid-name
    tls = "tls"  # pylint: disable=invalid-name
    ascii = "ascii"  # pylint: disable=invalid-name
    binary = "binary"  # pylint: disable=invalid-name


def _completer(incomplete: str, valid_values: List[str]) -> List[str]:
    """Complete value."""
    completion = []
    for name in valid_values:
        if name.startswith(incomplete):
            completion.append(name)
    return completion


def framers(incomplete: str) -> List[str]:
    """Return an autocompleted list of supported clouds."""
    _framers = ["socket", "rtu", "tls", "ascii", "binary"]
    return _completer(incomplete, _framers)


def servers(incomplete: str) -> List[str]:
    """Return an autocompleted list of supported clouds."""
    _servers = ["tcp", "serial", "tls", "udp"]
    return _completer(incomplete, _servers)


def process_extra_args(extra_args: list[str], modbus_config: dict) -> dict:
    """Process extra args passed to server."""
    options_stripped = [x.strip().replace("--", "") for x in extra_args[::2]]
    extra_args = dict(list(zip(options_stripped, extra_args[1::2])))
    for option, value in extra_args.items():
        if option in modbus_config:
            try:
                modbus_config[option] = type(modbus_config[option])(value)
            except ValueError as err:
                Log.error(
                    "Error parsing extra arg {} with value '{}'. {}", option, value, err
                )
                sys.exit(1)
    return modbus_config


app = typer.Typer(
    no_args_is_help=True,
    context_settings=CONTEXT_SETTING,
    help="Reactive modebus server",
)


@app.callback()
def server(
    ctx: typer.Context,
    host: str = typer.Option("localhost", "--host", help="Host address"),
    web_port: int = typer.Option(8080, "--web-port", help="Web app port"),
    broadcast_support: bool = typer.Option(
        False, "-b", help="Support broadcast messages"
    ),
    repl: bool = typer.Option(True, help="Enable/Disable repl for server"),
    verbose: bool = typer.Option(
        False, help="Run with debug logs enabled for pymodbus"
    ),
):
    """Run server code."""
    log_level = Log.DEBUG if verbose else Log.ERROR
    pymodbus_apply_logging_config(log_level)

    ctx.obj = {
        "repl": repl,
        "host": host,
        "web_port": web_port,
        "broadcast": broadcast_support,
    }


@app.command("run", context_settings=CONTEXT_SETTING)
def run(
    ctx: typer.Context,
    modbus_server: str = typer.Option(
        ModbusServerTypes.tcp,
        "--modbus-server",
        "-s",
        case_sensitive=False,
        autocompletion=servers,
        help="Modbus Server",
    ),
    modbus_framer: str = typer.Option(
        ModbusFramerTypes.socket,
        "--framer",
        "-f",
        case_sensitive=False,
        autocompletion=framers,
        help="Modbus framer to use",
    ),
    modbus_port: str = typer.Option("5020", "--modbus-port", "-p", help="Modbus port"),
    modbus_unit_id: List[int] = typer.Option(
        None, "--unit-id", "-u", help="Supported Modbus unit id's"
    ),
    modbus_config: Path = typer.Option(
        None, help="Path to additional modbus server config"
    ),
    randomize: int = typer.Option(
        0,
        "--random",
        "-r",
        help="Randomize every `r` reads. 0=never, 1=always,2=every-second-read"
        ", and so on. Applicable IR and DI.",
    ),
    change_rate: int = typer.Option(
        0,
        "--change-rate",
        "-c",
        help="Rate in % registers to change. 0=none, 100=all, 12=12% of registers"
        ", and so on. Applicable IR and DI.",
    ),
):
    """Run Reactive Modbus server.

    Exposing REST endpoint for response manipulation.
    """
    repl = ctx.obj.pop("repl")
    # TBD extra_args = ctx.args
    web_app_config = ctx.obj
    loop = asyncio.get_event_loop()
    framer = DEFAULT_FRAMER.get(modbus_framer, ModbusSocketFramer)
    if modbus_config:
        with open(modbus_config) as my_file:  # pylint: disable=unspecified-encoding
            modbus_config = json.load(my_file)
    else:
        modbus_config = DEFAULT_CONFIG

    extra_args = ctx.args
    data_block_settings = modbus_config.pop("data_block_settings", {})
    modbus_config = modbus_config.get(modbus_server, {})
    modbus_config = process_extra_args(extra_args, modbus_config)
    if modbus_server != "serial":
        modbus_port = int(modbus_port)
        handler = modbus_config.pop("handler", "ModbusConnectedRequestHandler")
    else:
        handler = modbus_config.pop("handler", "ModbusSingleRequestHandler")
    handler = DEFUALT_HANDLERS.get(handler.strip())

    modbus_config["handler"] = handler
    modbus_config["randomize"] = randomize
    modbus_config["change_rate"] = change_rate
    app = ReactiveServer.factory(
        modbus_server,
        framer,
        modbus_port=modbus_port,
        unit=modbus_unit_id,
        loop=loop,
        single=False,
        data_block_settings=data_block_settings,
        **web_app_config,
        **modbus_config,
    )
    try:
        loop.run_until_complete(app.run_async(repl))
        if repl:
            loop.run_until_complete(run_repl(app))
        loop.run_forever()

    except CANCELLED_ERROR:
        print("Done!!!!!")


if __name__ == "__main__":
    app()
