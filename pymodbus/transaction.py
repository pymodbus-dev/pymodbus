'''
Collection of transaction based abstractions
'''
import sys
import struct
import socket
from binascii import b2a_hex, a2b_hex
from serial import SerialException
from pymodbus.exceptions import ModbusIOException, NotImplementedException
from pymodbus.exceptions import InvalidMessageRecievedException
from pymodbus.constants  import Defaults
from pymodbus.interfaces import IModbusFramer
from pymodbus.utilities  import checkCRC, computeCRC
from pymodbus.utilities  import checkLRC, computeLRC
from pymodbus.compat import iterkeys, imap, byte2int

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)


#---------------------------------------------------------------------------#
# The Global Transaction Manager
#---------------------------------------------------------------------------#
class ModbusTransactionManager(object):
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

    def __init__(self, client, **kwargs):
        ''' Initializes an instance of the ModbusTransactionManager

        :param client: The client socket wrapper
        :param retry_on_empty: Should the client retry on empty
        :param retries: The number of retries to allow
        '''
        self.tid = Defaults.TransactionId
        self.client = client
        self.retry_on_empty = kwargs.get('retry_on_empty', Defaults.RetryOnEmpty)
        self.retries = kwargs.get('retries', Defaults.Retries)
        if client:
            self._set_adu_size()

    def _set_adu_size(self):
        # base ADU size of modbus frame in bytes
        if isinstance(self.client.framer, ModbusSocketFramer):
            self.base_adu_size = 7  # tid(2), pid(2), length(2), uid(1)
        elif isinstance(self.client.framer, ModbusRtuFramer):
            self.base_adu_size = 3  # address(1), CRC(2)
        elif isinstance(self.client.framer, ModbusAsciiFramer):
            self.base_adu_size = 7  # start(1)+ Address(2), LRC(2) + end(2)
        elif isinstance(self.client.framer, ModbusBinaryFramer):
            self.base_adu_size = 5  # start(1) + Address(1), CRC(2) + end(1)
        else:
            self.base_adu_size = -1

    def _calculate_response_length(self, expected_pdu_size):
        if self.base_adu_size == -1:
            return None
        else:
            return self.base_adu_size + expected_pdu_size

    def _calculate_exception_length(self):
        ''' Returns the length of the Modbus Exception Response according to
        the type of Framer.
        '''
        if isinstance(self.client.framer, ModbusSocketFramer):
            return self.base_adu_size + 2  # Fcode(1), ExcecptionCode(1)
        elif isinstance(self.client.framer, ModbusAsciiFramer):
            return self.base_adu_size + 4  # Fcode(2), ExcecptionCode(2)
        elif isinstance(self.client.framer, (ModbusRtuFramer, ModbusBinaryFramer)):
            return self.base_adu_size + 2  # Fcode(1), ExcecptionCode(1)

        return None

    def _check_response(self, response):
        ''' Checks if the response is a Modbus Exception.
        '''
        if isinstance(self.client.framer, ModbusSocketFramer):
            if len(response) >= 8 and byte2int(response[7]) > 128:
                return False
        elif isinstance(self.client.framer, ModbusAsciiFramer):
            if len(response) >= 5 and int(response[3:5], 16) > 128:
                return False
        elif isinstance(self.client.framer, (ModbusRtuFramer, ModbusBinaryFramer)):
            if len(response) >= 2 and byte2int(response[1]) > 128:
                return False

        return True

    def execute(self, request):
        ''' Starts the producer to send the next request to
        consumer.write(Frame(request))
        '''
        retries = self.retries
        request.transaction_id = self.getNextTID()
        _logger.debug("Running transaction %d" % request.transaction_id)
        self.client.framer.resetFrame()
        expected_response_length = None
        if not isinstance(self.client.framer, ModbusSocketFramer):
            if hasattr(request, "get_response_pdu_size"):
                response_pdu_size = request.get_response_pdu_size()
                if isinstance(self.client.framer, ModbusAsciiFramer):
                    response_pdu_size = response_pdu_size * 2
                if response_pdu_size:
                    expected_response_length = self._calculate_response_length(response_pdu_size)

        while retries > 0:
            try:
                last_exception = None
                self.client.connect()
                packet = self.client.framer.buildPacket(request)
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug("send: " + " ".join([hex(byte2int(x)) for x in packet]))
                self._send(packet)
                # exception = False
                result = self._recv(expected_response_length or 1024)

                if not result and self.retry_on_empty:
                    retries -= 1
                    continue
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug("recv: " + " ".join([hex(byte2int(x)) for x in result]))
                self.client.framer.processIncomingPacket(result, self.addTransaction)
                break
            except (socket.error, ModbusIOException, InvalidMessageRecievedException) as msg:
                self.client.close()
                _logger.debug("Transaction failed. (%s) " % msg)
                retries -= 1
                last_exception = msg
        response = self.getTransaction(request.transaction_id)
        if not response:
            if len(self.transactions):
                response = self.getTransaction(tid=0)
            else:
                last_exception = last_exception or ("No Response "
                                                    "received from the remote unit")
                response = ModbusIOException(last_exception)

        return response

    def _send(self, packet):
        return self.client._send(packet)

    def _recv(self, expected_response_length):
        retries = self.retries
        exception = False
        while retries:
            result = self.client._recv(expected_response_length or 1024)
            while result and expected_response_length and len(
                    result) < expected_response_length:
                if not exception and not self._check_response(result):
                    exception = True
                    expected_response_length = self._calculate_exception_length()
                    continue
                if isinstance(self.client.framer, ModbusSocketFramer):
                    # Ommit UID, which is included in header size
                    h_size = self.client.framer._hsize
                    length = struct.unpack(">H", result[4:6])[0] -1
                    expected_response_length = h_size + length

                if expected_response_length != len(result):
                    _logger.debug("Expected - {} bytes, "
                                  "Actual - {} bytes".format(
                        expected_response_length, len(result))
                    )
                    try:
                        r = self.client._recv(
                            expected_response_length - len(result)
                        )
                        result += r
                        if not r:
                            # If no response being recived there
                            # is no point in conitnuing
                            break
                    except (TimeoutError, SerialException):
                        break
                else:
                    break

            if result:
                break
            retries -= 1
        return result

    def addTransaction(self, request, tid=None):
        ''' Adds a transaction to the handler

        This holds the requets in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        '''
        raise NotImplementedException("addTransaction")

    def getTransaction(self, tid):
        ''' Returns a transaction matching the referenced tid

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        '''
        raise NotImplementedException("getTransaction")

    def delTransaction(self, tid):
        ''' Removes a transaction matching the referenced tid

        :param tid: The transaction to remove
        '''
        raise NotImplementedException("delTransaction")

    def getNextTID(self):
        ''' Retrieve the next unique transaction identifier

        This handles incrementing the identifier after
        retrieval

        :returns: The next unique transaction identifier
        '''
        self.tid = (self.tid + 1) & 0xffff
        return self.tid

    def reset(self):
        ''' Resets the transaction identifier '''
        self.tid = Defaults.TransactionId
        self.transactions = type(self.transactions)()


