from pymodbus.interfaces import IModbusSlaveContext

#---------------------------------------------------------------------------#
# Mocks
#---------------------------------------------------------------------------#
class mock(object): pass

class MockContext(IModbusSlaveContext):

    def __init__(self, valid=False, default=True):
        self.valid = valid
        self.default = default

    def validate(self, fx, address, count):
        return self.valid

    def getValues(self, fx, address, count):
        return [self.default] * count

    def setValues(self, fx, address, count):
        pass

class FakeList(object):
    ''' todo, replace with magic mock '''

    def __init__(self, size):
        self.size = size

    def __len__(self):
        return self.size

    def __iter__(self):
        return []

