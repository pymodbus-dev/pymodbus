#!/usr/bin/env python
import unittest
from pymodbus.datastore import *
from pymodbus.exceptions import *

class ModbusServerSingleContextTest(unittest.TestCase):
    ''' This is the unittest for the pymodbus.datastore.ModbusServerContext
    using a single slave context.
    '''

    def setUp(self):
        ''' Sets up the test environment '''
        self.slave = ModbusSlaveContext()
        self.context = ModbusServerContext(slaves=self.slave, single=True)

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.context

    def testSingleContextGets(self):
        ''' Test getting on a single context '''
        for id in xrange(0, 0xff):
            self.assertEqual(self.slave, self.context[id])

    def testSingleContextIter(self):
        ''' Test iterating over a single context '''
        expected = (0, self.slave)
        for slave in self.context:
            self.assertEqual(slave, expected)

    def testSingleContextDefault(self):
        ''' Test that the single context default values work '''
        self.context = ModbusServerContext()
        slave = self.context[0x00]
        self.assertEqual(slave, {})

    def testSingleContextSet(self):
        ''' Test a setting a single slave context '''
        slave = ModbusSlaveContext()
        self.context[0x00] = slave
        actual = self.context[0x00]
        self.assertEqual(slave, actual)

class ModbusServerMultipleContextTest(unittest.TestCase):
    ''' This is the unittest for the pymodbus.datastore.ModbusServerContext
    using multiple slave contexts.
    '''

    def setUp(self):
        ''' Sets up the test environment '''
        self.slaves  = dict((id, ModbusSlaveContext()) for id in xrange(10))
        self.context = ModbusServerContext(slaves=self.slaves, single=False)

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.context

    def testMultipleContextGets(self):
        ''' Test getting on multiple context '''
        for id in xrange(0, 10):
            self.assertEqual(self.slaves[id], self.context[id])

    def testMultipleContextIter(self):
        ''' Test iterating over multiple context '''
        for id, slave in self.context:
            self.assertEqual(slave, self.slaves[id])
            self.assertTrue(id in self.context)

    def testMultipleContextDefault(self):
        ''' Test that the multiple context default values work '''
        self.context = ModbusServerContext(single=False)
        self.assertRaises(ParameterException, lambda: self.context[0x00])

    def testMultipleContextSet(self):
        ''' Test a setting multiple slave contexts '''
        slaves = dict((id, ModbusSlaveContext()) for id in xrange(10))
        for id, slave in slaves.iteritems():
            self.context[id] = slave
        for id, slave in slaves.iteritems():
            actual = self.context[id]
            self.assertEqual(slave, actual)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
