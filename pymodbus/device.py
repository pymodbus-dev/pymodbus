'''
Modbus Device Controller

These are the device management handlers.  They should be
maintained in the server context and the various methods
should be inserted in the correct locations.
'''
from pymodbus.interfaces import Singleton

#---------------------------------------------------------------------------#
# Network Access Control
#---------------------------------------------------------------------------#
class ModbusAccessControl(Singleton):
    '''
    This is a simple implementation of a Network Management System table.
    Its purpose is to control access to the server (if it is used).
    We assume that if an entry is in the table, it is allowed accesses to
    resources.  However, if the host does not appear in the table (all
    unknown hosts) its connection will simply be closed.

    Since it is a singleton, only one version can possible exist and all
    instances pull from here.
    '''
    __nmstable = [
            "127.0.0.1",
    ]

    def add(self, host):
        '''
        Add allowed host(s) from the NMS table
        @param host The host to add
        '''
        if not isinstance(host, list):
            host = [host]
        for entry in host:
            if entry not in self.__nmstable:
                self.__nmstable.append(entry)

    def remove(self, host):
        '''
        Remove allowed host(s) from the NMS table
        @param host The host to remove
        '''
        if not isinstance(host, list):
            host = [host]
        for entry in host:
            if entry in self.__nmstable:
                self.__nmstable.remove(entry)

    def check(self, host):
        '''
        Check if a host is allowed to access resources
        @param host The host to check
        '''
        return host in self.__nmstable

#---------------------------------------------------------------------------#
# Device Information Control
#---------------------------------------------------------------------------#
class ModbusDeviceIdentification:
    '''
    This is used to supply the device identification
    for the readDeviceIdentification function

    For more information read section 6.21 of the modbus
    application protocol.
    '''
    _data = {
            0x00: '', # VendorName
            0x01: '', # ProductCode
            0x02: '', # MajorMinorRevision
            0x03: '', # VendorUrl
            0x04: '', # ProductName
            0x05: '', # ModelName
            0x06: '', # UserApplicationName
            0x07: '', # reserved
            0x08: '', # reserved
            # 0x80 -> 0xFF are private
    }

    def __init__(self, info=None):
        '''
        Initialize the datastore with the elements you need.
        (note acceptable range is [0x00-0x07,0x80-0xFF] inclusive)
        @param info A dictionary of {int:string} of values
        '''
        if info is not None and isinstance(info, dict):
            for i in info.keys():
                if (i < 0x07) or (i >= 0x80) or (i <= 0xff):
                    self._data[i] = info[i]

    def __setitem__(self, key, item):
        '''
        Wrapper used to access the device information
        @param key The register to set
        @param item The new value for referenced register
        '''
        if key not in [0x07, 0x08]:
            self._data[key] = item

    def __getitem__(self, key):
        '''
        Wrapper used to access the device information
        @param key The register to read
        '''
        if key not in self._data.keys():
            self._data[key] = ''
        return self._data[key]

    def __str__(self):
        return "DeviceIdentity"

    #---------------------------------------------------------------------------#
    # Eases access
    #---------------------------------------------------------------------------#
    vendor_name             = property(lambda self: self._data[0])
    product_code            = property(lambda self: self._data[1])
    major_minor_revision    = property(lambda self: self._data[2])
    vendor_url              = property(lambda self: self._data[3])
    product_name            = property(lambda self: self._data[4])
    model_name              = property(lambda self: self._data[5])
    user_application_name   = property(lambda self: self._data[6])

#---------------------------------------------------------------------------#
# Main server controll block
#---------------------------------------------------------------------------#
class ModbusControlBlock(Singleton):
    '''
    This is a global singleotn that controls all system information

    All activity should be logged here and all diagnostic requests
    should come from here.
    '''

    __counter = {
            'BusMessage'            : 0x0000,
            'BusCommunicationError' : 0x0000,
            'BusExceptionError'     : 0x0000,
            'SlaveMessage'          : 0x0000,
            'SlaveNoResponse'       : 0x0000,
            'SlaveNAK'              : 0x0000,
            'SlaveBusy'             : 0x0000,
            'BusCharacterOverrun'   : 0x0000,
    }
    __mode = 'ASCII'
    __diagnostic = [False] * 16
    __instance = None
    __listen_only = False
    __delimiter = '\r'
    Identity = ModbusDeviceIdentification()

    def __str__(self):
        return "ModbusControl"

    #---------------------------------------------------------------------------#
    # Conter Properties
    #---------------------------------------------------------------------------#
    def resetAllCounters(self):
        ''' This clears all of the system counters and diagnostic flags '''
        for i in self.__counter.keys():
            self.__counter[i] = 0x0000
        self.__diagnostic = [False] * 16

    def incrementCounter(self, counter):
        '''
        This increments a system counter
        @param counter The counter to increment
        '''
        if counter in self.__counter.keys():
            self.__counter[counter] += 1

    def getCounter(self, counter):
        '''
        This returns the requested counter
        @param counter The counter to return
        '''
        if counter in self.__counter.keys():
            return self.__counter[counter]
        return None

    def resetCounter(self, counter):
        ''' This clears the selected counter '''
        if counter in self.__counter.keys():
            self.__counter[counter] = 0x0000

    #---------------------------------------------------------------------------#
    # Listen Properties
    #---------------------------------------------------------------------------#
    def toggleListenOnly(self):
        ''' This toggles the listen only status '''
        self.__listen_only = not self.__listen_only

    def isListenOnly(self):
        ''' This returns weither we should listen only '''
        return self.__listen_only

    #---------------------------------------------------------------------------#
    # Mode Properties
    #---------------------------------------------------------------------------#
    def setMode(self, mode):
        '''
        This toggles the current serial mode
        @param mode The data transfer method in (RTU, ASCII)
        '''
        if mode in ['ASCII', 'RTU']:
            self.__mode = mode

    def getMode(self):
        ''' Returns the current transfer mode '''
        return self.__mode

    #---------------------------------------------------------------------------#
    # Delimiter Properties
    #---------------------------------------------------------------------------#
    def setDelimiter(self, char):
        '''
        This changes the serial delimiter character
        @param char The new serial delimiter character
        '''
        if isinstance(char, str):
            self.__delimiter = char
        elif isinstance(char, int):
            self.__delimiter = chr(char)

    def getDelimiter(self):
        ''' Returns the current serial delimiter character '''
        return self.__delimiter

    #---------------------------------------------------------------------------#
    # Diagnostic Properties
    #---------------------------------------------------------------------------#
    def setDiagnostic(self, mapping):
        '''
        This sets the value in the diagnostic register
        @param mapping Dictionary of key:value pairs to set
        '''
        for entry in mapping.iteritems():
            if entry[0] >= 0 and entry[0] < len(self.__diagnostic):
                self.__diagnostic[entry[0]] = (entry[1] != 0)

    def getDiagnostic(self, bit):
        '''
        This gets the value in the diagnostic register
        @param bit The bit to set
        '''
        if bit >= 0 and bit < len(self.__diagnostic):
            return self.__diagnostic[bit]
        return None

    def getDiagnosticRegister(self):
        '''
        This gets the entire diagnostic register
        '''
        return self.__diagnostic

__all__ = [
        "ModbusAccessControl",
        "ModbusDeviceIdentification",
        "ModbusControlBlock"
]
