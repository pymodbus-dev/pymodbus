"""Modbus Device Controller.

These are the device management handlers.  They should be
maintained in the server context and the various methods
should be inserted in the correct locations.
"""
import struct

# pylint: disable=missing-type-doc
from collections import OrderedDict

from pymodbus.constants import DeviceInformation
from pymodbus.interfaces import Singleton
from pymodbus.utilities import dict_property


# ---------------------------------------------------------------------------#
#  Modbus Plus Statistics
# ---------------------------------------------------------------------------#
class ModbusPlusStatistics:
    """This is used to maintain the current modbus plus statistics count.

    As of right now this is simply a stub to complete the modbus implementation.
    For more information, see the modbus implementation guide page 87.
    """

    __data = OrderedDict(
        {
            "node_type_id": [0x00] * 2,  # 00
            "software_version_number": [0x00] * 2,  # 01
            "network_address": [0x00] * 2,  # 02
            "mac_state_variable": [0x00] * 2,  # 03
            "peer_status_code": [0x00] * 2,  # 04
            "token_pass_counter": [0x00] * 2,  # 05
            "token_rotation_time": [0x00] * 2,  # 06
            "program_master_token_failed": [0x00],  # 07 hi
            "data_master_token_failed": [0x00],  # 07 lo
            "program_master_token_owner": [0x00],  # 08 hi
            "data_master_token_owner": [0x00],  # 08 lo
            "program_slave_token_owner": [0x00],  # 09 hi
            "data_slave_token_owner": [0x00],  # 09 lo
            "data_slave_command_transfer": [0x00],  # 10 hi
            "__unused_10_lowbit": [0x00],  # 10 lo
            "program_slave_command_transfer": [0x00],  # 11 hi
            "program_master_rsp_transfer": [0x00],  # 11 lo
            "program_slave_auto_logout": [0x00],  # 12 hi
            "program_master_connect_status": [0x00],  # 12 lo
            "receive_buffer_dma_overrun": [0x00],  # 13 hi
            "pretransmit_deferral_error": [0x00],  # 13 lo
            "frame_size_error": [0x00],  # 14 hi
            "repeated_command_received": [0x00],  # 14 lo
            "receiver_alignment_error": [0x00],  # 15 hi
            "receiver_collision_abort_error": [0x00],  # 15 lo
            "bad_packet_length_error": [0x00],  # 16 hi
            "receiver_crc_error": [0x00],  # 16 lo
            "transmit_buffer_dma_underrun": [0x00],  # 17 hi
            "bad_link_address_error": [0x00],  # 17 lo
            "bad_mac_function_code_error": [0x00],  # 18 hi
            "internal_packet_length_error": [0x00],  # 18 lo
            "communication_failed_error": [0x00],  # 19 hi
            "communication_retries": [0x00],  # 19 lo
            "no_response_error": [0x00],  # 20 hi
            "good_receive_packet": [0x00],  # 20 lo
            "unexpected_path_error": [0x00],  # 21 hi
            "exception_response_error": [0x00],  # 21 lo
            "forgotten_transaction_error": [0x00],  # 22 hi
            "unexpected_response_error": [0x00],  # 22 lo
            "active_station_bit_map": [0x00] * 8,  # 23-26
            "token_station_bit_map": [0x00] * 8,  # 27-30
            "global_data_bit_map": [0x00] * 8,  # 31-34
            "receive_buffer_use_bit_map": [0x00] * 8,  # 35-37
            "data_master_output_path": [0x00] * 8,  # 38-41
            "data_slave_input_path": [0x00] * 8,  # 42-45
            "program_master_outptu_path": [0x00] * 8,  # 46-49
            "program_slave_input_path": [0x00] * 8,  # 50-53
        }
    )

    def __init__(self):
        """Initialize the modbus plus statistics with the default information."""
        self.reset()

    def __iter__(self):
        """Iterate over the statistics.

        :returns: An iterator of the modbus plus statistics
        """
        return iter(self.__data.items())

    def reset(self):
        """Clear all of the modbus plus statistics."""
        for key in self.__data:
            self.__data[key] = [0x00] * len(self.__data[key])

    def summary(self):
        """Return a summary of the modbus plus statistics.

        :returns: 54 16-bit words representing the status
        """
        return iter(self.__data.values())

    def encode(self):
        """Return a summary of the modbus plus statistics.

        :returns: 54 16-bit words representing the status
        """
        total, values = [], sum(self.__data.values(), [])
        for i in range(0, len(values), 2):
            total.append((values[i] << 8) | values[i + 1])
        return total


