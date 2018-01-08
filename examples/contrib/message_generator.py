#!/usr/bin/env python
"""
Modbus Message Generator
--------------------------------------------------------------------------

The following is an example of how to generate example encoded messages
for the supplied modbus format:

* tcp    - `./generate-messages.py -f tcp -m rx -b`
* ascii  - `./generate-messages.py -f ascii -m tx -a`
* rtu    - `./generate-messages.py -f rtu -m rx -b`
* binary - `./generate-messages.py -f binary -m tx -b`
"""
from optparse import OptionParser
import codecs as c
# -------------------------------------------------------------------------- #
# import all the available framers
# -------------------------------------------------------------------------- #
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.transaction import ModbusBinaryFramer
from pymodbus.transaction import ModbusAsciiFramer
from pymodbus.transaction import ModbusRtuFramer
# -------------------------------------------------------------------------- #
# import all available messages
# -------------------------------------------------------------------------- #
from pymodbus.bit_read_message import *
from pymodbus.bit_write_message import *
from pymodbus.diag_message import *
from pymodbus.file_message import *
from pymodbus.other_message import *
from pymodbus.mei_message import *
from pymodbus.register_read_message import *
from pymodbus.register_write_message import *
from pymodbus.compat import IS_PYTHON3

# -------------------------------------------------------------------------- #
# initialize logging
# -------------------------------------------------------------------------- #
import logging
modbus_log = logging.getLogger("pymodbus")


# -------------------------------------------------------------------------- #
# enumerate all request messages
# -------------------------------------------------------------------------- #
_request_messages = [
    ReadHoldingRegistersRequest,
    ReadDiscreteInputsRequest,
    ReadInputRegistersRequest,
    ReadCoilsRequest,
    WriteMultipleCoilsRequest,
    WriteMultipleRegistersRequest,
    WriteSingleRegisterRequest,
    WriteSingleCoilRequest,
    ReadWriteMultipleRegistersRequest,

    ReadExceptionStatusRequest,
    GetCommEventCounterRequest,
    GetCommEventLogRequest,
    ReportSlaveIdRequest,

    ReadFileRecordRequest,
    WriteFileRecordRequest,
    MaskWriteRegisterRequest,
    ReadFifoQueueRequest,

    ReadDeviceInformationRequest,

    ReturnQueryDataRequest,
    RestartCommunicationsOptionRequest,
    ReturnDiagnosticRegisterRequest,
    ChangeAsciiInputDelimiterRequest,
    ForceListenOnlyModeRequest,
    ClearCountersRequest,
    ReturnBusMessageCountRequest,
    ReturnBusCommunicationErrorCountRequest,
    ReturnBusExceptionErrorCountRequest,
    ReturnSlaveMessageCountRequest,
    ReturnSlaveNoResponseCountRequest,
    ReturnSlaveNAKCountRequest,
    ReturnSlaveBusyCountRequest,
    ReturnSlaveBusCharacterOverrunCountRequest,
    ReturnIopOverrunCountRequest,
    ClearOverrunCountRequest,
    GetClearModbusPlusRequest
]


# -------------------------------------------------------------------------- #
# enumerate all response messages
# -------------------------------------------------------------------------- #
_response_messages = [
    ReadHoldingRegistersResponse,
    ReadDiscreteInputsResponse,
    ReadInputRegistersResponse,
    ReadCoilsResponse,
    WriteMultipleCoilsResponse,
    WriteMultipleRegistersResponse,
    WriteSingleRegisterResponse,
    WriteSingleCoilResponse,
    ReadWriteMultipleRegistersResponse,

    ReadExceptionStatusResponse,
    GetCommEventCounterResponse,
    GetCommEventLogResponse,
    ReportSlaveIdResponse,

    ReadFileRecordResponse,
    WriteFileRecordResponse,
    MaskWriteRegisterResponse,
    ReadFifoQueueResponse,

    ReadDeviceInformationResponse,

    ReturnQueryDataResponse,
    RestartCommunicationsOptionResponse,
    ReturnDiagnosticRegisterResponse,
    ChangeAsciiInputDelimiterResponse,
    ForceListenOnlyModeResponse,
    ClearCountersResponse,
    ReturnBusMessageCountResponse,
    ReturnBusCommunicationErrorCountResponse,
    ReturnBusExceptionErrorCountResponse,
    ReturnSlaveMessageCountResponse,
    ReturnSlaveNoReponseCountResponse,
    ReturnSlaveNAKCountResponse,
    ReturnSlaveBusyCountResponse,
    ReturnSlaveBusCharacterOverrunCountResponse,
    ReturnIopOverrunCountResponse,
    ClearOverrunCountResponse,
    GetClearModbusPlusResponse
]


# -------------------------------------------------------------------------- #
# build an arguments singleton
# -------------------------------------------------------------------------- #
# Feel free to override any values here to generate a specific message
# in question. It should be noted that many argument names are reused
# between different messages, and a number of messages are simply using
# their default values.
# -------------------------------------------------------------------------- #
_arguments = {
    'address': 0x12,
    'count': 0x08,
    'value': 0x01,
    'values': [0x01] * 8,
    'read_address': 0x12,
    'read_count': 0x08,
    'write_address': 0x12,
    'write_registers': [0x01] * 8,
    'transaction': 0x01,
    'protocol': 0x00,
    'unit': 0xff,
}


# -------------------------------------------------------------------------- #
# generate all the requested messages
# -------------------------------------------------------------------------- #
def generate_messages(framer, options):
    """ A helper method to parse the command line options

    :param framer: The framer to encode the messages with
    :param options: The message options to use
    """
    if options.messages == "tx":
        messages = _request_messages
    else:
        messages = _response_messages
    for message in messages:
        message = message(**_arguments)
        print("%-44s = " % message.__class__.__name__)
        packet = framer.buildPacket(message)
        if not options.ascii:
            if not IS_PYTHON3:
                packet = packet.encode('hex')
            else:
                packet = c.encode(packet, 'hex_codec').decode('utf-8')
        print ("{}\n".format(packet))   # because ascii ends with a \r\n


# -------------------------------------------------------------------------- #
# initialize our program settings
# -------------------------------------------------------------------------- #
def get_options():
    """ A helper method to parse the command line options

    :returns: The options manager
    """
    parser = OptionParser()

    parser.add_option("-f", "--framer",
                      help="The type of framer to use "
                           "(tcp, rtu, binary, ascii)",
                      dest="framer", default="tcp")

    parser.add_option("-D", "--debug",
                      help="Enable debug tracing",
                      action="store_true", dest="debug", default=False)

    parser.add_option("-a", "--ascii",
                      help="The indicates that the message is ascii",
                      action="store_true", dest="ascii", default=True)

    parser.add_option("-b", "--binary",
                      help="The indicates that the message is binary",
                      action="store_false", dest="ascii")

    parser.add_option("-m", "--messages",
                      help="The messages to encode (rx, tx)",
                      dest="messages", default='rx')

    (opt, arg) = parser.parse_args()
    return opt


def main():
    """ The main runner function
    """
    option = get_options()

    if option.debug:
        try:
            modbus_log.setLevel(logging.DEBUG)
            logging.basicConfig()
        except Exception as e:
            print("Logging is not supported on this system")

    framer = lookup = {
        'tcp':    ModbusSocketFramer,
        'rtu':    ModbusRtuFramer,
        'binary': ModbusBinaryFramer,
        'ascii':  ModbusAsciiFramer,
    }.get(option.framer, ModbusSocketFramer)(None)

    generate_messages(framer, option)


if __name__ == "__main__":
    main()
