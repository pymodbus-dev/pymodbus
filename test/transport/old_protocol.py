"""Test transport."""
import pytest

from pymodbus.transport import CommType


COMM_TYPES = [
    CommType.TCP,
    CommType.TLS,
    CommType.UDP,
    CommType.SERIAL,
]


class TestModbusProtocol:
    """Test protocol layer of the transport module.

    This part contains tests with real connections.
    Testing the real connections once, allows the safe use of
    NullModem for all other tests apart from
    the client/server end to end testing.
    """

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port."""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]

    @pytest.mark.parametrize("use_comm_type", COMM_TYPES)
    async def test_init_client(self, client):
        """Test init()."""
        assert client.unique_id == str(id(client))
        assert not hasattr(client, "active_connections")
        assert not client.is_server

    @pytest.mark.parametrize("use_comm_type", COMM_TYPES)
    async def test_init_server(self, server):
        """Test init()."""
        assert not hasattr(server, "unique_id")
        assert not server.active_connections
        assert server.is_server
