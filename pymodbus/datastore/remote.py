"""Remote datastore."""
# pylint: disable=missing-type-doc
from pymodbus.exceptions import NotImplementedException
from pymodbus.interfaces import IModbusSlaveContext
from pymodbus.logging import Log


# ---------------------------------------------------------------------------#
#  Context
# ---------------------------------------------------------------------------#
class RemoteSlaveContext(IModbusSlaveContext):
    """TODO.

    This creates a modbus data model that connects to
    a remote device (depending on the client used)
    """

    def __init__(self, client, unit=None):
        """Initialize the datastores.

        :param client: The client to retrieve values with
        :param unit: Unit ID of the remote slave
        """
        self._client = client
        self.unit = unit
        self.result = None
        self.__build_mapping()
        if not self.__set_callbacks:
            Log.error("Init went wrong.")

    def reset(self):
        """Reset all the datastores to their default values."""
        raise NotImplementedException()

    def validate(self, fc_as_hex, address, count=1):
        """Validate the request to make sure it is in range.

        :param fc_as_hex: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        """
        Log.debug("validate[{}] {}:{}", fc_as_hex, address, count)
        group_fx = self.decode(fc_as_hex)
        if fc_as_hex in self._write_fc:
            func_fc = self.__set_callbacks[f"{group_fx}{fc_as_hex}"]
        else:
            func_fc = self.__get_callbacks[group_fx]
        self.result = func_fc(address, count)
        return not self.result.isError()

    def getValues(self, fc_as_hex, address, count=1):
        """Get values from real call in validate"""
        if fc_as_hex in self._write_fc:
            return [0]
        return self.__extract_result(self.decode(fc_as_hex), self.result)

    def setValues(self, fc_as_hex, address, values):
        """Set the datastore with the supplied values.

        Already done in validate
        """

    def __str__(self):
        """Return a string representation of the context.

        :returns: A string representation of the context
        """
        return f"Remote Slave Context({self._client})"

    def __build_mapping(self):
        """Build the function code mapper."""
        kwargs = {}
        if self.unit:
            kwargs["slave"] = self.unit
        self.__get_callbacks = {
            "d": lambda a, c: self._client.read_discrete_inputs(  # pylint: disable=unnecessary-lambda
                a, c, **kwargs
            ),
            "c": lambda a, c: self._client.read_coils(  # pylint: disable=unnecessary-lambda
                a, c, **kwargs
            ),
            "h": lambda a, c: self._client.read_holding_registers(  # pylint: disable=unnecessary-lambda
                a, c, **kwargs
            ),
            "i": lambda a, c: self._client.read_input_registers(  # pylint: disable=unnecessary-lambda
                a, c, **kwargs
            ),
        }
        self.__set_callbacks = {
            "d5": lambda a, v: self._client.write_coil(  # pylint: disable=unnecessary-lambda
                a, v, **kwargs
            ),
            "d15": lambda a, v: self._client.write_coils(  # pylint: disable=unnecessary-lambda
                a, v, **kwargs
            ),
            "c5": lambda a, v: self._client.write_coils(  # pylint: disable=unnecessary-lambda
                a, v, **kwargs
            ),
            "c15": lambda a, v: self._client.write_coils(  # pylint: disable=unnecessary-lambda
                a, v, **kwargs
            ),
            "h6": lambda a, v: self._client.write_register(  # pylint: disable=unnecessary-lambda
                a, v, **kwargs
            ),
            "h16": lambda a, v: self._client.write_registers(  # pylint: disable=unnecessary-lambda
                a, v, **kwargs
            ),
            "i6": lambda a, v: self._client.write_register(  # pylint: disable=unnecessary-lambda
                a, v, **kwargs
            ),
            "i16": lambda a, v: self._client.write_registers(  # pylint: disable=unnecessary-lambda
                a, v, **kwargs
            ),
        }
        self._write_fc = (0x05, 0x06, 0x15, 0x16, 0x17)

    def __extract_result(self, fc_as_hex, result):
        """Extract the values out of a response.

        TODO make this consistent (values?)
        """
        if not result.isError():
            if fc_as_hex in {"d", "c"}:
                return result.bits
            if fc_as_hex in {"h", "i"}:
                return result.registers
        else:
            return result
        return None
