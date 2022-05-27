#!/usr/bin/env python3
"""Test all messages."""
import unittest
from pymodbus.constants import Defaults
from pymodbus.bit_read_message import (
    ReadDiscreteInputsResponse,
    ReadCoilsResponse,
    ReadDiscreteInputsRequest,
    ReadCoilsRequest,
)
from pymodbus.bit_write_message import (
    WriteMultipleCoilsResponse,
    WriteSingleCoilResponse,
    WriteSingleCoilRequest,
    WriteMultipleCoilsRequest,
)
from pymodbus.register_read_message import (
    ReadWriteMultipleRegistersResponse,
    ReadInputRegistersResponse,
    ReadHoldingRegistersResponse,
    ReadInputRegistersRequest,
    ReadWriteMultipleRegistersRequest,
    ReadHoldingRegistersRequest,
)
from pymodbus.register_write_message import (
    WriteMultipleRegistersResponse,
    WriteSingleRegisterResponse,
    WriteMultipleRegistersRequest,
    WriteSingleRegisterRequest,
)

# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class ModbusAllMessagesTests(unittest.TestCase):
    """All messages tests."""

    # -----------------------------------------------------------------------#
    #  Setup/TearDown
    # -----------------------------------------------------------------------#

    def setUp(self):
        """Initialize the test environment and builds request/result encoding pairs."""
        arguments = {
            "read_address": 1,
            "read_count": 1,
            "write_address": 1,
            "write_registers": 1,
        }
        self.requests = [
            lambda unit: ReadCoilsRequest(1, 5, unit=unit),
            lambda unit: ReadDiscreteInputsRequest(1, 5, unit=unit),
            lambda unit: WriteSingleCoilRequest(1, 1, unit=unit),
            lambda unit: WriteMultipleCoilsRequest(1, [1], unit=unit),
            lambda unit: ReadHoldingRegistersRequest(1, 5, unit=unit),
            lambda unit: ReadInputRegistersRequest(1, 5, unit=unit),
            lambda unit: ReadWriteMultipleRegistersRequest(unit=unit, **arguments),
            lambda unit: WriteSingleRegisterRequest(1, 1, unit=unit),
            lambda unit: WriteMultipleRegistersRequest(1, [1], unit=unit),
        ]
        self.responses = [
            lambda unit: ReadCoilsResponse([1], unit=unit),
            lambda unit: ReadDiscreteInputsResponse([1], unit=unit),
            lambda unit: WriteSingleCoilResponse(1, 1, unit=unit),
            lambda unit: WriteMultipleCoilsResponse(1, [1], unit=unit),
            lambda unit: ReadHoldingRegistersResponse([1], unit=unit),
            lambda unit: ReadInputRegistersResponse([1], unit=unit),
            lambda unit: ReadWriteMultipleRegistersResponse([1], unit=unit),
            lambda unit: WriteSingleRegisterResponse(1, 1, unit=unit),
            lambda unit: WriteMultipleRegistersResponse(1, 1, unit=unit),
        ]

    def tearDown(self):
        """Clean up the test environment"""

    def test_initializing_slave_address_request(self):
        """Test that every request can initialize the unit id"""
        unit_id = 0x12
        for factory in self.requests:
            request = factory(unit_id)
            self.assertEqual(request.unit_id, unit_id)

    def test_initializing_slave_address_response(self):
        """Test that every response can initialize the unit id"""
        unit_id = 0x12
        for factory in self.responses:
            response = factory(unit_id)
            self.assertEqual(response.unit_id, unit_id)

    def test_forwarding_kwargs_to_pdu(self):
        """Test that the kwargs are forwarded to the pdu correctly"""
        request = ReadCoilsRequest(1, 5, unit=0x12, transaction=0x12, protocol=0x12)
        self.assertEqual(request.unit_id, 0x12)
        self.assertEqual(request.transaction_id, 0x12)
        self.assertEqual(request.protocol_id, 0x12)

        request = ReadCoilsRequest(1, 5)
        self.assertEqual(request.unit_id, Defaults.UnitId)
        self.assertEqual(request.transaction_id, Defaults.TransactionId)
        self.assertEqual(request.protocol_id, Defaults.ProtocolId)
