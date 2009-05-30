""" Collection of transaction based abstractions
"""
from zope.interface import implements
from pymodbus import interfaces
from pymodbus.utilities import computeCRC, computeLRC
from binascii import b2a_hex
import struct

import logging
_logger = logging.getLogger('pymodbus.protocol')

#---------------------------------------------------------------------------#
# TCP Transaction
#---------------------------------------------------------------------------#
# count = 0
# do
#   result = send(message)
#   if (timeout or result == bad)
#      count++
#   else break
# while (count < 3)
#
# Default port is tcp(502)
#---------------------------------------------------------------------------#
class ModbusTCPTransaction:
    ''' Impelements a transaction for a tcp/ip request

    This is currently not used, although it should...
    '''

    def __init__(self, request=None):
        '''
        Initializes a transaction handle
        @param request The request to manage
        '''
        self.request = request
        self.retries = 3
        self.timeout = 5

    def doRetry(self):
        ''' Checks to see if we should retry the request '''
        if self.retries > 0:
            self.retries -= 1
            return True
        return False

    def execute(self):
        retries = self.retries
        self.req.transaction_id = self.getUniqueTransactionId()
        _logger.debug("Running transaction %d" % self.req.transaction_id)
        while (1):
            try:
                self.con.connect()
                tr = self.con.modbus_transport
                tr.writeMessage(self.req)
                res = tr.readResponse()
                return res
            except socket.error, msg:
                self.con.close()
                if retries > 0:
                    _logger.debug("Attemp to execute transaction failed. (%s) " % msg)
                    _logger.debug("Will try %d more times." % self.retries)
                    retries -= 1
                    continue
                raise

#---------------------------------------------------------------------------#
# The Global Transaction Manager
#---------------------------------------------------------------------------#
class ModbusTransactionManager(interfaces.Singleton):
    ''' Impelements a transaction for a manager '''

    __tid = 0
    __transactions = []

    def __init__(self):
        pass

    def addTransaction(self, request):
        '''
        Adds a transaction to the handler in case it needs to be resent
        @param request The request to hold on to
        '''
        self.__transactions.append(request)

    def getTransaction(self, tid):
        '''
        Returns a transaction matching the referenced tid
        @param tid The transaction to retrieve

        If the transaction does not exist, None is returned
        '''
        for k,v in enumerate(self.__transactions):
            if v.transaction_id == tid:
                return self.__transactions[k]
        return None

    def delTransaction(self, tid):
        '''
        Removes a transaction matching the referenced tid
        @param tid The transaction to remove
        '''
        for k,v in enumerate(self.__transactions):
            if v.transaction_id == tid:
                del self.__transactions[k]

    def getNextTID(self):
        '''
        Gets the next available transaction identifier
        and increments the global handler
        '''
        tid = self.__tid
        self.__tid += 1
        return tid

    def resetTID(self):
        ''' Resets the transaction identifier to 0 '''
        self.__tid = 0

