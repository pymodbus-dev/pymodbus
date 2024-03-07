"""Remote datastore."""
from pymodbus.datastore import ModbusBaseSlaveContext
from pymodbus.exceptions import NotImplementedException
from pymodbus.logging import Log


# ---------------------------------------------------------------------------#
#  Context
# ---------------------------------------------------------------------------#
class RemoteSlaveContext(ModbusBaseSlaveContext):
    """TODO.

    This creates a modbus data model that connects to
    a remote device (depending on the client used)
    """

    def __init__(self, client, slave=None):
        """Initialize the datastores.

        :param client: The client to retrieve values with
        :param slave: Unit ID of the remote slave
        """
        self._client = client
        self.slave = slave
        self.result = None
        self.__build_mapping()
        if not self.__set_callbacks:
            Log.error("Init went wrong.")

    def reset(self):
        """Reset all the datastores to their default values."""
        raise NotImplementedException()

    def validate(self, _fc_as_hex, _address, _count):
        """Validate the request to make sure it is in range.

        :returns: True
        """
        return True

    def getValues(self, fc_as_hex, _address, _count=1):
        """Get values from real call in validate."""
        if fc_as_hex in self._write_fc:
            return [0]
        group_fx = self.decode(fc_as_hex)
        func_fc = self.__get_callbacks[group_fx]
        self.result = func_fc(_address, _count)
        return self.__extract_result(self.decode(fc_as_hex), self.result)

    def setValues(self, fc_as_hex, address, values):
        """Set the datastore with the supplied values."""
        group_fx = self.decode(fc_as_hex)
        if fc_as_hex not in self._write_fc:
            raise ValueError(f"setValues() called with an non-write function code {fc_as_hex}")
        func_fc = self.__set_callbacks[f"{group_fx}{fc_as_hex}"]
        if fc_as_hex in {0x0F, 0x10}:  # Write Multiple Coils, Write Multiple Registers
            self.result = func_fc(address, values)
        else:
            self.result = func_fc(address, values[0])
        if self.result.isError():
            return self.result
        return None

    def __str__(self):
        """Return a string representation of the context.

        :returns: A string representation of the context
        """
        return f"Remote Slave Context({self._client})"

    def __build_mapping(self):
        """Build the function code mapper."""
        kwargs = {}
        if self.slave:
            kwargs["slave"] = self.slave
        self.__get_callbacks = {
            "d": lambda a, c: self._client.read_discrete_inputs(
                a, c, **kwargs
            ),
            "c": lambda a, c: self._client.read_coils(
                a, c, **kwargs
            ),
            "h": lambda a, c: self._client.read_holding_registers(
                a, c, **kwargs
            ),
            "i": lambda a, c: self._client.read_input_registers(
                a, c, **kwargs
            ),
        }
        self.__set_callbacks = {
            "d5": lambda a, v: self._client.write_coil(
                a, v, **kwargs
            ),
            "d15": lambda a, v: self._client.write_coils(
                a, v, **kwargs
            ),
            "c5": lambda a, v: self._client.write_coil(
                a, v, **kwargs
            ),
            "c15": lambda a, v: self._client.write_coils(
                a, v, **kwargs
            ),
            "h6": lambda a, v: self._client.write_register(
                a, v, **kwargs
            ),
            "h16": lambda a, v: self._client.write_registers(
                a, v, **kwargs
            ),
            "i6": lambda a, v: self._client.write_register(
                a, v, **kwargs
            ),
            "i16": lambda a, v: self._client.write_registers(
                a, v, **kwargs
            ),
        }
        self._write_fc = (0x05, 0x06, 0x0F, 0x10)

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
