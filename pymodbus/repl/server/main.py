"""
Copyright (c) 2020 by RiptideIO
All rights reserved.
"""
import asyncio
import json
import click
from pymodbus.compat import IS_PYTHON3, PYTHON_VERSION
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.server.reactive.main import (
    ReactiveServer, DEFAULT_FRAMER, DEFUALT_HANDLERS)
from pymodbus.server.reactive.default_config import DEFUALT_CONFIG
from pymodbus.repl.server.cli import run_repl

if IS_PYTHON3 and PYTHON_VERSION > (3, 7):
    CANCELLED_ERROR = asyncio.exceptions.CancelledError
else:
    CANCELLED_ERROR = asyncio.CancelledError


@click.group("ReactiveModbusServer")
@click.option("--host", default="localhost", help="Host address")
@click.option("--web-port", default=8080, help="Web app port")
@click.option("--broadcast-support", is_flag=True,
              default=False, help="Support broadcast messages")
@click.option("--repl/--no-repl", is_flag=True,
              default=True, help="Enable/Disable repl for server")
@click.option("--verbose", is_flag=True,
              help="Run with debug logs enabled for pymodbus")
@click.pass_context
def server(ctx, host, web_port, broadcast_support, repl, verbose):
    global logger
    import logging
    FORMAT = ('%(asctime)-15s %(threadName)-15s'
              ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
    pymodbus_logger = logging.getLogger("pymodbus")
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger(__name__)
    if verbose:
        pymodbus_logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        pymodbus_logger.setLevel(logging.ERROR)
        logger.setLevel(logging.ERROR)

    ctx.obj = {"repl": repl, "host": host, "web_port": web_port,
               "broadcast": broadcast_support}


@server.command("run")
@click.option("--modbus-server", default="tcp",
              type=click.Choice(["tcp", "serial", "tls", "udp"],
                                case_sensitive=False),
              help="Modbus server")
@click.option("--modbus-framer", default="socket",
              type=click.Choice(["socket", "rtu", "tls", "ascii", "binary"],
                                case_sensitive=False),
              help="Modbus framer to use")
@click.option("--modbus-port", default="5020", help="Modbus port")
@click.option("--modbus-unit-id", default=[1], type=int,
              multiple=True, help="Modbus unit id")
@click.option("--modbus-config", type=click.Path(exists=True),
              help="Path to additional modbus server config")
@click.option("-r", "--randomize", default=0, help="Randomize every `r` reads."
                                                   " 0=never, 1=always, "
                                                   "2=every-second-read, "
                                                   "and so on. "
                                                   "Applicable IR and DI.")
@click.pass_context
def run(ctx, modbus_server, modbus_framer, modbus_port, modbus_unit_id,
        modbus_config, randomize):
    """
    Run Reactive Modbus server exposing REST endpoint
    for response manipulation.
    """
    if not IS_PYTHON3:
        click.secho("Pymodbus Server REPL not supported on python2", fg="read")
        exit(1)
    repl = ctx.obj.pop("repl")
    web_app_config = ctx.obj
    loop = asyncio.get_event_loop()
    framer = DEFAULT_FRAMER.get(modbus_framer, ModbusSocketFramer)
    if modbus_config:
        with open(modbus_config) as f:
            modbus_config = json.load(f)
    else:
        modbus_config = DEFUALT_CONFIG
    modbus_config = modbus_config.get(modbus_server, {})
    if modbus_server != "serial":
        modbus_port = int(modbus_port)
        handler = modbus_config.pop("handler", "ModbusConnectedRequestHandler")
    else:
        handler = modbus_config.pop("handler", "ModbusSingleRequestHandler")
    handler = DEFUALT_HANDLERS.get(handler.strip())

    modbus_config["handler"] = handler
    modbus_config["randomize"] = randomize
    app = ReactiveServer.factory(modbus_server, framer,
                                 modbus_port=modbus_port,
                                 unit=modbus_unit_id,
                                 loop=loop,
                                 **web_app_config, **modbus_config)
    try:
        if repl:
            loop.run_until_complete(app.run_async())

            loop.run_until_complete(run_repl(app))
            loop.run_forever()
        else:
            app.run()

    except CANCELLED_ERROR:
        print("Done!!!!!")


if __name__ == '__main__':
    server()
