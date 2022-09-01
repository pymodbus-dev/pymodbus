"""Test client sync."""
import pytest

from pymodbus.repl.client.main import _process_args as process_args


def test_repl_client_process_args():
    """Test argument processing in repl.client.main (_process_args function)."""
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
    except Exception as exc:  # pylint: disable=broad-except
        pytest.fail(f"Exception in _process_args: {exc}")

    try:
        resp = process_args(["address=11ah", "value=0x10"], False)
    except ValueError:
        pass
    except Exception as exc:  # pylint: disable=broad-except
        pytest.fail(f"Exception in _process_args: {exc}")

    try:
        resp = process_args(["address=0b12", "value=0x10"], False)
    except ValueError:
        pass
    except Exception as exc:  # pylint: disable=broad-except
        pytest.fail(f"Exception in _process_args: {exc}")