#---------------------------------------------------------------------------#
# Modbus TCP Message
#---------------------------------------------------------------------------#
# Before each modbus TCP message is an MBAP header which is used as a
# message frame.  It allows us to easily separate messages as follows:
#
# [         MBAP Header         ] [ Function Code] [ Data ]
# [ tid ][ pid ][ length ][ uid ]
#   2b     2b     2b        1b           1b           Nb
#
# while len(message) > 0:
#     tid, pid, length`, uid = struct.unpack("HHHB", message)
#     request = message[0:7 + length - 1`]
#     message = [7 + length - 1:]
#
# * length = uid + function code + data
# * The -1 is to account for the uid byte
#---------------------------------------------------------------------------#
class ModbusTCPFramer:
    '''
    Modbus TCP Frame controller
    '''

    implements(interfaces.IModbusFramer)

    def __init__(self):
        self.__buffer = ''
        self.__header = {'tid':0, 'pid':0, 'len':0, 'uid':0}
        self.__hsize  = 0x07

    def checkFrame(self):
        '''
        Check and decode the next frame Return true if we were successful
        '''
        if len(self.__buffer) > self.__hsize:
            self.__header['tid'], self.__header['pid'], \
            self.__header['len'], self.__header['uid'] = struct.unpack(
                    '>HHHB', self.__buffer[0:self.__hsize])

            # someone sent us an error? ignore it
            if self.__header['len'] < 2:
                self.advanceFrame()
            # we have at least a complete message, continue
            elif len(self.__buffer) >= self.__header['len']:
                return True
        # we don't have enough of a message yet, wait
        return False

    def advanceFrame(self):
        ''' Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        '''
        self.__buffer = self.__buffer[self.__hsize + self.__header['len'] - 1:]
        self.__header = {'tid':0, 'pid':0, 'len':0, 'uid':0}

    def isFrameReady(self):
        ''' Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.
        @return True if ready, False otherwise
        '''
        return len(self.__buffer) > self.__hsize

    def addToFrame(self, message):
        '''
        This should be used before the decoding while loop to add the received
        data to the buffer handle.
        @param message The most recent packet
        '''
        self.__buffer += message

    def getFrame(self):
        ''' Return the next frame from the buffered data
        @return The next full frame buffer
        '''
        return self.__buffer[self.__hsize:self.__hsize +
                self.__header['len'] - 1]

    def populateResult(self, result):
        '''
        Populates the modbus result with the transport specific header
        information (pid, tid, uid, checksum, etc)
        @param result The response packet
        '''
        result.transaction_id = self.__header['tid']
        result.protocol_id = self.__header['pid']
        result.uint_id = self.__header['uid']

    def buildPacket(self, message):
        '''
        Creates a ready to send modbus packet from a modbus request/response
        unencoded message.
        @param message The request/response to send
        '''
        data = message.encode()
        packet = struct.pack('>HHHBB',
                message.transaction_id,
                message.protocol_id,
                len(data) + 2,
                message.unit_id,
                message.function_code) + data
        return packet

#---------------------------------------------------------------------------#
# Modbus RTU Message
#---------------------------------------------------------------------------#
#
# [ Start Wait ] [Address ][ Function Code] [ Data ][ CRC/LRC ][  End Wait  ]
#   3.5 chars     1b         1b               Nb      2b         3.5 chars
#
# Wait refers to the amount of time required to transmist at least x many
# characters.  In this case it is 3.5 characters.  Also, if we recieve a
# wait of 1.5 characters at any point, we must trigger an error message.
# Also, it appears as though this message is little endian.
#
#  block-on-read:
#      read until 3.5 delay
#      check for errors
#      decode
#
#---------------------------------------------------------------------------#
#  Baud  1.5c (18 bits)   3.5c (38 bits)
#---------------------------------------------------------------------------#
#  1200   13333.3 us       31666.7 us
#  4800    3333.3 us        7916.7 us
#  9600    1666.7 us        3958.3 us
# 19200     833.3 us        1979.2 us
# 38400     416.7 us         989.6 us
#---------------------------------------------------------------------------#
# 1 Byte = start + 8 bits + parity + stop = 11 bits
# (1/Baud)(bits) = delay seconds
#---------------------------------------------------------------------------#
class ModbusRTUFramer:
    '''
    Modbus RTU Frame controller
    '''

    implements(interfaces.IModbusFramer)

    def __init__(self):
        self.__buffer = ''
        self.__header = {'crc':0x0000, 'len':0}
        self.__end    = '\x0d\x0a'
        self.__start  = '\x3a'

    def checkFrame(self):
        '''
        Check and decode the next frame Return true if we were successful
        '''
        # i dunno yet
        return False

    def advanceFrame(self):
        ''' Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        '''
        self.__buffer = self.__buffer[-1:]
        self.__header = {'crc':0x0000, 'len':0}

    def isFrameReady(self):
        ''' Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.
        @return True if ready, False otherwise
        '''
        return len(self.__buffer) > 1

    def addToFrame(self, message):
        '''
        This should be used before the decoding while loop to add the received
        data to the buffer handle.
        @param message The most recent packet
        '''
        self.__buffer += message

    def getFrame(self):
        ''' Get the next frame from the buffer
        @return The frame data or ''
        '''
        return self.__buffer[:self.__header['len'] - 2]

    def populateResult(self, result):
        '''
        Populates the modbus result with the transport specific header
        information (pid, tid, uid, checksum, etc)
        @param result The response packet
        '''
        pass # no header for serial

    def buildPacket(self, message):
        '''
        Creates a ready to send modbus packet from a modbus request/response
        unencoded message.
        @param message The request/response to send
        '''
        data = message.encode()
        packet = struct.pack('>BB',
                message.unit_id,
                message.function_code) + data
        packet = packet + struct.pack("<H", computeCRC(packet))
        return packet


