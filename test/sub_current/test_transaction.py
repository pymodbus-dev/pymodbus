"""Test transaction."""
from unittest import mock

from pymodbus.exceptions import (
    ModbusIOException,
)
from pymodbus.framer import (
    FramerAscii,
    FramerRTU,
    FramerSocket,
    FramerTLS,
)
from pymodbus.pdu import DecodePDU, ModbusPDU
from pymodbus.transaction import (
    ModbusTransactionManager,
    SyncModbusTransactionManager,
)


TEST_MESSAGE = b"\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d"


class TestTransaction:  # pylint: disable=too-many-public-methods
    """Unittest for the pymodbus.transaction module."""

    client = None
    decoder = None
    _tcp = None
    _tls = None
    _rtu = None
    _ascii = None
    _manager = None
    _tm = None

    # ----------------------------------------------------------------------- #
    # Test Construction
    # ----------------------------------------------------------------------- #
    def setup_method(self):
        """Set up the test environment."""
        self.decoder = DecodePDU(True)
        self._tcp = FramerSocket(self.decoder)
        self._tls = FramerTLS(self.decoder)
        self._rtu = FramerRTU(self.decoder)
        self._ascii = FramerAscii(self.decoder)
        client = mock.MagicMock()
        client.framer = self._rtu
        self._manager = SyncModbusTransactionManager(client, 3)

    # ----------------------------------------------------------------------- #
    # Modbus transaction manager
    # ----------------------------------------------------------------------- #

    @mock.patch.object(SyncModbusTransactionManager, "_recv")
    @mock.patch.object(ModbusTransactionManager, "getTransaction")
    def test_execute(self, mock_get_transaction, mock_recv):
        """Test execute."""
        client = mock.MagicMock()
        client.framer = self._ascii
        client.framer._buffer = b"deadbeef"  # pylint: disable=protected-access
        client.framer.processIncomingFrame = mock.MagicMock()
        client.framer.processIncomingFrame.return_value = 0, None
        client.framer.buildFrame = mock.MagicMock()
        client.framer.buildFrame.return_value = b"deadbeef"
        client.send = mock.MagicMock()
        client.send.return_value = len(b"deadbeef")
        request = mock.MagicMock()
        request.get_response_pdu_size.return_value = 10
        request.slave_id = 1
        request.function_code = 222
        trans = SyncModbusTransactionManager(client, 3)
        mock_recv.reset_mock(
            return_value=b"abcdef"
        )
        assert trans.retries == 3

        mock_get_transaction.return_value = b"response"
        response = trans.execute(False, request)
        assert response == b"response"
        # No response
        mock_recv.reset_mock(
            return_value=b"abcdef"
        )
        trans.transactions = {}
        mock_get_transaction.return_value = None
        response = trans.execute(False, request)
        assert isinstance(response, ModbusIOException)

        # No response with retries
        mock_recv.reset_mock(
            side_effect=iter([b"", b"abcdef"])
        )
        response = trans.execute(False, request)
        assert isinstance(response, ModbusIOException)

        # wrong handle_local_echo
        mock_recv.reset_mock(
            side_effect=iter([b"abcdef", b"deadbe", b"123456"])
        )
        client.comm_params.handle_local_echo = True
        assert trans.execute(False, request).message == "[Input/Output] Wrong local echo"
        client.comm_params.handle_local_echo = False

        # retry on invalid response
        mock_recv.reset_mock(
            side_effect=iter([b"", b"abcdef", b"deadbe", b"123456"])
        )
        response = trans.execute(False, request)
        assert isinstance(response, ModbusIOException)

        # Unable to decode response
        mock_recv.reset_mock(
            side_effect=ModbusIOException()
        )
        client.framer.processIncomingFrame.side_effect = mock.MagicMock(
            side_effect=ModbusIOException()
        )
        assert isinstance(trans.execute(False, request), ModbusIOException)

    def test_transaction_manager_tid(self):
        """Test the transaction manager TID."""
        for tid in range(1, self._manager.getNextTID() + 10):
            assert tid + 1 == self._manager.getNextTID()
        self._manager.reset()
        assert self._manager.getNextTID() == 1

    def test_get_transaction_manager_transaction(self):
        """Test the getting a transaction from the transaction manager."""
        self._manager.reset()
        handle = ModbusPDU(transaction_id=self._manager.getNextTID(), slave_id=0)
        self._manager.addTransaction(handle)
        result = self._manager.getTransaction(handle.transaction_id)
        assert handle is result

    def test_delete_transaction_manager_transaction(self):
        """Test deleting a transaction from the dict transaction manager."""
        self._manager.reset()
        handle = ModbusPDU(transaction_id=self._manager.getNextTID(), slave_id=0)
        self._manager.addTransaction(handle)
        self._manager.delTransaction(handle.transaction_id)
        assert not self._manager.getTransaction(handle.transaction_id)
