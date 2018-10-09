#!/usr/bin/env python
import unittest
import mock
from mock import MagicMock
import redis
import random
from pymodbus.datastore import *
from pymodbus.datastore.store import BaseModbusDataBlock
from pymodbus.datastore.database import SqlSlaveContext
from pymodbus.datastore.database import RedisSlaveContext
from pymodbus.exceptions import NotImplementedException
from pymodbus.exceptions import NoSuchSlaveException
from pymodbus.exceptions import ParameterException
from pymodbus.datastore.remote import RemoteSlaveContext

class ModbusDataStoreTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.datastore module
    '''

    def setUp(self):
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testModbusDataBlock(self):
        ''' Test a base data block store '''
        block = BaseModbusDataBlock()
        block.default(10, True)

        self.assertNotEqual(str(block), None)
        self.assertEqual(block.default_value, True)
        self.assertEqual(block.values, [True]*10)

        block.default_value = False
        block.reset()
        self.assertEqual(block.values, [False]*10)

    def testModbusDataBlockIterate(self):
        ''' Test a base data block store '''
        block = BaseModbusDataBlock()
        block.default(10, False)
        for idx,value in block:
            self.assertEqual(value, False)

        block.values = {0 : False, 2 : False, 3 : False }
        for idx,value in block:
            self.assertEqual(value, False)

    def testModbusDataBlockOther(self):
        ''' Test a base data block store '''
        block = BaseModbusDataBlock()
        self.assertRaises(NotImplementedException, lambda: block.validate(1,1))
        self.assertRaises(NotImplementedException, lambda: block.getValues(1,1))
        self.assertRaises(NotImplementedException, lambda: block.setValues(1,1))

    def testModbusSequentialDataBlock(self):
        ''' Test a sequential data block store '''
        block = ModbusSequentialDataBlock(0x00, [False]*10)
        self.assertFalse(block.validate(-1, 0))
        self.assertFalse(block.validate(0, 20))
        self.assertFalse(block.validate(10, 1))
        self.assertTrue(block.validate(0x00, 10))

        block.setValues(0x00, True)
        self.assertEqual(block.getValues(0x00, 1), [True])

        block.setValues(0x00, [True]*10)
        self.assertEqual(block.getValues(0x00, 10), [True]*10)

    def testModbusSequentialDataBlockFactory(self):
        ''' Test the sequential data block store factory '''
        block = ModbusSequentialDataBlock.create()
        self.assertEqual(block.getValues(0x00, 65536), [False]*65536)
        block = ModbusSequentialDataBlock(0x00, 0x01)
        self.assertEqual(block.values, [0x01])

    def testModbusSparseDataBlock(self):
        ''' Test a sparse data block store '''
        values = dict(enumerate([True]*10))
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

        block.setValues(0x00, [True]*10)
        self.assertEqual(block.getValues(0x00, 10), [True]*10)

        block.setValues(0x00, dict(enumerate([False]*10)))
        self.assertEqual(block.getValues(0x00, 10), [False]*10)

    def testModbusSparseDataBlockFactory(self):
        ''' Test the sparse data block store factory '''
        block = ModbusSparseDataBlock.create()
        self.assertEqual(block.getValues(0x00, 65536), [False]*65536)

    def testModbusSparseDataBlockOther(self):
        block = ModbusSparseDataBlock([True]*10)
        self.assertEqual(block.getValues(0x00, 10), [True]*10)
        self.assertRaises(ParameterException,
            lambda: ModbusSparseDataBlock(True))

    def testModbusSlaveContext(self):
        ''' Test a modbus slave context '''
        store = {
            'di' : ModbusSequentialDataBlock(0, [False]*10),
            'co' : ModbusSequentialDataBlock(0, [False]*10),
            'ir' : ModbusSequentialDataBlock(0, [False]*10),
            'hr' : ModbusSequentialDataBlock(0, [False]*10),
        }
        context = ModbusSlaveContext(**store)
        self.assertNotEqual(str(context), None)

        for fx in [1,2,3,4]:
            context.setValues(fx, 0, [True]*10)
            self.assertTrue(context.validate(fx, 0,10))
            self.assertEqual(context.getValues(fx, 0,10), [True]*10)
        context.reset()

        for fx in [1,2,3,4]:
            self.assertTrue(context.validate(fx, 0,10))
            self.assertEqual(context.getValues(fx, 0,10), [False]*10)

    def testModbusServerContext(self):
        ''' Test a modbus server context '''
        def _set(ctx):
            ctx[0xffff] = None
        context = ModbusServerContext(single=False)
        self.assertRaises(NoSuchSlaveException, lambda: _set(context))
        self.assertRaises(NoSuchSlaveException, lambda: context[0xffff])


class RedisDataStoreTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.datastore.database.redis module
    '''

    def setUp(self):
        self.slave = RedisSlaveContext()

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testStr(self):
        # slave = RedisSlaveContext()
        self.assertEqual(str(self.slave), "Redis Slave Context %s" % self.slave.client)

    def testReset(self):
        assert isinstance(self.slave.client, redis.Redis)
        self.slave.client = MagicMock()
        self.slave.reset()
        self.slave.client.flushall.assert_called_once_with()

    def testValCallbacksSuccess(self):
        self.slave._build_mapping()
        mock_count = 3
        mock_offset = 0
        self.slave.client.mset = MagicMock()
        self.slave.client.mget = MagicMock(return_value=['11'])

        for key in ('d', 'c', 'h', 'i'):
            self.assertTrue(
                self.slave._val_callbacks[key](mock_offset, mock_count)
            )

    def testValCallbacksFailure(self):
        self.slave._build_mapping()
        mock_count = 3
        mock_offset = 0
        self.slave.client.mset = MagicMock()
        self.slave.client.mget = MagicMock(return_value=['11', None])

        for key in ('d', 'c', 'h', 'i'):
            self.assertFalse(
                self.slave._val_callbacks[key](mock_offset, mock_count)
            )

    def testGetCallbacks(self):
        self.slave._build_mapping()
        mock_count = 3
        mock_offset = 0
        self.slave.client.mget = MagicMock(return_value='11')

        for key in ('d', 'c'):
            resp = self.slave._get_callbacks[key](mock_offset, mock_count)
            self.assertEqual(resp, [True, False, False])

        for key in ('h', 'i'):
            resp = self.slave._get_callbacks[key](mock_offset, mock_count)
            self.assertEqual(resp, ['1', '1'])

    def testSetCallbacks(self):
        self.slave._build_mapping()
        mock_values = [3]
        mock_offset = 0
        self.slave.client.mset = MagicMock()
        self.slave.client.mget = MagicMock()

        for key in ['c', 'd']:
            self.slave._set_callbacks[key](mock_offset, [3])
            k = "pymodbus:{}:{}".format(key, mock_offset)
            self.slave.client.mset.assert_called_with(
                {k: '\x01'}
            )

        for key in ('h', 'i'):
            self.slave._set_callbacks[key](mock_offset, [3])
            k = "pymodbus:{}:{}".format(key, mock_offset)
            self.slave.client.mset.assert_called_with(
                {k: mock_values[0]}
            )

    def testValidate(self):
        self.slave.client.mget = MagicMock(return_value=[123])
        self.assertTrue(self.slave.validate(0x01, 3000))

    def testSetValue(self):
        self.slave.client.mset = MagicMock()
        self.slave.client.mget = MagicMock()
        self.assertEqual(self.slave.setValues(0x01, 1000, [12]), None)

    def testGetValue(self):
        self.slave.client.mget = MagicMock(return_value=["123"])
        self.assertEqual(self.slave.getValues(0x01, 23), [])