# ---------------------------------------------------------------------------#
#  Device Information Control
# ---------------------------------------------------------------------------#
class ModbusDeviceIdentification:
    """This is used to supply the device identification.

    For the readDeviceIdentification function

    For more information read section 6.21 of the modbus
    application protocol.
    """

    __data = {
        0x00: "",  # VendorName
        0x01: "",  # ProductCode
        0x02: "",  # MajorMinorRevision
        0x03: "",  # VendorUrl
        0x04: "",  # ProductName
        0x05: "",  # ModelName
        0x06: "",  # UserApplicationName
        0x07: "",  # reserved
        0x08: "",  # reserved
        # 0x80 -> 0xFF are privatek
    }

    __names = [
        "VendorName",
        "ProductCode",
        "MajorMinorRevision",
        "VendorUrl",
        "ProductName",
        "ModelName",
        "UserApplicationName",
    ]

    def __init__(self, info=None, info_name=None):
        """Initialize the datastore with the elements you need.

        (note acceptable range is [0x00-0x06,0x80-0xFF] inclusive)

        :param info: A dictionary of {int:string} of values
        :param set: A dictionary of {name:string} of values
        """
        if isinstance(info_name, dict):
            for key in info_name:
                inx = self.__names.index(key)
                self.__data[inx] = info_name[key]

        if isinstance(info, dict):
            for key in info:
                if (0x06 >= key >= 0x00) or (0xFF >= key >= 0x80):
                    self.__data[key] = info[key]

    def __iter__(self):
        """Iterate over the device information.

        :returns: An iterator of the device information
        """
        return iter(self.__data.items())

    def summary(self):
        """Return a summary of the main items.

        :returns: An dictionary of the main items
        """
        return dict(zip(self.__names, iter(self.__data.values())))

    def update(self, value):
        """Update the values of this identity.

        using another identify as the value

        :param value: The value to copy values from
        """
        self.__data.update(value)

    def __setitem__(self, key, value):
        """Access the device information.

        :param key: The register to set
        :param value: The new value for referenced register
        """
        if key not in [0x07, 0x08]:
            self.__data[key] = value

    def __getitem__(self, key):
        """Access the device information.

        :param key: The register to read
        """
        return self.__data.setdefault(key, "")

    def __str__(self):
        """Build a representation of the device.

        :returns: A string representation of the device
        """
        return "DeviceIdentity"

    # -------------------------------------------------------------------------#
    #  Properties
    # -------------------------------------------------------------------------#
    VendorName = dict_property(
        lambda s: s.__data, 0  # pylint: disable=protected-access
    )
    ProductCode = dict_property(
        lambda s: s.__data, 1  # pylint: disable=protected-access
    )
    MajorMinorRevision = dict_property(
        lambda s: s.__data, 2  # pylint: disable=protected-access
    )
    VendorUrl = dict_property(lambda s: s.__data, 3)  # pylint: disable=protected-access
    ProductName = dict_property(
        lambda s: s.__data, 4  # pylint: disable=protected-access
    )
    ModelName = dict_property(lambda s: s.__data, 5)  # pylint: disable=protected-access
    UserApplicationName = dict_property(
        lambda s: s.__data, 6  # pylint: disable=protected-access
    )


