"""Configuration for Pymodbus REPL Reactive Module."""

DEFAULT_CONFIG = {
    "tcp": {
        "handler": "ModbusConnectedRequestHandler",
        "allow_reuse_address": True,
        "allow_reuse_port": True,
        "backlog": 20,
        "ignore_missing_slaves": False,
    },
    "serial": {
        "handler": "ModbusSingleRequestHandler",
        "stopbits": 1,
        "bytesize": 8,
        "parity": "N",
        "baudrate": 9600,
        "timeout": 3,
        "auto_reconnect": False,
        "reconnect_delay": 2,
    },
    "tls": {
        "handler": "ModbusConnectedRequestHandler",
        "certfile": None,
        "keyfile": None,
        "allow_reuse_address": True,
        "allow_reuse_port": True,
        "backlog": 20,
        "ignore_missing_slaves": False,
    },
    "udp": {
        "handler": "ModbusDisonnectedRequestHandler",
        "ignore_missing_slaves": False,
    },
    "data_block_settings": {
        "min_binary_value": 0,  # For coils and DI
        "max_binary_value": 1,  # For coils and DI
        "min_register_value": 0,  # For Holding and input registers
        "max_register_value": 65535,  # For Holding and input registers
        "data_block": {
            "discrete_inputs": {
                "block_start": 0,  # Block start
                "block_size": 100,  # Block end
                "default": 0,  # Default value,
                "sparse": False,
            },
            "coils": {
                "block_start": 0,
                "block_size": 100,
                "default": 0,
                "sparse": False,
            },
            "holding_registers": {
                "block_start": 0,
                "block_size": 100,
                "default": 0,
                "sparse": False,
            },
            "input_registers": {
                "block_start": 0,
                "block_size": 100,
                "default": 0,
                "sparse": False,
            },
        },
    },
}

__all__ = ["DEFAULT_CONFIG"]
