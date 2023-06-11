"""Test transport."""
import time

import pytest


@pytest.mark.skipif(pytest.IS_WINDOWS, reason="not implemented.")
class TestCommUnixTransport:
    """Test for the transport module."""

    @pytest.mark.parametrize("positive", [True, False])
    async def test_connect(self, transport, domain_socket):
        """Test connect_unix()."""
        transport.setup_unix(False, domain_socket)
        start = time.time()
        assert not await transport.transport_connect()
        delta = time.time() - start
        assert delta < transport.comm_params.timeout_connect * 1.2
        transport.close()

    @pytest.mark.parametrize("positive", [True, False])
    async def test_listen(self, transport_server, positive, domain_socket):
        """Test listen_unix()."""
        transport_server.setup_unix(True, domain_socket)
        server = await transport_server.transport_listen()
        assert positive == bool(server)
        assert positive == bool(transport_server.transport)
        if server:
            server.close()
        transport_server.close()

    @pytest.mark.parametrize("positive", [True])
    async def test_connected(self, transport, transport_server, domain_socket):
        """Test listen/connect unix()."""
        transport_server.setup_unix(True, domain_socket)
        await transport_server.transport_listen()

        transport.setup_unix(False, domain_socket)
        assert await transport.transport_connect()
        transport.close()
        transport_server.close()


class TestCommTcpTransport:
    """Test for the transport module."""

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize("positive", [True, False])
    async def test_connect(self, transport, use_port, domain_host):
        """Test connect_tcp()."""
        transport.setup_tcp(False, domain_host, use_port)
        start = time.time()
        assert not await transport.transport_connect()
        delta = time.time() - start
        assert delta < transport.comm_params.timeout_connect * 1.2
        transport.close()

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize("positive", [True, False])
    async def test_listen(self, transport_server, use_port, positive, domain_host):
        """Test listen_tcp()."""
        transport_server.setup_tcp(True, domain_host, use_port)
        server = await transport_server.transport_listen()
        assert positive == bool(server)
        assert positive == bool(transport_server.transport)
        transport_server.close()
        if server:
            server.close()

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize("positive", [True])
    async def test_connected(self, transport, transport_server, use_port, domain_host):
        """Test listen/connect tcp()."""
        transport_server.setup_tcp(True, domain_host, use_port)
        server = await transport_server.transport_listen()
        assert server
        transport.setup_tcp(False, domain_host, use_port)
        assert await transport.transport_connect()
        transport.close()
        transport_server.close()
        server.close()


class TestCommTlsTransport:
    """Test for the transport module."""

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize("positive", [True, False])
    async def test_connect(self, transport, params, domain_host):
        """Test connect_tls()."""
        transport.setup_tls(
            False,
            domain_host,
            params.port,
            None,
            params.cwd + "crt",
            params.cwd + "key",
            None,
            "localhost",
        )
        start = time.time()
        assert not await transport.transport_connect()
        delta = time.time() - start
        assert delta < transport.comm_params.timeout_connect * 1.2
        transport.close()

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize("positive", [True, False])
    async def test_listen(self, transport_server, params, positive, domain_host):
        """Test listen_tls()."""
        transport_server.setup_tls(
            True,
            domain_host,
            params.port,
            None,
            params.cwd + "crt",
            params.cwd + "key",
            None,
            "localhost",
        )
        server = await transport_server.transport_listen()
        assert positive == bool(server)
        assert positive == bool(transport_server.transport)
        transport_server.close()
        if server:
            server.close()

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize("positive", [True])
    async def test_connected(self, transport, transport_server, params, domain_host):
        """Test listen/connect tls()."""
        transport_server.setup_tls(
            True,
            domain_host,
            params.port,
            None,
            params.cwd + "crt",
            params.cwd + "key",
            None,
            "localhost",
        )
        server = await transport_server.transport_listen()
        assert server

        transport.setup_tcp(False, domain_host, params.port)
        assert await transport.transport_connect()
        transport.close()
        transport_server.close()
        server.close()


class TestCommUdpTransport:
    """Test for the transport module."""

    async def test_connect(self):
        """Test connect_udp()."""
        # always true, since udp is connectionless.

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize("positive", [True, False])
    async def test_listen(self, transport_server, use_port, positive, domain_host):
        """Test listen_udp()."""
        transport_server.setup_udp(True, domain_host, use_port)
        server = await transport_server.transport_listen()
        assert positive == bool(server)
        assert positive == bool(transport_server.transport)
        transport_server.close()
        if server:
            server.close()

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize("positive", [True])
    async def test_connected(self, transport, transport_server, use_port, domain_host):
        """Test listen/connect udp()."""
        transport_server.setup_udp(True, domain_host, use_port)
        server = await transport_server.transport_listen()
        assert server
        transport.setup_udp(False, domain_host, use_port)
        assert await transport.transport_connect()
        transport.close()
        transport_server.close()
        server.close()


class TestCommSerialTransport:
    """Test for the transport module."""

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize("positive", [True, False])
    async def test_connect(self, transport, use_port, positive):
        """Test connect_serial()."""
        domain_port = f"unix:/localhost:{use_port}" if positive else "/illegal_port"
        transport.setup_serial(
            False,
            domain_port,
            9600,
            8,
            "E",
            2,
        )
        start = time.time()
        assert not await transport.transport_connect()
        delta = time.time() - start
        assert delta < transport.comm_params.timeout_connect * 1.2
        transport.close()

    async def test_listen(self, transport_server):
        """Test listen_serial()."""
        transport_server.setup_serial(
            True,
            "/illegal_port",
            9600,
            8,
            "E",
            2,
        )
        server = await transport_server.transport_listen()
        assert not server
        assert not transport_server.transport
        transport_server.close()

        # there are no positive test, since there are no standard tty port

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connected(self, transport, transport_server, use_port):
        """Test listen/connect serial()."""
        transport_server.setup_tcp(True, "localhost", use_port)
        server = await transport_server.transport_listen()
        assert server
        transport.setup_serial(
            False,
            f"socket://localhost:{use_port}",
            9600,
            8,
            "E",
            2,
        )
        assert await transport.transport_connect()
        transport.close()
        transport_server.close()
        server.close()
