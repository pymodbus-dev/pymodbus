"""Test server context."""
import unittest

from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
from pymodbus.exceptions import NoSuchSlaveException


class ModbusServerSingleContextTest(unittest.TestCase):
    """This is the unittest for the pymodbus.datastore.ModbusServerContext using a single slave context."""

    def setUp(self):
        """Set up the test environment"""
        self.slave = ModbusSlaveContext()
        self.context = ModbusServerContext(slaves=self.slave, single=True)

    def tearDown(self):
        """Clean up the test environment"""
        del self.context

    def test_single_context_gets(self):
        """Test getting on a single context"""
        for slave_id in range(0, 0xFF):
            self.assertEqual(self.slave, self.context[slave_id])

    def test_single_context_deletes(self):
        """Test removing on multiple context"""

        def _test():
            del self.context[0x00]

        self.assertRaises(NoSuchSlaveException, _test)

    def test_single_context_iter(self):
        """Test iterating over a single context"""
        expected = (0, self.slave)
        for slave in self.context:
            self.assertEqual(slave, expected)

    def test_single_context_default(self):
        """Test that the single context default values work"""
        self.context = ModbusServerContext()
        slave = self.context[0x00]
        self.assertEqual(slave, {})

    def test_single_context_set(self):
        """Test a setting a single slave context"""
        slave = ModbusSlaveContext()
        self.context[0x00] = slave
        actual = self.context[0x00]
        self.assertEqual(slave, actual)

    def test_single_context_register(self):
        """Test single context register."""
        request_db = [1, 2, 3]
        slave = ModbusSlaveContext()
        slave.register(0xFF, "custom_request", request_db)
        self.assertEqual(slave.store["custom_request"], request_db)
        self.assertEqual(slave.decode(0xFF), "custom_request")


class ModbusServerMultipleContextTest(unittest.TestCase):
    """This is the unittest for the pymodbus.datastore.ModbusServerContext using multiple slave contexts."""

    def setUp(self):
        """Set up the test environment"""
        self.slaves = {id: ModbusSlaveContext() for id in range(10)}
        self.context = ModbusServerContext(slaves=self.slaves, single=False)

    def tearDown(self):
        """Clean up the test environment"""
        del self.context

    def test_multiple_context_gets(self):
        """Test getting on multiple context"""
        for slave_id in range(0, 10):
            self.assertEqual(self.slaves[slave_id], self.context[slave_id])

    def test_multiple_context_deletes(self):
        """Test removing on multiple context"""
        del self.context[0x00]
        self.assertRaises(NoSuchSlaveException, lambda: self.context[0x00])

    def test_multiple_context_iter(self):
        """Test iterating over multiple context"""
        for slave_id, slave in self.context:
            self.assertEqual(slave, self.slaves[slave_id])
            self.assertTrue(slave_id in self.context)

    def test_multiple_context_default(self):
        """Test that the multiple context default values work"""
        self.context = ModbusServerContext(single=False)
        self.assertRaises(NoSuchSlaveException, lambda: self.context[0x00])

    def test_multiple_context_set(self):
        """Test a setting multiple slave contexts"""
        slaves = {id: ModbusSlaveContext() for id in range(10)}
        for slave_id, slave in iter(slaves.items()):
            self.context[slave_id] = slave
        for slave_id, slave in iter(slaves.items()):
            actual = self.context[slave_id]
            self.assertEqual(slave, actual)
