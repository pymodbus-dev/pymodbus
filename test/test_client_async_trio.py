from pymodbus.compat import IS_PYTHON3, PYTHON_VERSION
import pytest
TRIO_AVAILABLE = IS_PYTHON3 and PYTHON_VERSION >= (3, 6)
if TRIO_AVAILABLE:
    from unittest import mock
    from pymodbus.client.asynchronous.trio import (
        ModbusClientProtocol, TrioModbusTcpClient)#, ModbusUdpClientProtocol)
    # from test.trio_test_helper import return_as_coroutine, run_coroutine
    from pymodbus.factory import ClientDecoder
    from pymodbus.exceptions import ConnectionException
    from pymodbus.transaction import ModbusSocketFramer
    from pymodbus.bit_read_message import ReadCoilsRequest, ReadCoilsResponse
    # protocols = [ModbusUdpClientProtocol, ModbusClientProtocol]
    protocols = [ModbusClientProtocol]
else:
    import mock
    protocols = [None, None]


@pytest.mark.skipif(not TRIO_AVAILABLE, reason="requires python3.6 or above")
class TestTrioClient(object):
    def test_factory_stop(self):
        mock_protocol_class = mock.MagicMock()
        client = TrioModbusTcpClient(protocol_class=mock_protocol_class)

        assert not client.connected
        client.stop()
        assert not client.connected

        # fake connected client:
        client.protocol = mock.MagicMock()
        client.connected = True

        client.stop()
        client.protocol.transport.close.assert_called_once_with()

    def test_factory_protocol_made_connection(self):
        mock_protocol_class = mock.MagicMock()
        client = TrioModbusTcpClient(protocol_class=mock_protocol_class)

        assert not client.connected
        assert client.protocol is None
        client.protocol_made_connection(mock.sentinel.PROTOCOL)
        assert client.connected
        assert client.protocol is mock.sentinel.PROTOCOL

        client.protocol_made_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
        assert client.connected
        assert client.protocol is mock.sentinel.PROTOCOL

    # @pytest.mark.trio
    # async def test_factory_start_success(self):
    #     mock_protocol_class = mock.MagicMock()
    #     client = TrioModbusTcpClient(
    #         protocol_class=mock_protocol_class,
    #         host=mock.sentinel.HOST,
    #         port=mock.sentinel.PORT,
    #     )
    #
    #     async with client.manage_connection():
    #         # mock_loop.create_connection.assert_called_once_with(mock.ANY, mock.sentinel.HOST, mock.sentinel.PORT)
    #         # assert mock_async.call_count == 0
    #         pass

    @pytest.mark.parametrize("protocol", protocols)
    def testClientProtocolConnectionMade(self, protocol):
        """
        Test the client protocol close
        :return:
        """
        protocol = protocol(ModbusSocketFramer(ClientDecoder()))
        transport = mock.MagicMock()
        protocol.connection_made(transport)
        assert protocol.transport == transport
        # assert protocol.connected
