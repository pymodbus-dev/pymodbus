#!/usr/bin/env python3
"""Test datastore."""
import unittest
import random
from unittest.mock import MagicMock
import redis
from pymodbus.datastore import (
    ModbusServerContext,
    ModbusSlaveContext,
    ModbusSequentialDataBlock,
    ModbusSparseDataBlock,
)
from pymodbus.datastore.store import BaseModbusDataBlock
from pymodbus.datastore.database import SqlSlaveContext
from pymodbus.datastore.database import RedisSlaveContext
from pymodbus.exceptions import NotImplementedException
from pymodbus.exceptions import NoSuchSlaveException
from pymodbus.exceptions import ParameterException


class ModbusDataStoreTest(unittest.TestCase):
    """Unittest for the pymodbus.datastore module."""

    def setUp(self):
        """Do setup."""

    def tearDown(self):
        """Clean up the test environment"""

    def test_modbus_data_block(self):
        """Test a base data block store"""
        block = BaseModbusDataBlock()
        block.default(10, True)

        self.assertNotEqual(str(block), None)
        self.assertEqual(block.default_value, True)
        self.assertEqual(block.values, [True] * 10)

        block.default_value = False
        block.reset()
        self.assertEqual(block.values, [False] * 10)

    def test_modbus_data_block_iterate(self):
        """Test a base data block store"""
        block = BaseModbusDataBlock()
        block.default(10, False)
        for _, value in block:
            self.assertEqual(value, False)

        block.values = {0: False, 2: False, 3: False}
        for _, value in block:
            self.assertEqual(value, False)

    def test_modbus_data_block_other(self):
        """Test a base data block store"""
        block = BaseModbusDataBlock()
        self.assertRaises(NotImplementedException, lambda: block.validate(1, 1))
        self.assertRaises(NotImplementedException, lambda: block.getValues(1, 1))
        self.assertRaises(NotImplementedException, lambda: block.setValues(1, 1))

    def test_modbus_sequential_data_block(self):
        """Test a sequential data block store"""
        block = ModbusSequentialDataBlock(0x00, [False] * 10)
        self.assertFalse(block.validate(-1, 0))
        self.assertFalse(block.validate(0, 20))
        self.assertFalse(block.validate(10, 1))
        self.assertTrue(block.validate(0x00, 10))

        block.setValues(0x00, True)
        self.assertEqual(block.getValues(0x00, 1), [True])

        block.setValues(0x00, [True] * 10)
        self.assertEqual(block.getValues(0x00, 10), [True] * 10)

    def test_modbus_sequential_data_block_factory(self):
        """Test the sequential data block store factory"""
        block = ModbusSequentialDataBlock.create()
        self.assertEqual(block.getValues(0x00, 65536), [False] * 65536)
        block = ModbusSequentialDataBlock(0x00, 0x01)
        self.assertEqual(block.values, [0x01])

    def test_modbus_sparse_data_block(self):
        """Test a sparse data block store"""
        values = dict(enumerate([True] * 10))
        block = ModbusSparseDataBlock(values)
        self.assertFalse(block.validate(-1, 0))
        self.assertFalse(block.validate(0, 20))
        self.assertFalse(block.validate(10, 1))
        self.assertTrue(block.validate(0x00, 10))
        self.assertTrue(block.validate(0x00, 10))
        self.assertFalse(block.validate(0, 0))
        self.assertFalse(block.validate(5, 0))

        block.setValues(0x00, True)
        self.assertEqual(block.getValues(0x00, 1), [True])

        block.setValues(0x00, [True] * 10)
        self.assertEqual(block.getValues(0x00, 10), [True] * 10)

        block.setValues(0x00, dict(enumerate([False] * 10)))
        self.assertEqual(block.getValues(0x00, 10), [False] * 10)

        block = ModbusSparseDataBlock({3: [10, 11, 12], 10: 1, 15: [0] * 4})
        self.assertEqual(
            block.values, {3: 10, 4: 11, 5: 12, 10: 1, 15: 0, 16: 0, 17: 0, 18: 0}
        )
        self.assertEqual(
            block.default_value,
            {3: 10, 4: 11, 5: 12, 10: 1, 15: 0, 16: 0, 17: 0, 18: 0},
        )
        self.assertEqual(block.mutable, True)
        block.setValues(3, [20, 21, 22, 23], use_as_default=True)
        self.assertEqual(block.getValues(3, 4), [20, 21, 22, 23])
        self.assertEqual(
            block.default_value,
            {3: 20, 4: 21, 5: 22, 6: 23, 10: 1, 15: 0, 16: 0, 17: 0, 18: 0},
        )
        # check when values is a dict, address is ignored
        block.setValues(0, {5: 32, 7: 43})
        self.assertEqual(block.getValues(5, 3), [32, 23, 43])

        # assertEqual value is empty dict when initialized without params
        block = ModbusSparseDataBlock()
        self.assertEqual(block.values, {})

        # mark block as unmutable and see if parameter exception
        # is raised for invalid offset writes
        block = ModbusSparseDataBlock({1: 100}, mutable=False)
        self.assertRaises(ParameterException, block.setValues, 0, 1)
        self.assertRaises(ParameterException, block.setValues, 0, {2: 100})
        self.assertRaises(ParameterException, block.setValues, 0, [1] * 10)

        # Reset datablock
        block = ModbusSparseDataBlock({3: [10, 11, 12], 10: 1, 15: [0] * 4})
        block.setValues(0, {3: [20, 21, 22], 10: 11, 15: [10] * 4})
        self.assertEqual(
            block.values, {3: 20, 4: 21, 5: 22, 10: 11, 15: 10, 16: 10, 17: 10, 18: 10}
        )
        block.reset()
        self.assertEqual(
            block.values, {3: 10, 4: 11, 5: 12, 10: 1, 15: 0, 16: 0, 17: 0, 18: 0}
        )

    def test_modbus_sparse_data_block_factory(self):
        """Test the sparse data block store factory"""
        block = ModbusSparseDataBlock.create([0x00] * 65536)
        self.assertEqual(block.getValues(0x00, 65536), [False] * 65536)

    def test_modbus_sparse_data_block_other(self):
        """Test modbus sparce data block."""
        block = ModbusSparseDataBlock([True] * 10)
        self.assertEqual(block.getValues(0x00, 10), [True] * 10)
        self.assertRaises(ParameterException, lambda: ModbusSparseDataBlock(True))

    def test_modbus_slave_context(self):
        """Test a modbus slave context"""
        store = {
            "di": ModbusSequentialDataBlock(0, [False] * 10),
            "co": ModbusSequentialDataBlock(0, [False] * 10),
            "ir": ModbusSequentialDataBlock(0, [False] * 10),
            "hr": ModbusSequentialDataBlock(0, [False] * 10),
        }
        context = ModbusSlaveContext(**store)
        self.assertNotEqual(str(context), None)

        for i in (1, 2, 3, 4):
            context.setValues(i, 0, [True] * 10)
            self.assertTrue(context.validate(i, 0, 10))
            self.assertEqual(context.getValues(i, 0, 10), [True] * 10)
        context.reset()

        for i in (1, 2, 3, 4):
            self.assertTrue(context.validate(i, 0, 10))
            self.assertEqual(context.getValues(i, 0, 10), [False] * 10)

    def test_modbus_server_context(self):
        """Test a modbus server context"""

        def _set(ctx):
            ctx[0xFFFF] = None

        context = ModbusServerContext(single=False)
        self.assertRaises(NoSuchSlaveException, lambda: _set(context))
        self.assertRaises(NoSuchSlaveException, lambda: context[0xFFFF])


