"""Test server working as slave on a multidrop RS485 line."""
from unittest import mock

import pytest

from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.server.async_io import ServerDecoder


@pytest.fixture
def framer():
    return ModbusRtuFramer(ServerDecoder())


@pytest.fixture
def callback() -> mock.Mock:
    return mock.Mock()


expected_unit = [2]
good_frame = b"\x02\x03\x00\x01\x00}\xd4\x18"


def test_complete_frame(framer, callback):
    serial_event = good_frame
    framer.processIncomingPacket(serial_event, callback, expected_unit)
    callback.assert_called_once()


def test_complete_frame_bad_crc(framer, callback):
    serial_event = b"\x02\x03\x00\x01\x00}\xd4\x19"  # Manually mangled crc
    framer.processIncomingPacket(serial_event, callback, expected_unit)
    callback.assert_not_called()


def test_complete_frame_wrong_unit(framer, callback):
    serial_event = (
        b"\x01\x03\x00\x01\x00}\xd4+"  # Frame with good CRC but other unit id
    )
    framer.processIncomingPacket(serial_event, callback, expected_unit)
    callback.assert_not_called()


def test_big_split_response_frame_from_other_unit(framer, callback):
    # This is a single *response* from device id 1 after being queried for 125 holding register values
    # Because the response is so long it spans several serial events
    serial_events = [
        b"\x01\x03\xfa\xc4y\xc0\x00\xc4y\xc0\x00\xc4y\xc0\x00\xc4y\xc0\x00\xc4y\xc0\x00Dz\x00\x00C\x96\x00\x00",
        b"?\x05\x1e\xb8DH\x00\x00D\x96\x00\x00D\xfa\x00\x00DH\x00\x00D\x96\x00\x00D\xfa\x00\x00DH\x00",
        b"\x00D\x96\x00\x00D\xfa\x00\x00B\x96\x00\x00B\xb4\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        b"\x00\x00\x00\x00\x00\x00\x00N,",
    ]
    for serial_event in serial_events:
        framer.processIncomingPacket(serial_event, callback, expected_unit)
    callback.assert_not_called()


def test_split_frame(framer, callback):
    serial_events = [good_frame[:5], good_frame[5:]]
    for serial_event in serial_events:
        framer.processIncomingPacket(serial_event, callback, expected_unit)
    callback.assert_called_once()


def test_complete_frame_trailing_data_without_unit_id(framer, callback):
    garbage = b"\x05\x04\x03"  # Note the garbage doesn't contain our unit id
    serial_event = garbage + good_frame
    framer.processIncomingPacket(serial_event, callback, expected_unit)
    callback.assert_called_once()


def test_complete_frame_trailing_data_with_unit_id(framer, callback):
    garbage = b"\x05\x04\x03\x02\x01\x00"  # Note the garbage does contain our unit id
    serial_event = garbage + good_frame
    framer.processIncomingPacket(serial_event, callback, expected_unit)
    callback.assert_called_once()


def test_split_frame_trailing_data_with_unit_id(framer, callback):
    garbage = b"\x05\x04\x03\x02\x01\x00"
    serial_events = [garbage + good_frame[:5], good_frame[5:]]
    for serial_event in serial_events:
        framer.processIncomingPacket(serial_event, callback, expected_unit)
    callback.assert_called_once()


def test_wrapped_frame(framer, callback):
    garbage = b"\x05\x04\x03\x02\x01\x00"
    serial_event = garbage + good_frame + garbage
    framer.processIncomingPacket(serial_event, callback, expected_unit)

    # We probably should not respond in this case; in this case we've likely become desynchronized
    # i.e. this probably represents a case where a command came for us, but we didn't get
    # to the serial buffer in time (some other co-routine or perhaps a block on the USB bus)
    # and the master moved on and queried another device
    callback.assert_not_called()


def test_frame_with_trailing_data(framer, callback):
    garbage = b"\x05\x04\x03\x02\x01\x00"
    serial_event = good_frame + garbage
    framer.processIncomingPacket(serial_event, callback, expected_unit)

    # We should not respond in this case for identical reasons as test_wrapped_frame
    callback.assert_not_called()
