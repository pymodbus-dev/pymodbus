"""Repl server main."""
import asyncio
import contextlib
import json
import logging
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


def process_extra_args(extra_args: List[str], modbus_config: dict) -> dict:
    """Process extra args passed to server."""
    options_stripped = [x.strip().replace("--", "") for x in extra_args[::2]]
    extra_args_dict = dict(list(zip(options_stripped, extra_args[1::2])))
    for option, value in extra_args_dict.items():
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
    help="Reactive Modbus server",
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
    log_level = logging.DEBUG if verbose else logging.ERROR
    pymodbus_apply_logging_config(log_level)

    ctx.obj = {
        "repl": repl,
        "host": host,
        "web_port": web_port,
        "broadcast_enable": broadcast_support,
    }


@app.command("run", context_settings=CONTEXT_SETTING)
def run(
    ctx: typer.Context,
    modbus_server: str = typer.Option(
        ModbusServerTypes.tcp.value,
        "--modbus-server",
        "-s",
        case_sensitive=False,
        autocompletion=servers,
        help="Modbus Server",
    ),
    modbus_framer: str = typer.Option(
        ModbusFramerTypes.socket.value,
        "--framer",
        "-f",
        case_sensitive=False,
        autocompletion=framers,
        help="Modbus framer to use",
    ),
    modbus_port: str = typer.Option("5020", "--modbus-port", "-p", help="Modbus port"),
    modbus_slave_id: List[int] = typer.Option(
        [1], "--slave-id", "-u", help="Supported Modbus slave id's"
    ),
    modbus_config_path: Path = typer.Option(
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
    if modbus_config_path:
        with open(modbus_config_path, encoding="utf-8") as my_file:
            modbus_config = json.load(my_file)
    else:
        modbus_config = DEFAULT_CONFIG

    extra_args = ctx.args
    data_block_settings = modbus_config.pop("data_block_settings", {})
    modbus_config = modbus_config.get(modbus_server, {})
    modbus_config = process_extra_args(extra_args, modbus_config)

    modbus_config["randomize"] = randomize
    modbus_config["change_rate"] = change_rate

    async def _wrapper():
        app = ReactiveServer.factory(
            modbus_server,
            framer,
            modbus_port=modbus_port,
            slave=modbus_slave_id,
            single=False,
            data_block_settings=data_block_settings,
            **web_app_config,
            **modbus_config,
        )
        await app.run_async(repl)
        return app

    app = loop.run_until_complete(_wrapper())
    if repl:
        with contextlib.suppress(asyncio.CancelledError):
            loop.run_until_complete(run_repl(app))

    else:
        loop.run_forever()


if __name__ == "__main__":
    app()
