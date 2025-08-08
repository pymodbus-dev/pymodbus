"""Property-based tests for Modbus payload round-trip encoding/decoding with randomized word order."""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pymodbus.client.mixin import ModbusClientMixin as mixin


word_order_strategy = st.one_of(st.just("big"), st.just("little"))

@given(value=st.integers(min_value=-(2**15), max_value=2**15 - 1), word_order=word_order_strategy)
def test_round_trip_int16(value, word_order):
    """Test round-trip int16 encoding/decoding with randomized Modbus word order."""
    regs = mixin.convert_to_registers(value, word_order=word_order, data_type=mixin.DATATYPE.INT16)
    result = mixin.convert_from_registers(regs, word_order=word_order, data_type=mixin.DATATYPE.INT16)
    assert result == value

@given(value=st.integers(min_value=0, max_value=2**16 - 1), word_order=word_order_strategy)
def test_round_trip_uint16(value, word_order):
    """Test round-trip uint16 encoding/decoding with randomized Modbus word order."""
    regs = mixin.convert_to_registers(value, word_order=word_order, data_type=mixin.DATATYPE.UINT16)
    result = mixin.convert_from_registers(regs, word_order=word_order, data_type=mixin.DATATYPE.UINT16)
    assert result == value

@given(value=st.integers(min_value=-(2**31), max_value=2**31 - 1), word_order=word_order_strategy)
def test_round_trip_int32(value, word_order):
    """Test round-trip int32 encoding/decoding with randomized Modbus word order."""
    regs = mixin.convert_to_registers(value, word_order=word_order, data_type=mixin.DATATYPE.INT32)
    result = mixin.convert_from_registers(regs, word_order=word_order, data_type=mixin.DATATYPE.INT32)
    assert result == value

@given(value=st.floats(allow_nan=False, allow_infinity=False, width=64), word_order=word_order_strategy)
@settings(deadline=None)
def test_round_trip_float64(value, word_order):
    """Test round-trip float64 encoding/decoding with randomized Modbus word order."""
    regs = mixin.convert_to_registers(value, word_order=word_order, data_type=mixin.DATATYPE.FLOAT64)
    result = mixin.convert_from_registers(regs, word_order=word_order, data_type=mixin.DATATYPE.FLOAT64)
    assert result == pytest.approx(value, rel=1e-12)