class DictTransactionManager(ModbusTransactionManager):
    ''' Impelements a transaction for a manager where the
    results are keyed based on the supplied transaction id.
    '''

    def __init__(self, client, **kwargs):
        ''' Initializes an instance of the ModbusTransactionManager

        :param client: The client socket wrapper
        '''
        self.transactions = {}
        super(DictTransactionManager, self).__init__(client, **kwargs)

    def __iter__(self):
        ''' Iterater over the current managed transactions

        :returns: An iterator of the managed transactions
        '''
        return iterkeys(self.transactions)

    def addTransaction(self, request, tid=None):
        ''' Adds a transaction to the handler

        This holds the requets in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        '''
        tid = tid if tid != None else request.transaction_id
        _logger.debug("adding transaction %d" % tid)
        self.transactions[tid] = request

    def getTransaction(self, tid):
        ''' Returns a transaction matching the referenced tid

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        '''
        _logger.debug("getting transaction %d" % tid)
        return self.transactions.pop(tid, None)

    def delTransaction(self, tid):
        ''' Removes a transaction matching the referenced tid

        :param tid: The transaction to remove
        '''
        _logger.debug("deleting transaction %d" % tid)
        self.transactions.pop(tid, None)


class FifoTransactionManager(ModbusTransactionManager):
    ''' Impelements a transaction for a manager where the
    results are returned in a FIFO manner.
    '''

    def __init__(self, client, **kwargs):
        ''' Initializes an instance of the ModbusTransactionManager

        :param client: The client socket wrapper
        '''
        super(FifoTransactionManager, self).__init__(client, **kwargs)
        self.transactions = []

    def __iter__(self):
        ''' Iterater over the current managed transactions

        :returns: An iterator of the managed transactions
        '''
        return iter(self.transactions)

    def addTransaction(self, request, tid=None):
        ''' Adds a transaction to the handler

        This holds the requets in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        '''
        tid = tid if tid != None else request.transaction_id
        _logger.debug("adding transaction %d" % tid)
        self.transactions.append(request)

    def getTransaction(self, tid):
        ''' Returns a transaction matching the referenced tid

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        '''
        _logger.debug("getting transaction %s" % str(tid))
        return self.transactions.pop(0) if self.transactions else None

    def delTransaction(self, tid):
        ''' Removes a transaction matching the referenced tid

        :param tid: The transaction to remove
        '''
        _logger.debug("deleting transaction %d" % tid)
        if self.transactions: self.transactions.pop(0)


