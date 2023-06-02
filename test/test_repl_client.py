"""Test client sync."""
from contextlib import suppress

from pymodbus.repl.client.main import _process_args
from pymodbus.server.reactive.default_config import DEFAULT_CONFIG


def test_repl_default_config():
    """Test default config can be loaded."""
    config = DEFAULT_CONFIG
    assert config is not None


def test_repl_client_process_args():
    """Test argument processing in repl.client.main ( _process_args function)."""
    resp = _process_args(["address=11"], False)
    assert resp == ({"address": 11}, True)

    resp = _process_args(["address=0x11"], False)
    assert resp == ({"address": 17}, True)

    resp = _process_args(["address=0b11"], False)
    assert resp == ({"address": 3}, True)

    resp = _process_args(["address=0o11"], False)
    assert resp == ({"address": 9}, True)

    resp = _process_args(["address=11", "value=0x10"], False)
    assert resp == ({"address": 11, "value": 16}, True)

    resp = _process_args(["value=11", "address=0x10"], False)
    assert resp == ({"address": 16, "value": 11}, True)

    resp = _process_args(["address=0b11", "value=0x10"], False)
    assert resp == ({"address": 3, "value": 16}, True)

    with suppress(ValueError):
        resp = _process_args(["address=0xhj", "value=0x10"], False)

    with suppress(ValueError):
        resp = _process_args(["address=11ah", "value=0x10"], False)

    with suppress(ValueError):
        resp = _process_args(["address=0b12", "value=0x10"], False)
