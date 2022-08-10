"""Test client async."""


import logging
import pytest


_logger = logging.getLogger()

# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#


@pytest.mark.parametrize(
    "sync_server, sync_client",
    [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ]
)
@pytest.mark.parametrize(
    "test_comm, test_framer",
    [
        ("tcp", "socket"),
        ("tcp", "rtu"),
        ("tcp", "ascii"),
        ("tcp", "binary"),
        ("udp", "socket"),
        ("udp", "rtu"),
        ("udp", "ascii"),
        ("udp", "binary"),
        ("serial", "rtu"),
        ("serial", "ascii"),
        ("serial", "binary"),
        # TLS is not automatic testable, without a certificate
    ]
)
def test_dummy(sync_server, sync_client, test_comm, test_framer):
    """Dummy."""
    txt = f"testing: {sync_server}, {sync_client}, {test_comm}, {test_framer}"
    _logger.info(txt)

    # start server

    # run client as:
    #    client_X.py
    #    client_X_basic_calls.py
    #    client_X_extended_calls.py

    # stop client

    # stop server
