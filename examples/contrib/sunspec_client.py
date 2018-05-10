from pymodbus.constants import Endian
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from twisted.internet.defer import Deferred


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
logging.basicConfig()


# --------------------------------------------------------------------------- # 
# Sunspec Common Constants
# --------------------------------------------------------------------------- # 
class SunspecDefaultValue(object):
    """ A collection of constants to indicate if
    a value is not implemented.
    """
    Signed16        = 0x8000
    Unsigned16      = 0xffff
    Accumulator16   = 0x0000
    Scale           = 0x8000
    Signed32        = 0x80000000
    Float32         = 0x7fc00000
    Unsigned32      = 0xffffffff
    Accumulator32   = 0x00000000
    Signed64        = 0x8000000000000000
    Unsigned64      = 0xffffffffffffffff
    Accumulator64   = 0x0000000000000000
    String          = '\x00'


class SunspecStatus(object):
    """ Indicators of the current status of a
    sunspec device
    """
    Normal  = 0x00000000
    Error   = 0xfffffffe
    Unknown = 0xffffffff


class SunspecIdentifier(object):
    """ Assigned identifiers that are pre-assigned
    by the sunspec protocol.
    """
    Sunspec = 0x53756e53


class SunspecModel(object):
    """ Assigned device indentifiers that are pre-assigned
    by the sunspec protocol.
    """
    #---------------------------------------------
    # 0xx Common Models
    #---------------------------------------------
    CommonBlock                              = 1
    AggregatorBlock                          = 2

    #---------------------------------------------
    # 1xx Inverter Models
    #---------------------------------------------
    SinglePhaseIntegerInverter               = 101
    SplitPhaseIntegerInverter                = 102
    ThreePhaseIntegerInverter                = 103
    SinglePhaseFloatsInverter                = 103
    SplitPhaseFloatsInverter                 = 102
    ThreePhaseFloatsInverter                 = 103

    #---------------------------------------------
    # 2xx Meter Models
    #---------------------------------------------
    SinglePhaseMeter                         = 201
    SplitPhaseMeter                          = 201
    WyeConnectMeter                          = 201
    DeltaConnectMeter                        = 201

    #---------------------------------------------
    # 3xx Environmental Models
    #---------------------------------------------
    BaseMeteorological                       = 301
    Irradiance                               = 302
    BackOfModuleTemperature                  = 303
    Inclinometer                             = 304
    Location                                 = 305
    ReferencePoint                           = 306
    BaseMeteorological                       = 307
    MiniMeteorological                       = 308

    #---------------------------------------------
    # 4xx String Combiner Models             
    #---------------------------------------------
    BasicStringCombiner                      = 401
    AdvancedStringCombiner                   = 402

    #---------------------------------------------
    # 5xx Panel Models
    #---------------------------------------------
    PanelFloat                               = 501
    PanelInteger                             = 502

    #---------------------------------------------
    # 641xx Outback Blocks
    #---------------------------------------------
    OutbackDeviceIdentifier                  = 64110
    OutbackChargeController                  = 64111
    OutbackFMSeriesChargeController          = 64112
    OutbackFXInverterRealTime                = 64113
    OutbackFXInverterConfiguration           = 64114
    OutbackSplitPhaseRadianInverter          = 64115
    OutbackRadianInverterConfiguration       = 64116
    OutbackSinglePhaseRadianInverterRealTime = 64117
    OutbackFLEXNetDCRealTime                 = 64118
    OutbackFLEXNetDCConfiguration            = 64119
    OutbackSystemControl                     = 64120

    #---------------------------------------------
    # 64xxx Vender Extension Block
    #---------------------------------------------
    EndOfSunSpecMap                          = 65535

    @classmethod
    def lookup(klass, code):
        """ Given a device identifier, return the
        device model name for that identifier

        :param code: The device code to lookup
        :returns: The device model name, or None if none available
        """
        values = dict((v, k) for k, v in klass.__dict__.iteritems()
            if not callable(v))
        return values.get(code, None)


class SunspecOffsets(object):
    """ Well known offsets that are used throughout
    the sunspec protocol
    """
    CommonBlock             = 40000
    CommonBlockLength       = 69
    AlternateCommonBlock    = 50000


# --------------------------------------------------------------------------- # 
# Common Functions
# --------------------------------------------------------------------------- # 
def defer_or_apply(func):
    """ Decorator to apply an adapter method
    to a result regardless if it is a deferred
    or a concrete response.

    :param func: The function to decorate
    """
    def closure(future, adapt):
        if isinstance(future, Deferred):
            d = Deferred()
            future.addCallback(lambda r: d.callback(adapt(r)))
            return d
        return adapt(future)
    return closure


