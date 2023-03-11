"""Test datastore."""
import random
from test import mock

import pytest
import redis

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
    ModbusSparseDataBlock,
)
from pymodbus.datastore.database import RedisSlaveContext, SqlSlaveContext
from pymodbus.datastore.store import BaseModbusDataBlock
from pymodbus.exceptions import (
    NoSuchSlaveException,
    NotImplementedException,
    ParameterException,
)


class TestDataStore:
    """Unittest for the pymodbus.datastore module."""

    def test_modbus_data_block(self):
        """Test a base data block store"""
        block = BaseModbusDataBlock()
        block.default(10, True)

        assert str(block)
        assert block.default_value
        assert block.values == [True] * 10

        block.default_value = False
        block.reset()
        assert block.values == [False] * 10

    def test_modbus_data_block_iterate(self):
        """Test a base data block store"""
        block = BaseModbusDataBlock()
        block.default(10, False)
        for _, value in block:
            assert not value

        block.values = {0: False, 2: False, 3: False}
        for _, value in block:
            assert not value

    def test_modbus_data_block_other(self):
        """Test a base data block store"""
        block = BaseModbusDataBlock()
        with pytest.raises(NotImplementedException):
            block.validate(1, 1)
        with pytest.raises(NotImplementedException):
            block.getValues(1, 1)
        with pytest.raises(NotImplementedException):
            block.setValues(1, 1)

    def test_modbus_sequential_data_block(self):
        """Test a sequential data block store"""
        block = ModbusSequentialDataBlock(0x00, [False] * 10)
        assert not block.validate(-1, 0)
        assert not block.validate(0, 20)
        assert not block.validate(10, 1)
        assert block.validate(0x00, 10)

        block.setValues(0x00, True)
        assert block.getValues(0x00, 1) == [True]

        block.setValues(0x00, [True] * 10)
        assert block.getValues(0x00, 10) == [True] * 10

    def test_modbus_sequential_data_block_factory(self):
        """Test the sequential data block store factory"""
        block = ModbusSequentialDataBlock.create()
        assert block.getValues(0x00, 65536) == [False] * 65536
        block = ModbusSequentialDataBlock(0x00, 0x01)
        assert block.values == [0x01]

    def test_modbus_sparse_data_block(self):
        """Test a sparse data block store"""
        values = dict(enumerate([True] * 10))
        block = ModbusSparseDataBlock(values)
        assert not block.validate(-1, 0)
        assert not block.validate(0, 20)
        assert not block.validate(10, 1)
        assert block.validate(0x00, 10)
        assert block.validate(0x00, 10)
        assert not block.validate(0, 0)
        assert not block.validate(5, 0)

        block.setValues(0x00, True)
        assert block.getValues(0x00, 1) == [True]

        block.setValues(0x00, [True] * 10)
        assert block.getValues(0x00, 10) == [True] * 10

        block.setValues(0x00, dict(enumerate([False] * 10)))
        assert block.getValues(0x00, 10) == [False] * 10

        block = ModbusSparseDataBlock({3: [10, 11, 12], 10: 1, 15: [0] * 4})
        assert block.values == {3: 10, 4: 11, 5: 12, 10: 1, 15: 0, 16: 0, 17: 0, 18: 0}
        assert block.default_value == {
            3: 10,
            4: 11,
            5: 12,
            10: 1,
            15: 0,
            16: 0,
            17: 0,
            18: 0,
        }
        assert block.mutable
        block.setValues(3, [20, 21, 22, 23], use_as_default=True)
        assert block.getValues(3, 4) == [20, 21, 22, 23]
        assert block.default_value == {
            3: 20,
            4: 21,
            5: 22,
            6: 23,
            10: 1,
            15: 0,
            16: 0,
            17: 0,
            18: 0,
        }

        # check when values is a dict, address is ignored
        block.setValues(0, {5: 32, 7: 43})
        assert block.getValues(5, 3) == [32, 23, 43]

        # assertEqual value is empty dict when initialized without params
        block = ModbusSparseDataBlock()
        assert block.values == {}

        # mark block as unmutable and see if parameter exception
        # is raised for invalid offset writes
        block = ModbusSparseDataBlock({1: 100}, mutable=False)
        with pytest.raises(ParameterException):
            block.setValues(0, 1)
        with pytest.raises(ParameterException):
            block.setValues(0, {2: 100})
        with pytest.raises(ParameterException):
            block.setValues(0, [1] * 10)

        # Reset datablock
        block = ModbusSparseDataBlock({3: [10, 11, 12], 10: 1, 15: [0] * 4})
        block.setValues(0, {3: [20, 21, 22], 10: 11, 15: [10] * 4})
        assert block.values == {
            3: 20,
            4: 21,
            5: 22,
            10: 11,
            15: 10,
            16: 10,
            17: 10,
            18: 10,
        }
        block.reset()
        assert block.values == {3: 10, 4: 11, 5: 12, 10: 1, 15: 0, 16: 0, 17: 0, 18: 0}

    def test_modbus_sparse_data_block_factory(self):
        """Test the sparse data block store factory"""
        block = ModbusSparseDataBlock.create([0x00] * 65536)
        assert block.getValues(0x00, 65536) == [False] * 65536

    def test_modbus_sparse_data_block_other(self):
        """Test modbus sparce data block."""
        block = ModbusSparseDataBlock([True] * 10)
        assert block.getValues(0x00, 10) == [True] * 10
        with pytest.raises(ParameterException):
            ModbusSparseDataBlock(True)

    def test_modbus_slave_context(self):
        """Test a modbus slave context"""
        store = {
            "di": ModbusSequentialDataBlock(0, [False] * 10),
            "co": ModbusSequentialDataBlock(0, [False] * 10),
            "ir": ModbusSequentialDataBlock(0, [False] * 10),
            "hr": ModbusSequentialDataBlock(0, [False] * 10),
        }
        context = ModbusSlaveContext(**store)
        assert str(context)

        for i in (1, 2, 3, 4):
            context.setValues(i, 0, [True] * 10)
            assert context.validate(i, 0, 10)
            assert context.getValues(i, 0, 10) == [True] * 10
        context.reset()

        for i in (1, 2, 3, 4):
            assert context.validate(i, 0, 10)
            assert context.getValues(i, 0, 10) == [False] * 10

    def test_modbus_server_context(self):
        """Test a modbus server context"""

        def _set(ctx):
            ctx[0xFFFF] = None

        context = ModbusServerContext(single=False)
        with pytest.raises(NoSuchSlaveException):
            _set(context)
        with pytest.raises(NoSuchSlaveException):
            context[0xFFFF]  # pylint: disable=pointless-statement