class MockSqlResult(object):
        def __init__(self, rowcount=0, value=0):
            self.rowcount = rowcount
            self.value = value


class SqlDataStoreTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.datastore.database.SqlSlaveContesxt
    module
    '''

    def setUp(self):
        self.slave = SqlSlaveContext()
        self.slave._metadata.drop_all = MagicMock()
        self.slave._db_create = MagicMock()
        self.slave._table.select = MagicMock()
        self.slave._connection = MagicMock()

        self.mock_addr = random.randint(0, 65000)
        self.mock_values = random.sample(range(1, 100), 5)
        self.mock_function = 0x01
        self.mock_type = 'h'
        self.mock_offset = 0
        self.mock_count = 1

        self.function_map = {2: 'd', 4: 'i'}
        self.function_map.update([(i, 'h') for i in [3, 6, 16, 22, 23]])
        self.function_map.update([(i, 'c') for i in [1, 5, 15]])

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testStr(self):
        self.assertEqual(str(self.slave), "Modbus Slave Context")

    def testReset(self):
        self.slave.reset()

        self.slave._metadata.drop_all.assert_called_once_with()
        self.slave._db_create.assert_called_once_with(
            self.slave.table, self.slave.database
        )

    def testValidateSuccess(self):
        self.slave._connection.execute.return_value.fetchall.return_value = self.mock_values
        self.assertTrue(self.slave.validate(
            self.mock_function, self.mock_addr, len(self.mock_values))
        )

    def testValidateFailure(self):
        wrong_count = 9
        self.slave._connection.execute.return_value.fetchall.return_value = self.mock_values
        self.assertFalse(self.slave.validate(
            self.mock_function, self.mock_addr, wrong_count)
        )

    def testBuildSet(self):
        mock_set = [
            {
                'index': 0,
                'type': 'h',
                'value': 11
            },
            {
                'index': 1,
                'type': 'h',
                'value': 12
            }
        ]
        self.assertListEqual(self.slave._build_set('h', 0, [11, 12]), mock_set)

    def testCheckSuccess(self):
        mock_success_results = [1, 2, 3]
        self.slave._get = MagicMock(return_value=mock_success_results)
        self.assertFalse(self.slave._check('h', 0, 1))

    def testCheckFailure(self):
        mock_success_results = []
        self.slave._get = MagicMock(return_value=mock_success_results)
        self.assertTrue(self.slave._check('h', 0, 1))

    def testGetValues(self):
        self.slave._get = MagicMock()

        for key, value in self.function_map.items():
            self.slave.getValues(key, self.mock_addr, self.mock_count)
            self.slave._get.assert_called_with(
                value, self.mock_addr + 1, self.mock_count
            )

    def testSetValues(self):
        self.slave._set = MagicMock()

        for key, value in self.function_map.items():
            self.slave.setValues(key, self.mock_addr, self.mock_values)
            self.slave._set.assert_called_with(
                value, self.mock_addr + 1, self.mock_values
            )

    def testSet(self):
        self.slave._check = MagicMock(return_value=True)
        self.slave._connection.execute = MagicMock(
            return_value=MockSqlResult(rowcount=len(self.mock_values))
        )
        self.assertTrue(self.slave._set(
            self.mock_type, self.mock_offset, self.mock_values)
        )

        self.slave._check = MagicMock(return_value=False)
        self.assertFalse(
            self.slave._set(self.mock_type, self.mock_offset, self.mock_values)
        )

    def testUpdateSuccess(self):
        self.slave._connection.execute = MagicMock(
            return_value=MockSqlResult(rowcount=len(self.mock_values))
        )
        self.assertTrue(
            self.slave._update(self.mock_type, self.mock_offset, self.mock_values)
        )

    def testUpdateFailure(self):
        self.slave._connection.execute = MagicMock(
            return_value=MockSqlResult(rowcount=100)
        )
        self.assertFalse(
            self.slave._update(self.mock_type, self.mock_offset, self.mock_values)
        )

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
