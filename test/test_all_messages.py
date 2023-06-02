"""Test all messages."""
from pymodbus.bit_read_message import (
    ReadCoilsRequest,
    ReadCoilsResponse,
    ReadDiscreteInputsRequest,
    ReadDiscreteInputsResponse,
)
from pymodbus.bit_write_message import (
    WriteMultipleCoilsRequest,
    WriteMultipleCoilsResponse,
    WriteSingleCoilRequest,
    WriteSingleCoilResponse,
)
from pymodbus.constants import Defaults
from pymodbus.register_read_message import (
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
    ReadInputRegistersRequest,
    ReadInputRegistersResponse,
    ReadWriteMultipleRegistersRequest,
    ReadWriteMultipleRegistersResponse,
)
from pymodbus.register_write_message import (
    WriteMultipleRegistersRequest,
    WriteMultipleRegistersResponse,
    WriteSingleRegisterRequest,
    WriteSingleRegisterResponse,
)


# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class TestAllMessages:
    """All messages tests."""

    # -----------------------------------------------------------------------#
    #  Setup/TearDown
    # -----------------------------------------------------------------------#

    requests = [
        lambda slave: ReadCoilsRequest(1, 5, slave=slave),
        lambda slave: ReadDiscreteInputsRequest(1, 5, slave=slave),
        lambda slave: WriteSingleCoilRequest(1, 1, slave=slave),
        lambda slave: WriteMultipleCoilsRequest(1, [1], slave=slave),
        lambda slave: ReadHoldingRegistersRequest(1, 5, slave=slave),
        lambda slave: ReadInputRegistersRequest(1, 5, slave=slave),
        lambda slave: ReadWriteMultipleRegistersRequest(
            slave=slave,
            read_address=1,
            read_count=1,
            write_address=1,
            write_registers=1,
        ),
        lambda slave: WriteSingleRegisterRequest(1, 1, slave=slave),
        lambda slave: WriteMultipleRegistersRequest(1, [1], slave=slave),
    ]
    responses = [
        lambda slave: ReadCoilsResponse([1], slave=slave),
        lambda slave: ReadDiscreteInputsResponse([1], slave=slave),
        lambda slave: WriteSingleCoilResponse(1, 1, slave=slave),
        lambda slave: WriteMultipleCoilsResponse(1, [1], slave=slave),
        lambda slave: ReadHoldingRegistersResponse([1], slave=slave),
        lambda slave: ReadInputRegistersResponse([1], slave=slave),
        lambda slave: ReadWriteMultipleRegistersResponse([1], slave=slave),
        lambda slave: WriteSingleRegisterResponse(1, 1, slave=slave),
        lambda slave: WriteMultipleRegistersResponse(1, 1, slave=slave),
    ]

    def test_initializing_slave_address_request(self):
        """Test that every request can initialize the slave id"""
        slave_id = 0x12
        for factory in self.requests:
            request = factory(slave_id)
            assert request.slave_id == slave_id

    def test_initializing_slave_address_response(self):
        """Test that every response can initialize the slave id"""
        slave_id = 0x12
        for factory in self.responses:
            response = factory(slave_id)
            assert response.slave_id == slave_id

    def test_forwarding_kwargs_to_pdu(self):
        """Test that the kwargs are forwarded to the pdu correctly"""
        request = ReadCoilsRequest(1, 5, slave=0x12, transaction=0x12, protocol=0x12)
        assert request.slave_id == 0x12
        assert request.transaction_id == 0x12
        assert request.protocol_id == 0x12

        request = ReadCoilsRequest(1, 5)
        assert request.slave_id == Defaults.Slave
        assert request.transaction_id == Defaults.TransactionId
        assert request.protocol_id == Defaults.ProtocolId
