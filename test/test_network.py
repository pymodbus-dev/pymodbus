"""Test transport."""
import asyncio

import pytest

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.logging import Log
from pymodbus.transport import NULLMODEM_HOST, ModbusProtocolStub


class TestNetwork:
    """Test network problems."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port."""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]

    async def test_stub(self, use_port, use_cls):
        """Test double packet on network."""
        Log.debug("test_double_packet {}", use_port)
        client = AsyncModbusTcpClient(NULLMODEM_HOST, port=use_port)
        stub = ModbusProtocolStub(use_cls, True)
        assert await stub.start_run()
        assert await client.connect()
        test_data = b"Data got echoed."
        client.transport.write(test_data)
        client.transport_close()
        stub.transport_close()

    async def test_double_packet(self, use_port, use_cls):
        """Test double packet on network."""
        old_data = b''
        client = AsyncModbusTcpClient(NULLMODEM_HOST, port=use_port, retries=0)

        def local_handle_data(data: bytes) -> bytes | None:
            """Handle server side for this test case."""
            nonlocal old_data

            addr = int(data[9])
            response = data[0:5] + b'\x05\x00\x03\x02\x00' + (addr*10).to_bytes()

            # 1, 4, 8 return correct data
            # 2, 5 return NO data
            # 3 return 2 + 3
            # 6 return 5 + half 6
            # 7 return second half 6 + 7
            if addr in (2, 0):
                old_data = response
                response = None
            elif addr == 3:
                response = old_data + response
            #elif addr == 6:
            #    response = old_data
            #elif addr == 7:
            #    response = old_data
            return response

        async def local_call(addr: int) -> bool:
            """Call read_holding_register and control."""
            nonlocal client
            reply = await client.read_holding_registers(address=addr, count=1)
            assert not reply.isError(), f"addr {addr} isError"
            assert reply.registers[0] == addr * 10, f"addr {addr} value"

        stub = ModbusProtocolStub(use_cls, True, handler=local_handle_data)
        stub.stub_handle_data = local_handle_data
        await stub.start_run()

        assert await client.connect()
        await asyncio.gather(*[local_call(x) for x in range(1, 4)])
        client.transport_close()
        stub.transport_close()
