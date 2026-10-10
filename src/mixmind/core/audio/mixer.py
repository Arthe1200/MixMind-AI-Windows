"""Pure, deterministic mixer helpers used by the real-time audio layer."""
from __future__ import annotations
import math

def clamp(value: float, low: float, high: float) -> float:
    """Clamp a numeric value to an inclusive range."""
    if low > high:
        raise ValueError("low must be less than or equal to high")
    return max(low, min(high, value))

def equal_power_crossfade(position: float) -> tuple[float, float]:
    """Return equal-power (A, B) gains for a crossfader position from 0 to 1."""
    position = clamp(position, 0.0, 1.0)
    angle = position * math.pi / 2
    return math.cos(angle), math.sin(angle)

def channel_gain(gain_percent: float, master_percent: float = 100.0) -> float:
    """Convert channel and master percentages to a linear amplitude multiplier."""
    gain = clamp(gain_percent, 0.0, 100.0) / 100.0
    master = clamp(master_percent, 0.0, 100.0) / 100.0
    return gain * master

def crossfader_output_levels(position: float, gain_a_percent: float = 100.0,
                             gain_b_percent: float = 100.0,
                             master_percent: float = 100.0) -> tuple[float, float]:
    """Calculate final linear gains for decks A and B after crossfade and master."""
    a, b = equal_power_crossfade(position)
    master = clamp(master_percent, 0.0, 100.0) / 100.0
    return a * channel_gain(gain_a_percent) * master, b * channel_gain(gain_b_percent) * master
