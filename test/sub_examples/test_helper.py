"""Test example helper function."""
from unittest import mock

import pytest

from examples import helper


class TestHelperExamples:
    """Test helper functions in examples."""

    def test_commandline_server_defaults(self):
        """Test defaults"""
        args = helper.get_commandline(server=True, cmdline=[])
        assert args.comm == "tcp"
        assert args.log == "info"
        assert args.baudrate == 9600
        assert args.framer
        assert args.port
        assert args.store
        assert not args.slaves
        assert not args.context

    def test_commandline_client_defaults(self):
        """Test defaults"""
        args = helper.get_commandline(server=False, cmdline=["--log", "info"])
        assert args.comm == "tcp"
        assert args.log == "info"
        assert args.baudrate == 9600
        assert args.host == "127.0.0.1"
        assert args.framer
        assert args.port

    def test_commandline(self):
        """Test defaults"""
        args = helper.get_commandline(
            server=False, cmdline=["--log", "debug", "--comm", "udp"]
        )
        assert args.comm == "udp"
        assert args.log == "debug"

    @pytest.mark.parametrize("suffix", ["crt", "key"])
    def test_certificate(self, suffix):
        """Test certificate."""
        path = helper.get_certificate(suffix)
        with open(path, encoding="utf-8"):
            pass

    def test_certificate_illegal(self):
        """Test illegal path."""
        with mock.patch(
            "examples.helper.os.getcwd", return_value="no/good/path"
        ), pytest.raises(RuntimeError):
            helper.get_certificate("crt")