class DeviceInformationFactory(Singleton):  # pylint: disable=too-few-public-methods
    """This is a helper factory.

    That really just hides
    some of the complexity of processing the device information
    requests (function code 0x2b 0x0e).
    """

    __lookup = {
        DeviceInformation.Basic: lambda c, r, i: c.__gets(  # pylint: disable=protected-access
            r, list(range(i, 0x03))
        ),
        DeviceInformation.Regular: lambda c, r, i: c.__gets(  # pylint: disable=protected-access
            r,
            list(range(i, 0x07))
            if c.__get(r, i)[i]  # pylint: disable=protected-access
            else list(range(0, 0x07)),
        ),
        DeviceInformation.Extended: lambda c, r, i: c.__gets(  # pylint: disable=protected-access
            r,
            [x for x in range(i, 0x100) if x not in range(0x07, 0x80)]
            if c.__get(r, i)[i]  # pylint: disable=protected-access
            else [x for x in range(0, 0x100) if x not in range(0x07, 0x80)],
        ),
        DeviceInformation.Specific: lambda c, r, i: c.__get(  # pylint: disable=protected-access
            r, i
        ),
    }

    @classmethod
    def get(cls, control, read_code=DeviceInformation.Basic, object_id=0x00):
        """Get the requested device data from the system.

        :param control: The control block to pull data from
        :param read_code: The read code to process
        :param object_id: The specific object_id to read
        :returns: The requested data (id, length, value)
        """
        identity = control.Identity
        return cls.__lookup[read_code](cls, identity, object_id)

    @classmethod
    def __get(cls, identity, object_id):  # pylint: disable=unused-private-member
        """Read a single object_id from the device information.

        :param identity: The identity block to pull data from
        :param object_id: The specific object id to read
        :returns: The requested data (id, length, value)
        """
        return {object_id: identity[object_id]}

    @classmethod
    def __gets(cls, identity, object_ids):  # pylint: disable=unused-private-member
        """Read multiple object_ids from the device information.

        :param identity: The identity block to pull data from
        :param object_ids: The specific object ids to read
        :returns: The requested data (id, length, value)
        """
        return {oid: identity[oid] for oid in object_ids if identity[oid]}