class RedisDataStoreTest(unittest.TestCase):
    """Unittest for the pymodbus.datastore.database.redis module."""

    def setUp(self):
        """Do setup."""
        self.slave = RedisSlaveContext()

    def tearDown(self):
        """Clean up the test environment"""

    def test_str(self):
        """Test string."""
        # slave = RedisSlaveContext()
        self.assertEqual(str(self.slave), f"Redis Slave Context {self.slave.client}")

    def test_reset(self):
        """Test reset."""
        self.assertTrue(isinstance(self.slave.client, redis.Redis))
        self.slave.client = MagicMock()
        self.slave.reset()
        self.slave.client.flushall.assert_called_once_with()

    def test_val_callbacks_success(self):
        """Test value callbacks success."""
        self.slave._build_mapping()  # pylint: disable=protected-access
        mock_count = 3
        mock_offset = 0
        self.slave.client.mset = MagicMock()
        self.slave.client.mget = MagicMock(return_value=["11"])

        for key in ("d", "c", "h", "i"):
            self.assertTrue(
                self.slave._val_callbacks[key](  # pylint: disable=protected-access
                    mock_offset, mock_count
                )
            )

    def test_val_callbacks_failure(self):
        """Test value callbacks failure."""
        self.slave._build_mapping()  # pylint: disable=protected-access
        mock_count = 3
        mock_offset = 0
        self.slave.client.mset = MagicMock()
        self.slave.client.mget = MagicMock(return_value=["11", None])

        for key in ("d", "c", "h", "i"):
            self.assertFalse(
                self.slave._val_callbacks[key](  # pylint: disable=protected-access
                    mock_offset, mock_count
                )
            )

    def test_get_callbacks(self):
        """Test get callbacks."""
        self.slave._build_mapping()  # pylint: disable=protected-access
        mock_count = 3
        mock_offset = 0
        self.slave.client.mget = MagicMock(return_value="11")

        for key in ("d", "c"):
            resp = self.slave._get_callbacks[key](  # pylint: disable=protected-access
                mock_offset, mock_count
            )
            self.assertEqual(resp, [True, False, False])

        for key in ("h", "i"):
            resp = self.slave._get_callbacks[key](  # pylint: disable=protected-access
                mock_offset, mock_count
            )
            self.assertEqual(resp, ["1", "1"])

    def test_set_callbacks(self):
        """Test set callbacks."""
        self.slave._build_mapping()  # pylint: disable=protected-access
        mock_values = [3]
        mock_offset = 0
        self.slave.client.mset = MagicMock()
        self.slave.client.mget = MagicMock()

        for key in ("c", "d"):
            self.slave._set_callbacks[key](  # pylint: disable=protected-access
                mock_offset, [3]
            )
            k = f"pymodbus:{key}:{mock_offset}"
            self.slave.client.mset.assert_called_with({k: "\x01"})

        for key in ("h", "i"):
            self.slave._set_callbacks[key](  # pylint: disable=protected-access
                mock_offset, [3]
            )
            k = f"pymodbus:{key}:{mock_offset}"
            self.slave.client.mset.assert_called_with({k: mock_values[0]})

    def test_validate(self):
        """Test validate."""
        self.slave.client.mget = MagicMock(return_value=[123])
        self.assertTrue(self.slave.validate(0x01, 3000))

    def test_set_value(self):
        """Test set value."""
        self.slave.client.mset = MagicMock()
        self.slave.client.mget = MagicMock()
        self.assertEqual(self.slave.setValues(0x01, 1000, [12]), None)

    def test_get_value(self):
        """Test get value."""
        self.slave.client.mget = MagicMock(return_value=["123"])
        self.assertEqual(self.slave.getValues(0x01, 23), [])