def create_sunspec_sync_client(host):
    """ A quick helper method to create a sunspec
    client.

    :param host: The host to connect to
    :returns: an initialized SunspecClient
    """
    modbus = ModbusTcpClient(host)
    modbus.connect()
    client = SunspecClient(modbus)
    client.initialize()
    return client


# --------------------------------------------------------------------------- # 
# Sunspec Client
# --------------------------------------------------------------------------- # 
class SunspecDecoder(BinaryPayloadDecoder):
    """ A decoder that deals correctly with the sunspec
    binary format.
    """

    def __init__(self, payload, byteorder):
        """ Initialize a new instance of the SunspecDecoder

        .. note:: This is always set to big endian byte order
        as specified in the protocol.
        """
        byteorder = Endian.Big
        BinaryPayloadDecoder.__init__(self, payload, byteorder)

    def decode_string(self, size=1):
        """ Decodes a string from the buffer

        :param size: The size of the string to decode
        """
        self._pointer += size
        string = self._payload[self._pointer - size:self._pointer]
        return string.split(SunspecDefaultValue.String)[0]


class SunspecClient(object):

    def __init__(self, client):
        """ Initialize a new instance of the client

        :param client: The modbus client to use
        """
        self.client = client
        self.offset = SunspecOffsets.CommonBlock

    def initialize(self):
        """ Initialize the underlying client values

        :returns: True if successful, false otherwise
        """
        decoder  = self.get_device_block(self.offset, 2)
        if decoder.decode_32bit_uint() == SunspecIdentifier.Sunspec:
            return True
        self.offset = SunspecOffsets.AlternateCommonBlock
        decoder  = self.get_device_block(self.offset, 2)
        return decoder.decode_32bit_uint() == SunspecIdentifier.Sunspec

    def get_common_block(self):
        """ Read and return the sunspec common information
        block.

        :returns: A dictionary of the common block information
        """
        length  = SunspecOffsets.CommonBlockLength
        decoder = self.get_device_block(self.offset, length)
        return {
            'SunSpec_ID':       decoder.decode_32bit_uint(),
            'SunSpec_DID':      decoder.decode_16bit_uint(),
            'SunSpec_Length':   decoder.decode_16bit_uint(),
            'Manufacturer':     decoder.decode_string(size=32),
            'Model':            decoder.decode_string(size=32),
            'Options':          decoder.decode_string(size=16),
            'Version':          decoder.decode_string(size=16),
            'SerialNumber':     decoder.decode_string(size=32),
            'DeviceAddress':    decoder.decode_16bit_uint(),
            'Next_DID':         decoder.decode_16bit_uint(),
            'Next_DID_Length':  decoder.decode_16bit_uint(),
        }

    def get_device_block(self, offset, size):
        """ A helper method to retrieve the next device block

        .. note:: We will read 2 more registers so that we have
        the information for the next block.

        :param offset: The offset to start reading at
        :param size: The size of the offset to read
        :returns: An initialized decoder for that result
        """
        _logger.debug("reading device block[{}..{}]".format(offset, offset + size))
        response = self.client.read_holding_registers(offset, size + 2)
        return SunspecDecoder.fromRegisters(response.registers)

    def get_all_device_blocks(self):
        """ Retrieve all the available blocks in the supplied
        sunspec device.

        .. note:: Since we do not know how to decode the available
        blocks, this returns a list of dictionaries of the form:

            decoder: the-binary-decoder,
            model:   the-model-identifier (name)

        :returns: A list of the available blocks
        """
        blocks = []
        offset = self.offset + 2
        model  = SunspecModel.CommonBlock
        while model != SunspecModel.EndOfSunSpecMap:
            decoder = self.get_device_block(offset, 2)
            model   = decoder.decode_16bit_uint()
            length  = decoder.decode_16bit_uint()
            blocks.append({
                'model' : model,
                'name'  : SunspecModel.lookup(model),
                'length': length,
                'offset': offset + length + 2
            })
            offset += length + 2
        return blocks


#------------------------------------------------------------
# A quick test runner
#------------------------------------------------------------
if __name__ == "__main__":
    client = create_sunspec_sync_client("YOUR.HOST.GOES.HERE")

    # print out all the device common block
    common = client.get_common_block()
    for key, value in common.iteritems():
        if key == "SunSpec_DID":
            value = SunspecModel.lookup(value)
        print("{:<20}: {}".format(key, value))

    # print out all the available device blocks
    blocks = client.get_all_device_blocks()
    for block in blocks:
        print(block)

    client.client.close()