# ---------------------------------------------------------------------------#
#  Counters Handler
# ---------------------------------------------------------------------------#
class ModbusCountersHandler:
    """This is a helper class to simplify the properties for the counters.

    0x0B  1  Return Bus Message Count

             Quantity of messages that the remote
             device has detected on the communications system since its
             last restart, clear counters operation, or power-up.  Messages
             with bad CRC are not taken into account.

    0x0C  2  Return Bus Communication Error Count

             Quantity of CRC errors encountered by the remote device since its
             last restart, clear counters operation, or power-up.  In case of
             an error detected on the character level, (overrun, parity error),
             or in case of a message length < 3 bytes, the receiving device is
             not able to calculate the CRC. In such cases, this counter is
             also incremented.

    0x0D  3  Return Slave Exception Error Count

             Quantity of MODBUS exception error detected by the remote device
             since its last restart, clear counters operation, or power-up.  It
             comprises also the error detected in broadcast messages even if an
             exception message is not returned in this case.
             Exception errors are described and listed in "MODBUS Application
             Protocol Specification" document.

    0xOE  4  Return Slave Message Count

             Quantity of messages addressed to the remote device,  including
             broadcast messages, that the remote device has processed since its
             last restart, clear counters operation, or power-up.

    0x0F  5  Return Slave No Response Count

             Quantity of messages received by the remote device for which it
             returned no response (neither a normal response nor an exception
             response), since its last restart, clear counters operation, or
             power-up. Then, this counter counts the number of broadcast
             messages it has received.

    0x10  6  Return Slave NAK Count

             Quantity of messages addressed to the remote device for which it
             returned a Negative Acknowledge (NAK) exception response, since
             its last restart, clear counters operation, or power-up. Exception
             responses are described and listed in "MODBUS Application Protocol
             Specification" document.

    0x11  7  Return Slave Busy Count

             Quantity of messages addressed to the remote device for which it
             returned a Slave Device Busy exception response, since its last
             restart, clear counters operation, or power-up. Exception
             responses are described and listed in "MODBUS Application
             Protocol Specification" document.

    0x12  8  Return Bus Character Overrun Count

             Quantity of messages addressed to the remote device that it could
             not handle due to a character overrun condition, since its last
             restart, clear counters operation, or power-up. A character
             overrun is caused by data characters arriving at the port faster
             than they can.

    .. note:: I threw the event counter in here for convenience
    """

    __data = {i: 0x0000 for i in range(9)}
    __names = [
        "BusMessage",
        "BusCommunicationError",
        "SlaveExceptionError",
        "SlaveMessage",
        "SlaveNoResponse",
        "SlaveNAK",
        "SlaveBusy",
        "BusCharacterOverrun",
    ]

    def __iter__(self):
        """Iterate over the device counters.

        :returns: An iterator of the device counters
        """
        return zip(self.__names, iter(self.__data.values()))

    def update(self, values):
        """Update the values of this identity.

        using another identify as the value

        :param values: The value to copy values from
        """
        for k, v_item in iter(values.items()):
            v_item += self.__getattribute__(  # pylint: disable=unnecessary-dunder-call
                k
            )
            self.__setattr__(k, v_item)  # pylint: disable=unnecessary-dunder-call

    def reset(self):
        """Clear all of the system counters."""
        self.__data = {i: 0x0000 for i in range(9)}

    def summary(self):
        """Return a summary of the counters current status.

        :returns: A byte with each bit representing each counter
        """
        count, result = 0x01, 0x00
        for i in iter(self.__data.values()):
            if i != 0x00:  # pylint: disable=compare-to-zero
                result |= count
            count <<= 1
        return result

    # -------------------------------------------------------------------------#
    #  Properties
    # -------------------------------------------------------------------------#
    BusMessage = dict_property(
        lambda s: s.__data, 0  # pylint: disable=protected-access
    )
    BusCommunicationError = dict_property(
        lambda s: s.__data, 1  # pylint: disable=protected-access
    )
    BusExceptionError = dict_property(
        lambda s: s.__data, 2  # pylint: disable=protected-access
    )
    SlaveMessage = dict_property(
        lambda s: s.__data, 3  # pylint: disable=protected-access
    )
    SlaveNoResponse = dict_property(
        lambda s: s.__data, 4  # pylint: disable=protected-access
    )
    SlaveNAK = dict_property(lambda s: s.__data, 5)  # pylint: disable=protected-access
    SlaveBusy = dict_property(lambda s: s.__data, 6)  # pylint: disable=protected-access
    BusCharacterOverrun = dict_property(
        lambda s: s.__data, 7  # pylint: disable=protected-access
    )
    Event = dict_property(lambda s: s.__data, 8)  # pylint: disable=protected-access


