'''
Collection of transaction based abstractions
'''
import struct
from binascii import b2a_hex

from pymodbus.constants  import Defaults
from pymodbus.interfaces import Singleton, IModbusFramer
from pymodbus.utilities  import computeCRC, computeLRC

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger('pymodbus.protocol')

#---------------------------------------------------------------------------#
# The Global Transaction Manager
#---------------------------------------------------------------------------#
class ModbusTransactionManager(Singleton):
    ''' Impelements a transaction for a manager

    The transaction protocol can be represented by the following pseudo code::

        count = 0
        do
          result = send(message)
          if (timeout or result == bad)
             count++
          else break
        while (count < 3)
    
    This module helps to abstract this away from the framer and protocol.
    '''

    __tid = Defaults.TransactionId
    __transactions = []

    def __init__(self):
        ''' Initializes an instance of the ModbusTransactionManager '''
        pass

    def execute(self, request):
        ''' Starts the producer to send the next request to
        consumer.write(Frame(request))
        '''
        retries = Defaults.Retries
        request.transaction_id = self.__getNextTID()
        _logging.debug("Running transaction %d" % request.transaction_id)

        while retries > 0:
            try:
                self.socket.connect()
                self.socket.send(self.framer.buildPacket(request))
                #return tr.readResponse()
            except socket.error, msg:
                self.socket.close()
                _logging.debug("Transaction failed. (%s) " % msg)
                retries -= 1

    def addTransaction(self, request):
        ''' Adds a transaction to the handler
           
        This holds the requets in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        '''
        ModbusTransactionManager.__transactions.append(request)

    def getTransaction(self, tid):
        ''' Returns a transaction matching the referenced tid

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        '''
        for k,v in enumerate(ModbusTransactionManager.__transactions):
            if v.transaction_id == tid:
                return ModbusTransactionManager.__transactions[k]
        return None

    def delTransaction(self, tid):
        ''' Removes a transaction matching the referenced tid

        :param tid: The transaction to remove
        '''
        for k,v in enumerate(ModbusTransactionManager.__transactions):
            if v.transaction_id == tid:
                del ModbusTransactionManager.__transactions[k]

    def getNextTID(self):
        ''' Retrieve the next unique transaction identifier
        
        This handles incrementing the identifier after
        retrieval

        :returns: The next unique transaction identifier
        '''
        tid = ModbusTransactionManager.__tid
        ModbusTransactionManager.__tid += 1
        return tid

    def resetTID(self):
        ''' Resets the transaction identifier '''
        ModbusTransactionManager.__tid = Defaults.TransactionId

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
class ModbusSocketFramer(IModbusFramer):
    '''
    Modbus Socket Frame controller
    '''

    def __init__(self, decoder):
        ''' Initializes a new instance of the framer

        :param decoder: The decoder implementation to use
        '''
        self.__buffer = ''
        self.__header = {'tid':0, 'pid':0, 'len':0, 'uid':0}
        self.__hsize  = 0x07
        self.decoder  = decoder

    #-----------------------------------------------------------------------#
    # Private Helper Functions
    #-----------------------------------------------------------------------#
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

        :returns: True if ready, False otherwise
        '''
        return len(self.__buffer) > self.__hsize

    def addToFrame(self, message):
        ''' Adds new packet data to the current frame buffer

        :param message: The most recent packet
        '''
        self.__buffer += message

    def getFrame(self):
        ''' Return the next frame from the buffered data

        :returns: The next full frame buffer
        '''
        return self.__buffer[self.__hsize:self.__hsize +
                self.__header['len'] - 1]

    def populateResult(self, result):
        '''
        Populates the modbus result with the transport specific header
        information (pid, tid, uid, checksum, etc)

        :param result: The response packet
        '''
        result.transaction_id = self.__header['tid']
        result.protocol_id = self.__header['pid']
        result.unit_id = self.__header['uid']

    #-----------------------------------------------------------------------#
    # Public Member Functions
    #-----------------------------------------------------------------------#
    def processIncomingPacket(self, data, callback):
        ''' The new packet processing pattern

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 / N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.

        :param data: The new packet data
        :param callback: The function to send results to
        '''
        _logger.debug(" ".join([hex(ord(x)) for x in data]))
        self.addToFrame(data)
        while self.isFrameReady():
            if self.checkFrame():
                result = self.decoder.decode(self.getFrame())
                if result is None:
                    raise ModbusIOException("Unable to decode request")
                self.populateResult(result)
                self.advanceFrame()
                callback(result) # defer or push to a thread?
            else: break

    def buildPacket(self, message):
        ''' Creates a ready to send modbus packet

        :param message: The populated request/response to send
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
class ModbusRtuFramer(IModbusFramer):
    '''
    Modbus RTU Frame controller::

        [ Start Wait ] [Address ][ Function Code] [ Data ][ CRC/LRC ][  End Wait  ]
          3.5 chars     1b         1b               Nb      2b         3.5 chars
        
    Wait refers to the amount of time required to transmist at least x many
    characters.  In this case it is 3.5 characters.  Also, if we recieve a
    wait of 1.5 characters at any point, we must trigger an error message.
    Also, it appears as though this message is little endian. The logic is
    simplified as the following::
        
        block-on-read:
            read until 3.5 delay
            check for errors
            decode

    The following table is a listing of the baud wait times for the specified
    baud rates::
        
        --------------------------------------------------------------------------#
         Baud  1.5c (18 bits)   3.5c (38 bits)
        --------------------------------------------------------------------------#
         1200   13333.3 us       31666.7 us
         4800    3333.3 us        7916.7 us
         9600    1666.7 us        3958.3 us
        19200     833.3 us        1979.2 us
        38400     416.7 us         989.6 us
        --------------------------------------------------------------------------#
        1 Byte = start + 8 bits + parity + stop = 11 bits
        (1/Baud)(bits) = delay seconds
    '''

    def __init__(self, decoder):
        ''' Initializes a new instance of the framer

        :param decoder: The decoder implementation to use
        '''
        self.__buffer = ''
        self.__header = {'crc':0x0000, 'len':0}
        self.__end    = '\x0d\x0a'
        self.__start  = '\x3a'
        self.decoder  = decoder

    #-----------------------------------------------------------------------#
    # Private Helper Functions
    #-----------------------------------------------------------------------#
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

        :returns: True if ready, False otherwise
        '''
        return len(self.__buffer) > 1

    def addToFrame(self, message):
        '''
        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        '''
        self.__buffer += message

    def getFrame(self):
        ''' Get the next frame from the buffer

        :returns: The frame data or ''
        '''
        return self.__buffer[:self.__header['len'] - 2]

    def populateResult(self, result):
        ''' Populates the modbus result header
   
        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        '''
        pass # no header for serial

    #-----------------------------------------------------------------------#
    # Public Member Functions
    #-----------------------------------------------------------------------#
    def processIncomingPacket(self, data, callback):
        ''' The new packet processing pattern

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 / N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.

        :param data: The new packet data
        :param callback: The function to send results to
        '''
        self.addToFrame(data)
        while self.isFrameReady():
            if self.checkFrame():
                result = self.decoder.decode(self.getFrame())
                if result is None:
                    raise ModbusIOException("Unable to decode response")
                self.populate(result)
                self.advanceFrame()
                callback(result) # defer or push to a thread?
            else: break

    def buildPacket(self, message):
        ''' Creates a ready to send modbus packet

        :param message: The populated request/response to send
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
class ModbusAsciiFramer(IModbusFramer):
    '''
    Modbus ASCII Frame Controller::
        
        [ Start ][Address ][ Function ][ Data ][ LRC ][ End ]
          1c        2c         2c         Nc     2c      2c
        
        * data can be 0 - 2x252 chars
        * end is '\\r\\n' (Carriage return line feed), however the line feed
          character can be changed via a special command
        * start is ':'
   
    This framer is used for serial transmission.  Unlike the RTU protocol,
    the data in this framer is transferred in plain text ascii.
    '''

    def __init__(self, decoder):
        ''' Initializes a new instance of the framer

        :param decoder: The decoder implementation to use
        '''
        self.__buffer = ''
        self.__header = {'lrc':'0000', 'len':0}
        self.__start  = ':'
        self.__end    = "\r\n"
        self.decoder  = decoder

    #-----------------------------------------------------------------------#
    # Private Helper Functions
    #-----------------------------------------------------------------------#
    def checkFrame(self):
        ''' Check and decode the next frame

        :returns: True if we successful, False otherwise
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
            # return checkLRC(data, self.__header['lrc'])
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

        :returns: True if ready, False otherwise
        '''
        return len(self.__buffer) > 1

    def addToFrame(self, message):
        ''' Add the next message to the frame buffer
        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        '''
        self.__buffer += message

    def getFrame(self):
        ''' Get the next frame from the buffer

        :returns: The frame data or ''
        '''
        return self.__buffer[1:self.__header['len']]

    def populateResult(self, result):
        ''' Populates the modbus result header
   
        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        '''
        pass # no header for serial

    #-----------------------------------------------------------------------#
    # Public Member Functions
    #-----------------------------------------------------------------------#
    def processIncomingPacket(self, data, callback):
        ''' The new packet processing pattern

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 / N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.

        :param data: The new packet data
        :param callback: The function to send results to
        '''
        self.addToFrame(data)
        while self.isFrameReady():
            if self.checkFrame():
                result = self.decoder.decode(self.getFrame())
                if result is None:
                    raise ModbusIOException("Unable to decode response")
                self.populate(result)
                self.advanceFrame()
                callback(result) # defer or push to a thread?
            else: break

    def buildPacket(self, message):
        ''' Creates a ready to send modbus packet
        Built off of a  modbus request/response

        :param message: The request/response to send
        :return: The built packet
        '''
        data   = b2a_hex(message.encode())
        packet = '%02x%02x%s' % (message.unit_id, message.function_code, data)
        packet = '%c%s%02x%s' % (self.__start, packet, computeLRC(packet), self.__end)
        return packet

