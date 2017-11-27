#!/usr/bin/env python
import unittest
import mock
from mock import MagicMock
import redis
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
        self.slave.client.mset = MagicMock()
        self.slave.client.mget = MagicMock(return_value="11")

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


class SqlDataStoreTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.datastore.database.SqlSlaveContesxt
    module
    '''

    def setUp(self):
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testStr(self):
        pass


#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