# ---------------------------------------------------------------------------#
#  Main server control block
# ---------------------------------------------------------------------------#
class ModbusControlBlock(Singleton):
    """This is a global singleton that controls all system information.

    All activity should be logged here and all diagnostic requests
    should come from here.
    """

    __mode = "ASCII"
    __diagnostic = [False] * 16
    __instance = None
    __listen_only = False
    __delimiter = "\r"
    __counters = ModbusCountersHandler()
    __identity = ModbusDeviceIdentification()
    __plus = ModbusPlusStatistics()
    __events = []

    # -------------------------------------------------------------------------#
    #  Magic
    # -------------------------------------------------------------------------#
    def __str__(self):
        """Build a representation of the control block.

        :returns: A string representation of the control block
        """
        return "ModbusControl"

    def __iter__(self):
        """Iterate over the device counters.

        :returns: An iterator of the device counters
        """
        return self.__counters.__iter__()

    # -------------------------------------------------------------------------#
    #  Events
    # -------------------------------------------------------------------------#
    def addEvent(self, event):  # pylint: disable=invalid-name
        """Add a new event to the event log.

        :param event: A new event to add to the log
        """
        self.__events.insert(0, event)
        self.__events = self.__events[0:64]  # chomp to 64 entries
        self.Counter.Event += 1

    def getEvents(self):  # pylint: disable=invalid-name
        """Return an encoded collection of the event log.

        :returns: The encoded events packet
        """
        events = [event.encode() for event in self.__events]
        return b"".join(events)

    def clearEvents(self):  # pylint: disable=invalid-name
        """Clear the current list of events."""
        self.__events = []

    # -------------------------------------------------------------------------#
    #  Other Properties
    # -------------------------------------------------------------------------#
    Identity = property(lambda s: s.__identity)
    Counter = property(lambda s: s.__counters)
    Events = property(lambda s: s.__events)
    Plus = property(lambda s: s.__plus)

    def reset(self):
        """Clear all of the system counters and the diagnostic register."""
        self.__events = []
        self.__counters.reset()
        self.__diagnostic = [False] * 16

    # -------------------------------------------------------------------------#
    #  Listen Properties
    # -------------------------------------------------------------------------#
    def _setListenOnly(self, value):  # pylint: disable=invalid-name
        """Toggle the listen only status.

        :param value: The value to set the listen status to
        """
        self.__listen_only = bool(value)  # pylint: disable=unused-private-member

    ListenOnly = property(lambda s: s.__listen_only, _setListenOnly)

    # -------------------------------------------------------------------------#
    #  Mode Properties
    # -------------------------------------------------------------------------#
    def _setMode(self, mode):  # pylint: disable=invalid-name
        """Toggle the current serial mode.

        :param mode: The data transfer method in (RTU, ASCII)
        """
        if mode in {"ASCII", "RTU"}:
            self.__mode = mode  # pylint: disable=unused-private-member

    Mode = property(lambda s: s.__mode, _setMode)

    # -------------------------------------------------------------------------#
    #  Delimiter Properties
    # -------------------------------------------------------------------------#
    def _setDelimiter(self, char):  # pylint: disable=invalid-name
        """Change the serial delimiter character.

        :param char: The new serial delimiter character
        """
        if isinstance(char, str):
            self.__delimiter = char.encode()  # pylint: disable=unused-private-member
        if isinstance(char, bytes):
            self.__delimiter = char  # pylint: disable=unused-private-member
        elif isinstance(char, int):
            self.__delimiter = struct.pack(  # pylint: disable=unused-private-member
                ">B", char
            )

    Delimiter = property(lambda s: s.__delimiter, _setDelimiter)

    # -------------------------------------------------------------------------#
    #  Diagnostic Properties
    # -------------------------------------------------------------------------#
    def setDiagnostic(self, mapping):  # pylint: disable=invalid-name
        """Set the value in the diagnostic register.

        :param mapping: Dictionary of key:value pairs to set
        """
        for entry in iter(mapping.items()):
            if entry[0] >= 0 and entry[0] < len(self.__diagnostic):
                self.__diagnostic[entry[0]] = bool(entry[1])

    def getDiagnostic(self, bit):  # pylint: disable=invalid-name
        """Get the value in the diagnostic register.

        :param bit: The bit to get
        :returns: The current value of the requested bit
        """
        try:
            if bit and 0 <= bit < len(self.__diagnostic):
                return self.__diagnostic[bit]
        except Exception:  # pylint: disable=broad-except
            return None
        return None

    def getDiagnosticRegister(self):  # pylint: disable=invalid-name
        """Get the entire diagnostic register.

        :returns: The diagnostic register collection
        """
        return self.__diagnostic


# ---------------------------------------------------------------------------#
#  Exported Identifiers
# ---------------------------------------------------------------------------#
__all__ = [
    "ModbusPlusStatistics",
    "ModbusDeviceIdentification",
    "DeviceInformationFactory",
    "ModbusControlBlock",
]
