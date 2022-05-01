"""
Copyright (c) 2020 by RiptideIO
All rights reserved.
"""

DEFUALT_CONFIG = {
  "tcp": {
    "handler": "ModbusConnectedRequestHandler",
    "allow_reuse_address": True,
    "allow_reuse_port": True,
    "backlog": 20,
    "ignore_missing_slaves": False
  },
  "serial": {
    "handler": "ModbusSingleRequestHandler",
    "stopbits": 1,
    "bytesize": 8,
    "parity": "N",
    "baudrate": 9600,
    "timeout": 3,
    "auto_reconnect": False,
    "reconnect_delay": 2
  },
  "tls": {
    "handler": "ModbusConnectedRequestHandler",
    "certfile": None,
    "keyfile": None,
    "allow_reuse_address": True,
    "allow_reuse_port": True,
    "backlog": 20,
    "ignore_missing_slaves": False
  },
  "udp": {
    "handler": "ModbusDisonnectedRequestHandler",
    "ignore_missing_slaves": False
  }
}
