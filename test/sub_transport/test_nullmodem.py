"""Test transport."""
import asyncio

import pytest

from pymodbus.transport import NullModem


class TestNullModem:
    """Test null modem module."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_my_port(base_ports):
        """Return next port"""
        base_ports[__class__.__name__] += 2
        return base_ports[__class__.__name__]

    def teardown(self):
        """Run class teardown"""
        assert not NullModem.is_dirty()

    def test_init(self, dummy_protocol):
        """Test initialize."""
        prot = dummy_protocol()
        NullModem(prot)
        prot.connection_made.assert_not_called()
        prot.connection_lost.assert_not_called()
        assert True

    def test_close(self, dummy_protocol):
        """Test initialize."""
        prot = dummy_protocol()
        modem = NullModem(dummy_protocol())
        modem.close()
        prot.connection_made.assert_not_called()
        prot.connection_lost.assert_not_called()
        assert True

    def test_listen(self, dummy_protocol, use_port):
        """Test listener (shared list)"""
        protocol = dummy_protocol(is_server=True)
        listen = NullModem.set_listener(use_port, protocol)
        assert NullModem.listeners[use_port] == protocol
        if len(NullModem.listeners) > 1:
            print("jan igen")
        assert len(NullModem.listeners) == 1
        listen.close()
        assert not NullModem.listeners
        protocol.connection_made.assert_not_called()
        protocol.connection_lost.assert_not_called()

    def test_listen_twice(self, dummy_protocol, use_port):
        """Test exception when listening twice."""
        port1 = use_port
        listen1 = NullModem.set_listener(port1, dummy_protocol(is_server=True))
        with pytest.raises(AssertionError):
            NullModem.set_listener(port1, dummy_protocol(is_server=True))
        listen1.close()
        listen2 = NullModem.set_listener(port1, dummy_protocol(is_server=True))
        assert len(NullModem.listeners) == 1
        listen2.close()

    def test_listen_triangle(self, dummy_protocol, use_port):
        """Test listener (shared list)"""
        port1 = use_port
        port2 = use_port + 1
        listen1 = NullModem.set_listener(port1, dummy_protocol(is_server=True))
        listen2 = NullModem.set_listener(port2, dummy_protocol(is_server=True))
        listen1.close()
        assert port1 not in NullModem.listeners
        assert len(NullModem.listeners) == 1
        listen2.close()
        assert not NullModem.listeners

    def test_connect(self, dummy_protocol, use_port):
        """Test connect."""
        port1 = use_port
        prot_listen = dummy_protocol(is_server=True)
        listen1 = NullModem.set_listener(port1, prot_listen)
        prot1 = dummy_protocol()
        modem1, _ = NullModem.set_connection(port1, prot1)
        modem1b = modem1.other_modem
        assert modem1.protocol != listen1.protocol
        assert modem1.protocol != modem1b.protocol
        assert len(NullModem.connections) == 2
        assert NullModem.connections[modem1] == port1
        assert NullModem.connections[modem1b] == -port1
        modem1.close()
        assert modem1b not in NullModem.connections
        listen1.close()
        prot_listen.connection_made.assert_not_called()
        prot_listen.connection_lost.assert_not_called()
        prot1.connection_made.assert_called_once()
        prot1.connection_lost.assert_called_once()
        modem1b.protocol.connection_made.assert_called_once()
        modem1b.protocol.connection_lost.assert_called_once()

    def test_connect_no_listen(self, dummy_protocol, use_port):
        """Test connect without listen"""
        with pytest.raises(asyncio.TimeoutError):
            NullModem.set_connection(use_port, dummy_protocol())

    def test_connect_multiple(self, dummy_protocol, use_port):
        """Test multiple connect."""
        port1 = use_port
        listen1 = NullModem.set_listener(port1, dummy_protocol(is_server=True))
        modem1, _ = NullModem.set_connection(port1, dummy_protocol())
        modem1b = modem1.other_modem
        modem2, _ = NullModem.set_connection(port1, dummy_protocol())
        modem2b = modem2.other_modem
        protocol_list = [
            modem1.protocol,
            modem1b.protocol,
            modem2.protocol,
            modem2b.protocol,
            listen1.protocol,
        ]
        entries = [modem1, modem1b, modem2, modem2b]
        for inx in range(0, 4):
            test_list = protocol_list.copy()
            del test_list[inx]
            assert entries[inx].protocol not in test_list
        assert len(NullModem.connections) == 4
        listen1.close()
        modem1.close()
        assert len(NullModem.connections) == 2
        assert modem1b not in NullModem.connections
        assert modem2b in NullModem.connections
        modem2.close()

    def test_single_flow(self, dummy_protocol, use_port):
        """Test single flow."""
        port1 = use_port
        listen1 = NullModem.set_listener(port1, dummy_protocol(is_server=True))
        modem1, _ = NullModem.set_connection(port1, dummy_protocol())
        modem1b = modem1.other_modem
        test_data1 = b"abcd"
        test_data2 = b"efgh"
        modem1.sendto(test_data1)
        modem1b.write(test_data2)
        assert modem1b.protocol.data == test_data1
        assert modem1.protocol.data == test_data2
        modem1.close()
        listen1.close()

    def test_triangle_flow(self, dummy_protocol, use_port):
        """Test triangle flow."""
        port1 = use_port
        listen1 = NullModem.set_listener(port1, dummy_protocol(is_server=True))
        modem1, _ = NullModem.set_connection(port1, dummy_protocol())
        modem1b = modem1.other_modem
        modem2, _ = NullModem.set_connection(port1, dummy_protocol())
        modem2b = modem2.other_modem
        test_data1 = b"abcd"
        test_data2 = b"efgh"
        test_data3 = b"ijkl"
        test_data4 = b"mnop"
        modem1.write(test_data1)
        modem1b.write(test_data2)
        assert modem1b.protocol.data == test_data1
        assert modem1.protocol.data == test_data2
        assert modem2b.protocol.data == b""
        assert modem2.protocol.data == b""
        modem2.write(test_data3)
        modem2b.write(test_data4)
        assert modem1b.protocol.data == test_data1
        assert modem1.protocol.data == test_data2
        assert modem2b.protocol.data == test_data3
        assert modem2.protocol.data == test_data4
        modem1.close()
        modem2.close()
        listen1.close()

    def test_manipulator_simple(self, dummy_protocol, use_port):
        """Test manipulator."""
        add_text = b"MANIPULATED"

        def manipulator(data):
            """Test manipulator"""
            return [data + add_text]

        port1 = use_port
        listen1 = NullModem.set_listener(port1, dummy_protocol(is_server=True))
        modem1, _ = NullModem.set_connection(port1, dummy_protocol())
        modem1b = modem1.other_modem
        modem1.set_manipulator(manipulator)
        test_data1 = b"abcd"
        test_data2 = b"efgh"
        modem1.write(test_data1)
        modem1b.write(test_data2)
        assert modem1b.protocol.data == test_data1 + add_text
        assert modem1.protocol.data == test_data2
        modem1.close()
        listen1.close()

    def test_manipulator_adv(self, dummy_protocol, use_port):
        """Test manipulator."""
        add_text = b"MANIPULATED"

        def manipulator(data):
            """Test manipulator"""
            return [data, add_text]

        port1 = use_port
        listen1 = NullModem.set_listener(port1, dummy_protocol(is_server=True))
        modem1, _ = NullModem.set_connection(port1, dummy_protocol())
        modem1b = modem1.other_modem
        modem1.set_manipulator(manipulator)
        test_data1 = b"abcd"
        test_data2 = b"efgh"
        modem1.write(test_data1)
        modem1b.write(test_data2)
        assert modem1b.protocol.data == test_data1 + add_text
        assert modem1.protocol.data == test_data2
        modem1.close()
        listen1.close()

    async def test_serve_forever(self, dummy_protocol):
        """Test external methods."""
        modem = NullModem(dummy_protocol())
        modem.serving.set_result(True)
        await modem.serve_forever()
        modem.close()

    def test_abstract_methods(self, dummy_protocol):
        """Test asyncio abstract methods."""
        modem = NullModem(dummy_protocol())
        modem.abort()
        modem.can_write_eof()
        modem.get_write_buffer_size()
        modem.get_write_buffer_limits()
        modem.set_write_buffer_limits(1024, 1)
        modem.write_eof()
        modem.get_protocol()
        modem.set_protocol(None)
        modem.is_closing()
        modem.is_reading()
        modem.pause_reading()
        modem.resume_reading()