#---------------------------------------------------------------------------#
# Modbus TCP Message
#---------------------------------------------------------------------------#
class ModbusSocketFramer(IModbusFramer):
    ''' Modbus Socket Frame controller

    Before each modbus TCP message is an MBAP header which is used as a
    message frame.  It allows us to easily separate messages as follows::

        [         MBAP Header         ] [ Function Code] [ Data ]
        [ tid ][ pid ][ length ][ uid ]
          2b     2b     2b        1b           1b           Nb

        while len(message) > 0:
            tid, pid, length`, uid = struct.unpack(">HHHB", message)
            request = message[0:7 + length - 1`]
            message = [7 + length - 1:]

        * length = uid + function code + data
        * The -1 is to account for the uid byte
    '''

    def __init__(self, decoder):
        ''' Initializes a new instance of the framer

        :param decoder: The decoder factory implementation to use
        '''
        self._buffer = b''
        self._header = {'tid':0, 'pid':0, 'len':0, 'uid':0}
        self._hsize  = 0x07
        self.decoder  = decoder

    #-----------------------------------------------------------------------#
    # Private Helper Functions
    #-----------------------------------------------------------------------#
    def checkFrame(self):
        '''
        Check and decode the next frame Return true if we were successful
        '''
        if len(self._buffer) > self._hsize:
            self._header['tid'], self._header['pid'], \
            self._header['len'], self._header['uid'] = struct.unpack(
                    '>HHHB', self._buffer[0:self._hsize])

            # someone sent us an error? ignore it
            if self._header['len'] < 2:
                self.advanceFrame()
            # we have at least a complete message, continue
            elif len(self._buffer) - self._hsize + 1 >= self._header['len']:
                return True
        # we don't have enough of a message yet, wait
        return False

    def advanceFrame(self):
        ''' Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        '''
        length = self._hsize + self._header['len'] - 1
        self._buffer = self._buffer[length:]
        self._header = {'tid':0, 'pid':0, 'len':0, 'uid':0}

    def isFrameReady(self):
        ''' Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder factory know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        '''
        return len(self._buffer) > self._hsize

    def addToFrame(self, message):
        ''' Adds new packet data to the current frame buffer

        :param message: The most recent packet
        '''
        self._buffer += message

    def getFrame(self):
        ''' Return the next frame from the buffered data

        :returns: The next full frame buffer
        '''
        length = self._hsize + self._header['len'] - 1
        return self._buffer[self._hsize:length]

    def populateResult(self, result):
        '''
        Populates the modbus result with the transport specific header
        information (pid, tid, uid, checksum, etc)

        :param result: The response packet
        '''
        result.transaction_id = self._header['tid']
        result.protocol_id = self._header['pid']
        result.unit_id = self._header['uid']

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
        _logger.debug(' '.join([hex(byte2int(x)) for x in data]))
        self.addToFrame(data)
        while True:
            if self.isFrameReady():
                if self.checkFrame():
                    self._process(callback)
                else: self.resetFrame()
            else:
                if len(self._buffer):
                    # Possible error ???
                    if self._header['len'] < 2:
                        self._process(callback, error=True)
                break

    def _process(self, callback, error=False):
        """
        Process incoming packets irrespective error condition
        """
        data = self.getRawFrame() if error else self.getFrame()
        result = self.decoder.decode(data)
        if result is None:
            raise ModbusIOException("Unable to decode request")
        elif error and result.function_code < 0x80:
            raise InvalidMessageRecievedException(result)
        else:
            self.populateResult(result)
            self.advanceFrame()
            callback(result)  # defer or push to a thread?

    def resetFrame(self):
        ''' Reset the entire message frame.
        This allows us to skip ovver errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        '''
        self._buffer = b''
        self._header = {}

    def getRawFrame(self):
        """
        Returns the complete buffer
        """
        return self._buffer

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

        [ Start Wait ] [Address ][ Function Code] [ Data ][ CRC ][  End Wait  ]
          3.5 chars     1b         1b               Nb      2b      3.5 chars

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

        ------------------------------------------------------------------
         Baud  1.5c (18 bits)   3.5c (38 bits)
        ------------------------------------------------------------------
         1200   13333.3 us       31666.7 us
         4800    3333.3 us        7916.7 us
         9600    1666.7 us        3958.3 us
        19200     833.3 us        1979.2 us
        38400     416.7 us         989.6 us
        ------------------------------------------------------------------
        1 Byte = start + 8 bits + parity + stop = 11 bits
        (1/Baud)(bits) = delay seconds
    '''

    def __init__(self, decoder):
        ''' Initializes a new instance of the framer

        :param decoder: The decoder factory implementation to use
        '''
        self._buffer = b''
        self._header = {}
        self._hsize  = 0x01
        self._end    = b'\x0d\x0a'
        self._min_frame_size = 4
        self.decoder  = decoder

    #-----------------------------------------------------------------------#
    # Private Helper Functions
    #-----------------------------------------------------------------------#
    def checkFrame(self):
        '''
        Check if the next frame is available. Return True if we were
        successful.
        '''
        try:
            self.populateHeader()
            frame_size = self._header['len']
            data = self._buffer[:frame_size - 2]
            crc = self._buffer[frame_size - 2:frame_size]
            crc_val = (byte2int(crc[0]) << 8) + byte2int(crc[1])
            return checkCRC(data, crc_val)
        except (IndexError, KeyError):
            return False

    def advanceFrame(self):
        ''' Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        '''
        try:
            self._buffer = self._buffer[self._header['len']:]
        except KeyError:
            #   Error response, no header len found
            self.resetFrame()
        self._header = {}

    def resetFrame(self):
        ''' Reset the entire message frame.
        This allows us to skip ovver errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        '''
        self._buffer = b''
        self._header = {}

    def isFrameReady(self):
        ''' Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        '''
        return len(self._buffer) > self._hsize

    def populateHeader(self):
        ''' Try to set the headers `uid`, `len` and `crc`.

        This method examines `self._buffer` and writes meta
        information into `self._header`. It calculates only the
        values for headers that are not already in the dictionary.

        Beware that this method will raise an IndexError if
        `self._buffer` is not yet long enough.
        '''
        self._header['uid'] = byte2int(self._buffer[0])
        func_code = byte2int(self._buffer[1])
        pdu_class = self.decoder.lookupPduClass(func_code)
        size = pdu_class.calculateRtuFrameSize(self._buffer)
        self._header['len'] = size
        self._header['crc'] = self._buffer[size - 2:size]

    def addToFrame(self, message):
        '''
        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        '''
        self._buffer += message

    def getFrame(self):
        ''' Get the next frame from the buffer

        :returns: The frame data or ''
        '''
        start  = self._hsize
        end    = self._header['len'] - 2
        buffer = self._buffer[start:end]
        if end > 0: return buffer
        return ''

    def populateResult(self, result):
        ''' Populates the modbus result header

        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        '''
        result.unit_id = self._header['uid']

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
        while True:
            if self.isFrameReady():
                if self.checkFrame():
                    self._process(callback)
                else:
                    # Could be an error response
                    if len(self._buffer):
                        # Possible error ???
                       self._process(callback, error=True)
            else:
                if len(self._buffer):
                    # Possible error ???
                    if self._header.get('len', 0) < 2:
                        self._process(callback, error=True)
                break

    def buildPacket(self, message):
        ''' Creates a ready to send modbus packet

        :param message: The populated request/response to send
        '''
        data = message.encode()
        packet = struct.pack('>BB',
            message.unit_id,
            message.function_code) + data
        packet += struct.pack(">H", computeCRC(packet))
        return packet

    def _process(self, callback, error=False):
        """
        Process incoming packets irrespective error condition
        """
        data = self.getRawFrame() if error else self.getFrame()
        result = self.decoder.decode(data)
        if result is None:
            raise ModbusIOException("Unable to decode request")
        elif error and result.function_code < 0x80:
            raise InvalidMessageRecievedException(result)
        else:
            self.populateResult(result)
            self.advanceFrame()
            callback(result)  # defer or push to a thread?

    def getRawFrame(self):
        """
        Returns the complete buffer
        """
        return self._buffer



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
        self._buffer = b''
        self._header = {'lrc':'0000', 'len':0, 'uid':0x00}
        self._hsize  = 0x02
        self._start  = b':'
        self._end    = b"\r\n"
        self.decoder  = decoder

    #-----------------------------------------------------------------------#
    # Private Helper Functions
    #-----------------------------------------------------------------------#
    def checkFrame(self):
        ''' Check and decode the next frame

        :returns: True if we successful, False otherwise
        '''
        start = self._buffer.find(self._start)
        if start == -1: return False
        if start > 0 :  # go ahead and skip old bad data
            self._buffer = self._buffer[start:]
            start = 0

        end = self._buffer.find(self._end)
        if (end != -1):
            self._header['len'] = end
            self._header['uid'] = int(self._buffer[1:3], 16)
            self._header['lrc'] = int(self._buffer[end - 2:end], 16)
            data = a2b_hex(self._buffer[start + 1:end - 2])
            return checkLRC(data, self._header['lrc'])
        return False

    def advanceFrame(self):
        ''' Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        '''
        self._buffer = self._buffer[self._header['len'] + 2:]
        self._header = {'lrc':'0000', 'len':0, 'uid':0x00}

    def isFrameReady(self):
        ''' Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        '''
        return len(self._buffer) > 1

    def addToFrame(self, message):
        ''' Add the next message to the frame buffer
        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        '''
        self._buffer += message

    def getFrame(self):
        ''' Get the next frame from the buffer

        :returns: The frame data or ''
        '''
        start  = self._hsize + 1
        end    = self._header['len'] - 2
        buffer   = self._buffer[start:end]
        if end > 0: return a2b_hex(buffer)
        return b''

    def resetFrame(self):
        ''' Reset the entire message frame.
        This allows us to skip ovver errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        '''
        self._buffer = b''
        self._header = {'lrc':'0000', 'len':0, 'uid':0x00}

    def populateResult(self, result):
        ''' Populates the modbus result header

        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        '''
        result.unit_id = self._header['uid']

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
                frame = self.getFrame()
                result = self.decoder.decode(frame)
                if result is None:
                    raise ModbusIOException("Unable to decode response")
                self.populateResult(result)
                self.advanceFrame()
                callback(result)  # defer this
            else:
                break

    def buildPacket(self, message):
        ''' Creates a ready to send modbus packet
        Built off of a  modbus request/response

        :param message: The request/response to send
        :return: The encoded packet
        '''
        encoded  = message.encode()
        buffer     = struct.pack('>BB', message.unit_id, message.function_code)
        checksum = computeLRC(encoded + buffer)

        packet = bytearray()
        params = (message.unit_id, message.function_code)
        packet.extend(self._start)
        packet.extend(('%02x%02x' % params).encode())
        packet.extend(b2a_hex(encoded))
        packet.extend(('%02x' % checksum).encode())
        packet.extend(self._end)
        return bytes(packet).upper()


#---------------------------------------------------------------------------#
# Modbus Binary Message
#---------------------------------------------------------------------------#
class ModbusBinaryFramer(IModbusFramer):
    '''
    Modbus Binary Frame Controller::

        [ Start ][Address ][ Function ][ Data ][ CRC ][ End ]
          1b        1b         1b         Nb     2b     1b

        * data can be 0 - 2x252 chars
        * end is   '}'
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
        self._buffer = b''
        self._header = {'crc':0x0000, 'len':0, 'uid':0x00}
        self._hsize  = 0x01
        self._start  = b'\x7b'  # {
        self._end    = b'\x7d'  # }
        self._repeat = [b'}'[0], b'{'[0]] # python3 hack
        self.decoder  = decoder

    #-----------------------------------------------------------------------#
    # Private Helper Functions
    #-----------------------------------------------------------------------#
    def checkFrame(self):
        ''' Check and decode the next frame

        :returns: True if we are successful, False otherwise
        '''
        start = self._buffer.find(self._start)
        if start == -1: return False
        if start > 0 :  # go ahead and skip old bad data
            self._buffer = self._buffer[start:]

        end = self._buffer.find(self._end)
        if (end != -1):
            self._header['len'] = end
            self._header['uid'] = struct.unpack('>B', self._buffer[1:2])
            self._header['crc'] = struct.unpack('>H', self._buffer[end - 2:end])[0]
            data = self._buffer[start + 1:end - 2]
            return checkCRC(data, self._header['crc'])
        return False

    def advanceFrame(self):
        ''' Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        '''
        self._buffer = self._buffer[self._header['len'] + 2:]
        self._header = {'crc':0x0000, 'len':0, 'uid':0x00}

    def isFrameReady(self):
        ''' Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        '''
        return len(self._buffer) > 1

    def addToFrame(self, message):
        ''' Add the next message to the frame buffer
        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        '''
        self._buffer += message

    def getFrame(self):
        ''' Get the next frame from the buffer

        :returns: The frame data or ''
        '''
        start  = self._hsize + 1
        end    = self._header['len'] - 2
        buffer = self._buffer[start:end]
        if end > 0: return buffer
        return b''

    def populateResult(self, result):
        ''' Populates the modbus result header

        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        '''
        result.unit_id = self._header['uid']

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
                self.populateResult(result)
                self.advanceFrame()
                callback(result)  # defer or push to a thread?
            else:
                break

    def buildPacket(self, message):
        ''' Creates a ready to send modbus packet

        :param message: The request/response to send
        :returns: The encoded packet
        '''
        data = self._preflight(message.encode())
        packet = struct.pack('>BB',
            message.unit_id,
            message.function_code) + data
        packet += struct.pack(">H", computeCRC(packet))
        packet  = self._start + packet + self._end
        return packet

    def _preflight(self, data):
        ''' Preflight buffer test

        This basically scans the buffer for start and end
        tags and if found, escapes them.

        :param data: The message to escape
        :returns: the escaped packet
        '''
        array = bytearray()
        for d in data:
            if d in self._repeat:
                array.append(d)
            array.append(d)
        return bytes(array)

    def resetFrame(self):
        ''' Reset the entire message frame.
        This allows us to skip ovver errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        '''
        self._buffer = b''
        self._header = {'crc': 0x0000, 'len': 0, 'uid': 0x00}

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "FifoTransactionManager",
    "DictTransactionManager",
    "ModbusSocketFramer", "ModbusRtuFramer",
    "ModbusAsciiFramer", "ModbusBinaryFramer",
]
