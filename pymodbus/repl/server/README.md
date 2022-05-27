# Pymodbus REPL Server

Pymodbus REPL server helps to quicky spin an [asynchronous server](../../../examples/common/asyncio_server.py) from command line. 

Support both `Modbus TCP` and `Modbus RTU` server.


Some features offered are

---
1. Runs a [reactive server](../../server/reactive/main.py) in `REPL` and `NON REPL` mode.
2. Exposes REST API's to manipulate the behaviour of the server in non repl mode.
3. Ability to manipulate the out-going response dynamically (either via REPL console or via REST API request).
4. Ability to delay the out-going response dynamically (either via REPL console or via REST API request).
5. Auto revert to normal response after pre-defined number of manipulated responses.

## Installation
Install `pymodbus` with the required dependencies

`pip install pymodbus[repl]`

## Usage

Invoke REPL server with `pymodbus.server run` command.

```shell
✗ pymodbus.server --help
Usage: pymodbus.server [OPTIONS] COMMAND [ARGS]...

  Server code.

Options:
  -h, --host TEXT          Host address  [default: localhost]
  -p, --web-port INTEGER   Web app port  [default: 8080]
  -b, --broadcast-support  Support broadcast messages
  --repl / --no-repl       Enable/Disable repl for server  [default: repl]
  --verbose                Run with debug logs enabled for pymodbus
  --help                   Show this message and exit.

Commands:
  run  Run Reactive Modbus server exposing REST endpoint for response...
```

```shell
✗ pymodbus.server run --help
Usage: pymodbus.server run [OPTIONS]

  Run Reactive Modbus server exposing REST endpoint for response manipulation.

Options:
  -s, --modbus-server [tcp|serial|tls|udp]
                                  Modbus server  [default: tcp]
  -f, --modbus-framer [socket|rtu|tls|ascii|binary]
                                  Modbus framer to use  [default: socket]
  -mp, --modbus-port TEXT         Modbus port
  -u, --modbus-unit-id INTEGER    Modbus unit id
  --modbus-config PATH            Path to additional modbus server config
  -r, --randomize INTEGER         Randomize every `r` reads. 0=never,
                                  1=always, 2=every-second-read, and so on.
                                  Applicable IR and DI.  [default: 0]
  --help                          Show this message and exit.
```

### Pymodbus Server REPL mode 

