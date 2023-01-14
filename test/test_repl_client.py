"""Test client sync."""
from pymodbus.repl.client.main import process_args
from pymodbus.server.reactive.default_config import DEFAULT_CONFIG


def test_repl_default_config():
    """Test default config can be loaded."""
    config = DEFAULT_CONFIG
    assert config is not None


def test_repl_client_process_args():
    """Test argument processing in repl.client.main ( process_args function)."""
    resp = process_args(["address=11"], False)
    assert resp == ({"address": 11}, True)

    resp = process_args(["address=0x11"], False)
    assert resp == ({"address": 17}, True)

    resp = process_args(["address=0b11"], False)
    assert resp == ({"address": 3}, True)

    resp = process_args(["address=0o11"], False)
    assert resp == ({"address": 9}, True)

    resp = process_args(["address=11", "value=0x10"], False)
    assert resp == ({"address": 11, "value": 16}, True)

    resp = process_args(["value=11", "address=0x10"], False)
    assert resp == ({"address": 16, "value": 11}, True)

    resp = process_args(["address=0b11", "value=0x10"], False)
    assert resp == ({"address": 3, "value": 16}, True)

    try:
        resp = process_args(["address=0xhj", "value=0x10"], False)
    except ValueError:
        pass

    try:
        resp = process_args(["address=11ah", "value=0x10"], False)
    except ValueError:
        pass

    try:
        resp = process_args(["address=0b12", "value=0x10"], False)
    except ValueError:
        pass
