"""Test transaction."""
from unittest import mock

from pymodbus.framer import (
    FramerAscii,
    FramerRTU,
    FramerSocket,
    FramerTLS,
)
from pymodbus.pdu import DecodePDU, ModbusPDU
from pymodbus.transaction.old_transaction import SyncModbusTransactionManager


TEST_MESSAGE = b"\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d"


class TestOldTransaction:  # pylint: disable=too-many-public-methods
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