class TestRedisDataStore:
    """Unittest for the pymodbus.datastore.database.redis module."""

    slave = RedisSlaveContext()

    def test_str(self):
        """Test string."""
        # slave = RedisSlaveContext()
        assert str(self.slave) == f"Redis Slave Context {self.slave.client}"

    def test_reset(self):
        """Test reset."""
        assert isinstance(self.slave.client, redis.Redis)
        self.slave.client = mock.MagicMock()
        self.slave.reset()
        self.slave.client.flushall.assert_called_once_with()

    def test_val_callbacks_success(self):
        """Test value callbacks success."""
        self.slave._build_mapping()  # pylint: disable=protected-access
        mock_count = 3
        mock_offset = 0
        self.slave.client.mset = mock.MagicMock()
        self.slave.client.mget = mock.MagicMock(return_value=["11"])

        for key in ("d", "c", "h", "i"):
            assert self.slave._val_callbacks[key](  # pylint: disable=protected-access
                mock_offset, mock_count
            )

    def test_val_callbacks_failure(self):
        """Test value callbacks failure."""
        self.slave._build_mapping()  # pylint: disable=protected-access
        mock_count = 3
        mock_offset = 0
        self.slave.client.mset = mock.MagicMock()
        self.slave.client.mget = mock.MagicMock(return_value=["11", None])

        for key in ("d", "c", "h", "i"):
            assert not self.slave._val_callbacks[  # pylint: disable=protected-access
                key
            ](mock_offset, mock_count)

    def test_get_callbacks(self):
        """Test get callbacks."""
        self.slave._build_mapping()  # pylint: disable=protected-access
        mock_count = 3
        mock_offset = 0
        self.slave.client.mget = mock.MagicMock(return_value="11")

        for key in ("d", "c"):
            resp = self.slave._get_callbacks[key](  # pylint: disable=protected-access
                mock_offset, mock_count
            )
            assert resp == [True, False, False]

        for key in ("h", "i"):
            resp = self.slave._get_callbacks[key](  # pylint: disable=protected-access
                mock_offset, mock_count
            )
            assert resp == ["1", "1"]

    def test_set_callbacks(self):
        """Test set callbacks."""
        self.slave._build_mapping()  # pylint: disable=protected-access
        mock_values = [3]
        mock_offset = 0
        self.slave.client.mset = mock.MagicMock()
        self.slave.client.mget = mock.MagicMock()

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
        self.slave.client.mget = mock.MagicMock(return_value=[123])
        assert self.slave.validate(0x01, 3000)

    def test_set_value(self):
        """Test set value."""
        self.slave.client.mset = mock.MagicMock()
        self.slave.client.mget = mock.MagicMock()
        assert not self.slave.setValues(0x01, 1000, [12])

    def test_get_value(self):
        """Test get value."""
        self.slave.client.mget = mock.MagicMock(return_value=["123"])
        assert self.slave.getValues(0x01, 23) == []


class MockSqlResult:  # pylint: disable=too-few-public-methods
    """Mock SQL Result."""

    def __init__(self, rowcount=0, value=0):
        """Initialize."""
        self.rowcount = rowcount
        self.value = value