#---------------------------------------------------------------------------#
# Modbus Binary Message
#---------------------------------------------------------------------------#
class ModbusBinaryFramer(IModbusFramer):
    '''
    Modbus Binary Frame Controller::

        [ Start ][Address ][ Function ][ Data ][ CRC ][ End ]
          1c        2c         2c         Nc     2c      1c

        * data can be 0 - 2x252 chars
        * end is '}'
        * start is '{'

    The idea here is that we implement the RTU protocol, however,
    instead of using timing for message delimiting, we use start
    and end of message characters (in this case { and }). Basically,
    this is a binary framer.

    The only case we have to watch out for is when a message contains
    the { or } characters.  If we encounter these characters, we
    simply duplicate them.  Hopefully we will not encounter those
    characters that often and will save a little bit of bandwitch
    without a real-time system.

    Protocol defined by jamod.sourceforge.net.
    '''

    def __init__(self, decoder):
        ''' Initializes a new instance of the framer

        :param decoder: The decoder implementation to use
        '''
        self.__buffer = ''
        self.__header = {'crc':0x0000, 'len':0}
        self.__start  = '{'
        self.__end    = "}"
        self.decoder  = decoder

    #-----------------------------------------------------------------------#
    # Private Helper Functions
    #-----------------------------------------------------------------------#
    def checkFrame(self):
        ''' Check and decode the next frame

        :returns: True if we successful, False otherwise
        '''
        start = self.__buffer.find(self.__start)
        if start == -1: return False
        if start > 0 : # go ahead and skip old bad data
            self.__buffer = self.__buffer[start:]

        end = self.__buffer.find(self.__end)
        if (end != -1):
            self.__header['len'] = end
            self.__header['crc'] = self.__buffer[end-1:end]
            # return checkCRC(data, self.__header['crc'])
            return True
        return False

    def advanceFrame(self):
        ''' Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        '''
        self.__buffer = self.__buffer[self.__header['len'] + 2:]
        self.__header = {'crc':0x0000, 'len':0}

    def isFrameReady(self):
        ''' Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        '''
        return len(self.__buffer) > 1

    def addToFrame(self, message):
        ''' Add the next message to the frame buffer
        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        '''
        self.__buffer += message

    def getFrame(self):
        ''' Get the next frame from the buffer

        :returns: The frame data or ''
        '''
        return self.__buffer[1:self.__header['len']]

    def populateResult(self, result):
        ''' Populates the modbus result header
   
        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        '''
        pass # no header for serial

    #-----------------------------------------------------------------------#
    # Public Member Functions
    #-----------------------------------------------------------------------#
    def processIncomingPacket(self, data, callback):
        ''' The new packet processing pattern

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 / N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.

        :param data: The new packet data
        :param callback: The function to send results to
        '''
        self.addToFrame(data)
        while self.isFrameReady():
            if self.checkFrame():
                result = self.decoder.decode(self.getFrame())
                if result is None:
                    raise ModbusIOException("Unable to decode response")
                self.populate(result)
                self.advanceFrame()
                callback(result) # defer or push to a thread?
            else: break

    def buildPacket(self, message):
        ''' Creates a ready to send modbus packet

        :param message: The request/response to send
        :returns: The encoded packet
        '''
        data = self._preflight(message.encode())
        packet = struct.pack('>BB',
                message.unit_id,
                message.function_code) + data
        packet = packet + struct.pack("<H", computeCRC(packet))
        return packet

    def _preflight(self, data):
        ''' Preflight buffer test

        This basically scans the buffer for start and end
        tags and if found, escapes them.

        :param data: The message to escape
        :returns: the escaped packet
        '''
        def _filter(a):
            return a*2 if a in ['}', '{'] else a, data
        return ''.join(map(_filter, data))

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ModbusTransactionManager",
    "ModbusSocketFramer", "ModbusRtuFramer",
    "ModbusAsciiFramer", "ModbusBinaryFramer",
]