#---------------------------------------------------------------------------#
# Modbus ASCII Message
#---------------------------------------------------------------------------#
#
# [ Start ][Address ][ Function ][ Data ][ LRC ][ End ]
#   1c        2c         2c         Nc     2c      2c
#
# * data can be 0 - 2x252 chars
# * end is '\r\n' (Carriage return line feed), however the line feed character
#   can be changed via a special command
# * start is ':'
#
# Also, it appears as though this message is little endian.
#
#  read until stream == ':':
#    buffer until stream == '\r\n'
#    check for errors
#    decode
#
#---------------------------------------------------------------------------#
# @todo This is actually being encoded as binary instead of ascii, so
#       I need to fix that. I need to re-read the spec.
#---------------------------------------------------------------------------#
class ModbusASCIIFramer:
    '''
    Modbus ASCII Frame controller
    '''

    implements(interfaces.IModbusFramer)

    def __init__(self):
        self.__buffer = ''
        self.__header = {'lrc':'0000', 'len':0}
        self.__start  = ':'
        self.__end    = "\r\n"

    def checkFrame(self):
        ''' Check and decode the next frame
        @return True if we successful, False otherwise
        '''
        start = self.__buffer.find(self.__start)
        if start == -1: return False
        # go ahead and skip old bad data
        if start > 0 :
            self.__buffer = self.__buffer[start:]

        end = self.__buffer.find(self.__end)
        if (end != -1):
            self.__header['len'] = end
            self.__header['lrc'] = self.__buffer[end-2:end]
            # if correct lrc
            return True
        return False

    def advanceFrame(self):
        ''' Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        '''
        self.__buffer = self.__buffer[self.__header['len'] + 2:]
        self.__header = {'lrc':'0000', 'len':0}

    def isFrameReady(self):
        ''' Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.
        @return True if ready, False otherwise
        '''
        return len(self.__buffer) > 1

    def addToFrame(self, message):
        ''' Add the next message to the frame buffer
        This should be used before the decoding while loop to add the received
        data to the buffer handle.
        @param message The most recent packet
        '''
        self.__buffer += message

    def getFrame(self):
        ''' Get the next frame from the buffer
        @return The frame data or ''
        '''
        return self.__buffer[1:self.__header['len']]

    def populateResult(self, result):
        ''' Populates the modbus result with current frame header
        @param result The response packet
        '''
        pass # no header for serial

    def buildPacket(self, message):
        ''' Creates a ready to send modbus packet
        Built off of a  modbus request/response
        @param message The request/response to send
        @return The built packet
        '''
        data   = b2a_hex(message.encode())
        packet = '%02x%02x%s' % (message.unit_id, message.function_code, data)
        packet = '%c%s%02x%s' % (self.__start, packet, computeLRC(packet), self.__end)
        return packet

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ModbusTCPTransaction", "ModbusTransactionManager",
    "ModbusTCPFramer", "ModbusRTUFramer", "ModbusASCIIFramer",
]
