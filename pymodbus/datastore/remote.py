"""Remote datastore."""
from pymodbus.exceptions import NotImplementedException
from pymodbus.pdu import ExceptionResponse

from .context import ModbusBaseDeviceContext


# ---------------------------------------------------------------------------#
#  Context
# ---------------------------------------------------------------------------#
class RemoteDeviceContext(ModbusBaseDeviceContext):
    """TODO.

    This creates a modbus data model that connects to
    a remote device (depending on the client used)
    """

    def __init__(self, client, device_id=None):
        """Initialize the datastores.

        :param client: The client to retrieve values with
        :param device_id: Unit ID of the remote device
        """
        self._client = client
        self.device_id = device_id
        self.result = None
        self.__build_mapping()

    def reset(self):
        """Reset all the datastores to their default values."""
        raise NotImplementedException()

    def getValues(self, func_code, address, count=1):
        """Get values from remote device."""
        if func_code in self._write_fc:
            return [0]
        group_fx = self.decode(func_code)
        func_fc = self.__get_callbacks[group_fx]
        self.result = func_fc(address, count)
        return self.__extract_result(self.decode(func_code), self.result)

    def setValues(self, func_code, address, values):
        """Set the datastore with the supplied values."""
        group_fx = self.decode(func_code)
        if func_code not in self._write_fc:
            raise ValueError(f"setValues() called with an non-write function code {func_code}")
        func_fc = self.__set_callbacks[f"{group_fx}{func_code}"]
        if func_code in {0x0F, 0x10}:  # Write Multiple Coils, Write Multiple Registers
            self.result = func_fc(address, values)
        else:
            self.result = func_fc(address, values[0])
        # if self.result.isError():
        #    return self.result

    def __str__(self):
        """Return a string representation of the context.

        :returns: A string representation of the context
        """
        return f"Remote Device Context({self._client})"

    def __build_mapping(self):
        """Build the function code mapper."""
        params = {}
        if self.device_id:
            params["device_id"] = self.device_id
        self.__get_callbacks = {
            "d": lambda a, c: self._client.read_discrete_inputs(
                a, count=c, **params
            ),
            "c": lambda a, c: self._client.read_coils(
                a, count=c, **params
            ),
            "h": lambda a, c: self._client.read_holding_registers(
                a, count=c, **params
            ),
            "i": lambda a, c: self._client.read_input_registers(
                a, count=c, **params
            ),
            "x": lambda a, c: ExceptionResponse(0
            ),
        }
        self.__set_callbacks = {
            "d5": lambda a, v: self._client.write_coil(
                a, v, **params
            ),
            "d15": lambda a, v: self._client.write_coils(
                a, v, **params
            ),
            "c5": lambda a, v: self._client.write_coil(
                a, v, **params
            ),
            "c15": lambda a, v: self._client.write_coils(
                a, v, **params
            ),
            "h6": lambda a, v: self._client.write_register(
                a, v, **params
            ),
            "h16": lambda a, v: self._client.write_registers(
                a, v, **params
            ),
            "i6": lambda a, v: self._client.write_register(
                a, v, **params
            ),
            "i16": lambda a, v: self._client.write_registers(
                a, v, **params
            ),
        }
        self._write_fc = (0x05, 0x06, 0x0F, 0x10)

    def __extract_result(self, func_code, result):
        """Extract the values out of a response.

        TODO make this consistent (values?)
        """
        if result.isError():
            return None
        if func_code in {"d", "c"}:
            return result.bits
        if func_code in {"h", "i"}:
            return result.registers
        return result
