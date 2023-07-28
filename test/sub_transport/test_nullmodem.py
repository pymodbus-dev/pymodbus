"""Test transport."""
import asyncio

import pytest

from pymodbus.transport import NullModem


class TestNullModem:
    """Test null modem module."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port"""
        base_ports[__class__.__name__] += 2
        return base_ports[__class__.__name__]

    def test_init(self, dummy_protocol):
        """Test initialize."""
        prot = dummy_protocol()
        NullModem(prot)
        prot.connection_made.assert_not_called()
        prot.connection_lost.assert_not_called()

    def test_close(self, dummy_protocol):
        """Test initialize."""
        prot = dummy_protocol()
        modem = NullModem(prot)
        modem.close()
        prot.connection_made.assert_not_called()
        prot.connection_lost.assert_called_once()
        modem.close()  # test _is_closing works.

    def test_listen(self, dummy_protocol, use_port):
        """Test listener (shared list)"""
        protocol = dummy_protocol(is_server=True)
        listen = NullModem.set_listener(use_port, protocol)
        assert NullModem.listeners[use_port] == protocol
        assert len(NullModem.listeners) == 1
        assert not NullModem.connections
        listen.close()
        assert not NullModem.listeners
        protocol.connection_made.assert_not_called()
        protocol.connection_lost.assert_not_called()

    def test_listen_twice(self, dummy_protocol, use_port):
        """Test exception when listening twice."""
        listen1 = NullModem.set_listener(use_port, dummy_protocol(is_server=True))
        with pytest.raises(AssertionError):
            NullModem.set_listener(use_port, dummy_protocol(is_server=True))
        listen1.close()
        listen2 = NullModem.set_listener(use_port, dummy_protocol(is_server=True))
        assert len(NullModem.listeners) == 1
        listen2.close()

    def test_listen_triangle(self, dummy_protocol, use_port):
        """Test listener (shared list)"""
        use_port2 = use_port + 1
        listen1 = NullModem.set_listener(use_port, dummy_protocol(is_server=True))
        listen2 = NullModem.set_listener(use_port2, dummy_protocol(is_server=True))
        listen1.close()
        assert use_port not in NullModem.listeners
        assert len(NullModem.listeners) == 1
        listen2.close()
        assert not NullModem.listeners

    def test_connect(self, dummy_protocol, use_port):
        """Test connect."""
        prot_listen = dummy_protocol(is_server=True)
        listen = NullModem.set_listener(use_port, prot_listen)
        prot1 = dummy_protocol()
        modem, _ = NullModem.set_connection(use_port, prot1)
        modem_b = modem.other_modem
        assert modem.protocol != listen.protocol
        assert modem.protocol != modem_b.protocol
        assert len(NullModem.connections) == 2
        assert NullModem.connections[modem] == use_port
        assert NullModem.connections[modem_b] == -use_port
        modem.close()
        assert modem_b not in NullModem.connections
        listen.close()
        prot_listen.connection_made.assert_not_called()
        prot_listen.connection_lost.assert_not_called()
        prot1.connection_made.assert_called_once()
        prot1.connection_lost.assert_called_once()
        modem_b.protocol.connection_made.assert_called_once()
        modem_b.protocol.connection_lost.assert_called_once()

    def test_connect_no_listen(self, dummy_protocol, use_port):
        """Test connect without listen"""
        with pytest.raises(asyncio.TimeoutError):
            NullModem.set_connection(use_port, dummy_protocol())

    def test_listen_close(self, dummy_protocol, use_port):
        """Test connect without listen"""
        listen = NullModem.set_listener(use_port, dummy_protocol(is_server=True))
        modem, _ = NullModem.set_connection(use_port, dummy_protocol())
        listen.close()
        assert len(NullModem.connections) == 2
        assert not NullModem.listeners
        modem.close()

    def test_connect_multiple(self, dummy_protocol, use_port):
        """Test multiple connect."""
        listen1 = NullModem.set_listener(use_port, dummy_protocol(is_server=True))
        modem1, _ = NullModem.set_connection(use_port, dummy_protocol())
        modem1b = modem1.other_modem
        modem2, _ = NullModem.set_connection(use_port, dummy_protocol())
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

    def test_is_dirty(self, dummy_protocol, use_port):
        """Test connect."""
        assert not NullModem.is_dirty()
        listen = NullModem.set_listener(use_port, dummy_protocol(is_server=True))
        modem, _ = NullModem.set_connection(use_port, dummy_protocol())
        assert NullModem.is_dirty()
        modem.close()
        listen.close()
        assert not NullModem.is_dirty()

    def test_single_flow(self, dummy_protocol, use_port):
        """Test single flow."""
        listen = NullModem.set_listener(use_port, dummy_protocol(is_server=True))
        modem, _ = NullModem.set_connection(use_port, dummy_protocol())
        modem_b = modem.other_modem
        test_data1 = b"abcd"
        test_data2 = b"efgh"
        modem.sendto(test_data1)
        modem_b.write(test_data2)
        assert modem_b.protocol.data == test_data1
        assert modem.protocol.data == test_data2
        modem.close()
        listen.close()

    def test_triangle_flow(self, dummy_protocol, use_port):
        """Test triangle flow."""
        listen = NullModem.set_listener(use_port, dummy_protocol(is_server=True))
        modem1, _ = NullModem.set_connection(use_port, dummy_protocol())
        modem1b = modem1.other_modem
        modem2, _ = NullModem.set_connection(use_port, dummy_protocol())
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
        listen.close()

    @pytest.mark.parametrize(
        "add_text",
        [
            [b""],
            [b"MANIPULATED"],
            [b"MANIPULATED", b"and more"],
            [b"MANIPULATED", b"and", b"much more"],
        ],
    )
    def test_manipulator(self, add_text, dummy_protocol, use_port):
        """Test manipulator."""

        def manipulator(data):
            """Test manipulator"""
            data = [data]
            data.extend(add_text)
            return data

        listen = NullModem.set_listener(use_port, dummy_protocol(is_server=True))
        modem, _ = NullModem.set_connection(use_port, dummy_protocol())
        modem_b = modem.other_modem
        modem.set_manipulator(manipulator)
        data1 = b"abcd"
        data2 = b"efgh"
        modem.write(data1)
        modem.write(data2)
        modem_b.write(data1)
        modem_b.write(data2)
        x = b"".join(part for part in add_text)
        assert modem.protocol.data == data1 + data2
        assert modem_b.protocol.data == data1 + x + data2 + x
        modem.close()
        listen.close()

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