class MockSqlResult:  # pylint: disable=too-few-public-methods
    """Mock SQL Result."""

    def __init__(self, rowcount=0, value=0):
        """Initialize."""
        self.rowcount = rowcount
        self.value = value


class SqlDataStoreTest(unittest.TestCase):
    """Unittest for the pymodbus.datastore.database.SqlSlaveContext module."""

    def setUp(self):
        """Do setup."""
        self.slave = SqlSlaveContext()
        self.slave._metadata.drop_all = MagicMock()  # pylint: disable=protected-access
        self.slave._db_create = MagicMock()  # pylint: disable=protected-access
        self.slave._table.select = MagicMock()  # pylint: disable=protected-access
        self.slave._connection = MagicMock()  # pylint: disable=protected-access

        self.mock_addr = random.randint(0, 65000)  # NOSONAR # nosec
        self.mock_values = random.sample(range(1, 100), 5)  # NOSONAR # nosec
        self.mock_function = 0x01
        self.mock_type = "h"
        self.mock_offset = 0
        self.mock_count = 1

        self.function_map = {2: "d", 4: "i"}
        self.function_map.update([(i, "h") for i in (3, 6, 16, 22, 23)])
        self.function_map.update([(i, "c") for i in (1, 5, 15)])

    def tearDown(self):
        """Clean up the test environment"""

    def test_str(self):
        """Test string."""
        self.assertEqual(str(self.slave), "Modbus Slave Context")

    def test_reset(self):
        """Test reset."""
        self.slave.reset()

        self.slave._metadata.drop_all.assert_called_once_with()  # pylint: disable=protected-access
        self.slave._db_create.assert_called_once_with(  # pylint: disable=protected-access
            self.slave.table, self.slave.database
        )

    def test_validate_success(self):
        """Test validate success."""
        self.slave._connection.execute.return_value.fetchall.return_value = (  # pylint: disable=protected-access
            self.mock_values
        )
        self.assertTrue(
            self.slave.validate(
                self.mock_function, self.mock_addr, len(self.mock_values)
            )
        )

    def test_validate_failure(self):
        """Test validate failure."""
        wrong_count = 9
        self.slave._connection.execute.return_value.fetchall.return_value = (  # pylint: disable=protected-access
            self.mock_values
        )
        self.assertFalse(
            self.slave.validate(self.mock_function, self.mock_addr, wrong_count)
        )

    def test_build_set(self):
        """Test build set."""
        mock_set = [
            {"index": 0, "type": "h", "value": 11},
            {"index": 1, "type": "h", "value": 12},
        ]
        self.assertListEqual(
            self.slave._build_set("h", 0, [11, 12]), mock_set  # pylint: disable=protected-access
        )

    def test_check_success(self):
        """Test check success."""
        mock_success_results = [1, 2, 3]
        self.slave._get = MagicMock(  # pylint: disable=protected-access
            return_value=mock_success_results
        )
        self.assertFalse(
            self.slave._check("h", 0, 1)  # pylint: disable=protected-access
        )

    def test_check_failure(self):
        """Test check failure."""
        mock_success_results = []
        self.slave._get = MagicMock(  # pylint: disable=protected-access
            return_value=mock_success_results
        )
        self.assertTrue(
            self.slave._check("h", 0, 1)  # pylint: disable=protected-access
        )

    def test_get_values(self):
        """Test get values."""
        self.slave._get = MagicMock()  # pylint: disable=protected-access

        for key, value in self.function_map.items():
            self.slave.getValues(key, self.mock_addr, self.mock_count)
            self.slave._get.assert_called_with(  # pylint: disable=protected-access
                value, self.mock_addr + 1, self.mock_count
            )

    def test_set_values(self):
        """Test set values."""
        self.slave._set = MagicMock()  # pylint: disable=protected-access

        for key, value in self.function_map.items():
            self.slave.setValues(key, self.mock_addr, self.mock_values, update=False)
            self.slave._set.assert_called_with(  # pylint: disable=protected-access
                value, self.mock_addr + 1, self.mock_values
            )

    def test_set(self):
        """Test set."""
        self.slave._check = MagicMock(  # pylint: disable=protected-access
            return_value=True
        )
        self.slave._connection.execute = MagicMock(  # pylint: disable=protected-access
            return_value=MockSqlResult(rowcount=len(self.mock_values))
        )
        self.assertTrue(
            self.slave._set(  # pylint: disable=protected-access
                self.mock_type, self.mock_offset, self.mock_values
            )
        )

        self.slave._check = MagicMock(  # pylint: disable=protected-access
            return_value=False
        )
        self.assertFalse(
            self.slave._set(  # pylint: disable=protected-access
                self.mock_type, self.mock_offset, self.mock_values
            )
        )

    def test_update_success(self):
        """Test update success."""
        self.slave._connection.execute = MagicMock(  # pylint: disable=protected-access
            return_value=MockSqlResult(rowcount=len(self.mock_values))
        )
        self.assertTrue(
            self.slave._update(  # pylint: disable=protected-access
                self.mock_type, self.mock_offset, self.mock_values
            )
        )

    def test_update_failure(self):
        """Test update failure."""
        self.slave._connection.execute = MagicMock(  # pylint: disable=protected-access
            return_value=MockSqlResult(rowcount=100)
        )
        self.assertFalse(
            self.slave._update(  # pylint: disable=protected-access
                self.mock_type, self.mock_offset, self.mock_values
            )
        )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
