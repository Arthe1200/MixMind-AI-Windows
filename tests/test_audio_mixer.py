import math
import pytest
from mixmind.core.audio.mixer import channel_gain, crossfader_output_levels, equal_power_crossfade

def test_equal_power_crossfade_endpoints():
    assert equal_power_crossfade(0) == pytest.approx((1.0, 0.0))
    assert equal_power_crossfade(1) == pytest.approx((0.0, 1.0))

def test_equal_power_crossfade_center():
    assert equal_power_crossfade(0.5) == pytest.approx((math.sqrt(0.5), math.sqrt(0.5)))

def test_crossfader_clamps_out_of_range_values():
    assert equal_power_crossfade(-2) == pytest.approx((1.0, 0.0))
    assert equal_power_crossfade(2) == pytest.approx((0.0, 1.0))

def test_channel_and_master_gain_are_combined():
    assert channel_gain(50, 80) == pytest.approx(0.4)
    assert crossfader_output_levels(0.0, 80, 50, 50) == pytest.approx((0.4, 0.0))

def test_invalid_clamp_range_is_rejected():
    from mixmind.core.audio.mixer import clamp
    with pytest.raises(ValueError):
        clamp(1, 2, 0)