class SqlDataStoreTest:
    """Unittest for the pymodbus.datastore.database.SqlSlaveContext module."""

    class SQLslave:  # pylint: disable=too-few-public-methods
        """Single test setup."""

        def __init__(self):
            """Prepare test."""
            self.slave = SqlSlaveContext()
            self.slave._metadata.drop_all = mock.MagicMock()
            self.slave._db_create = mock.MagicMock()
            self.slave._table.select = mock.MagicMock()
            self.slave._connection = mock.MagicMock()

            self.mock_addr = random.randint(0, 65000)
            self.mock_values = random.sample(range(1, 100), 5)
            self.mock_function = 0x01
            self.mock_type = "h"
            self.mock_offset = 0
            self.mock_count = 1

            self.function_map = {2: "d", 4: "i"}
            self.function_map.update([(i, "h") for i in (3, 6, 16, 22, 23)])
            self.function_map.update([(i, "c") for i in (1, 5, 15)])

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_str(self):
        """Test string."""
        slave = self.SQLslave()
        assert str(slave.slave) == "Modbus Slave Context"

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_reset(self):
        """Test reset."""
        slave = self.SQLslave()
        slave.slave.reset()

        slave.slave._metadata.drop_all.assert_called_once_with()  # pylint: disable=protected-access
        slave.slave._db_create.assert_called_once_with(  # pylint: disable=protected-access
            slave.slave.table, slave.slave.database
        )

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_validate_success(self):
        """Test validate success."""
        slave = self.SQLslave()
        slave.slave._connection.execute.return_value.fetchall.return_value = (  # pylint: disable=protected-access
            slave.mock_values
        )
        assert slave.slave.validate(
            slave.mock_function, slave.mock_addr, len(slave.mock_values)
        )

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_validate_failure(self):
        """Test validate failure."""
        slave = self.SQLslave()
        wrong_count = 9
        slave.slave._connection.execute.return_value.fetchall.return_value = (  # pylint: disable=protected-access
            slave.mock_values
        )
        assert not slave.slave.validate(
            slave.mock_function, slave.mock_addr, wrong_count
        )

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_build_set(self):
        """Test build set."""
        slave = self.SQLslave()
        mock_set = [
            {"index": 0, "type": "h", "value": 11},
            {"index": 1, "type": "h", "value": 12},
        ]
        assert (
            slave.slave._build_set("h", 0, [11, 12])  # pylint: disable=protected-access
            == mock_set
        )

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_check_success(self):
        """Test check success."""
        slave = self.SQLslave()
        mock_success_results = [1, 2, 3]
        slave.slave._get = mock.MagicMock(  # pylint: disable=protected-access
            return_value=mock_success_results
        )
        assert not slave.slave._check("h", 0, 1)  # pylint: disable=protected-access

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_check_failure(self):
        """Test check failure."""
        slave = self.SQLslave()
        mock_success_results = []
        slave.slave._get = mock.MagicMock(  # pylint: disable=protected-access
            return_value=mock_success_results
        )
        assert slave.slave._check("h", 0, 1)  # pylint: disable=protected-access

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_get_values(self):
        """Test get values."""
        slave = self.SQLslave()
        slave.slave._get = mock.MagicMock()  # pylint: disable=protected-access

        for key, value in slave.function_map.items():
            slave.slave.getValues(key, slave.mock_addr, slave.mock_count)
            slave.slave._get.assert_called_with(  # pylint: disable=protected-access
                value, slave.mock_addr + 1, slave.mock_count
            )

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_set_values(self):
        """Test set values."""
        slave = self.SQLslave()
        slave.slave._set = mock.MagicMock()  # pylint: disable=protected-access

        for key, value in slave.function_map.items():
            slave.slave.setValues(key, slave.mock_addr, slave.mock_values, update=False)
            slave.slave._set.assert_called_with(  # pylint: disable=protected-access
                value, slave.mock_addr + 1, slave.mock_values
            )

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_set(self):
        """Test set."""
        slave = self.SQLslave()
        slave.slave._check = mock.MagicMock(  # pylint: disable=protected-access
            return_value=True
        )
        slave.slave._connection.execute = (  # pylint: disable=protected-access
            mock.MagicMock(return_value=MockSqlResult(rowcount=len(slave.mock_values)))
        )
        assert slave.slave._set(  # pylint: disable=protected-access
            slave.mock_type, slave.mock_offset, slave.mock_values
        )

        slave.slave._check = mock.MagicMock(  # pylint: disable=protected-access
            return_value=False
        )
        assert not slave.slave._set(  # pylint: disable=protected-access
            slave.mock_type, slave.mock_offset, slave.mock_values
        )

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_update_success(self):
        """Test update success."""
        slave = self.SQLslave()
        slave.slave._connection.execute = (  # pylint: disable=protected-access
            mock.MagicMock(return_value=MockSqlResult(rowcount=len(slave.mock_values)))
        )
        assert slave.slave._update(  # pylint: disable=protected-access
            slave.mock_type, slave.mock_offset, slave.mock_values
        )

    @pytest.mark.skip
    @pytest.mark.xdist_group(name="sql")
    def test_update_failure(self):
        """Test update failure."""
        slave = self.SQLslave()
        slave.slave._connection.execute = (  # pylint: disable=protected-access
            mock.MagicMock(return_value=MockSqlResult(rowcount=100))
        )
        assert not slave.slave._update(  # pylint: disable=protected-access
            slave.mock_type, slave.mock_offset, slave.mock_values
        )
