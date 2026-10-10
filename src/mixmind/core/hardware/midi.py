"""Serializable MIDI mapping profiles and a testable mapping dispatcher."""
from __future__ import annotations
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

@dataclass(frozen=True)
class MidiMessage:
    """Normalized MIDI control message."""
    message_type: str
    channel: int
    control: int
    value: int

    def __post_init__(self) -> None:
        if self.message_type not in {"note_on", "note_off", "control_change"}:
            raise ValueError("Unsupported MIDI message type")
        if not 0 <= self.channel <= 15:
            raise ValueError("MIDI channel must be between 0 and 15")
        if not 0 <= self.control <= 127 or not 0 <= self.value <= 127:
            raise ValueError("MIDI control and value must be between 0 and 127")

@dataclass(frozen=True)
class MidiBinding:
    """Map one MIDI message identity to an application action."""
    message_type: str
    channel: int
    control: int
    action: str
    description: str = ""

    def matches(self, message: MidiMessage) -> bool:
        return (self.message_type == message.message_type and
                self.channel == message.channel and self.control == message.control)

@dataclass
class MidiProfile:
    """Named, portable controller mapping profile."""
    name: str
    manufacturer: str = "Custom"
    model: str = "Unspecified"
    bindings: list[MidiBinding] = field(default_factory=list)

    def bind(self, binding: MidiBinding) -> None:
        """Add or replace a binding for the same MIDI message identity."""
        self.bindings = [item for item in self.bindings if
                         (item.message_type, item.channel, item.control) !=
                         (binding.message_type, binding.channel, binding.control)]
        self.bindings.append(binding)

    def resolve(self, message: MidiMessage) -> MidiBinding | None:
        """Return the first binding matching a normalized MIDI message."""
        return next((item for item in self.bindings if item.matches(message)), None)

    def save(self, path: str | Path) -> None:
        """Save this profile as readable JSON."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "MidiProfile":
        """Load a profile saved by save()."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        payload["bindings"] = [MidiBinding(**item) for item in payload.get("bindings", [])]
        return cls(**payload)

class MidiMappingDispatcher:
    """Dispatch mapped MIDI messages to registered application callbacks."""
    def __init__(self, profile: MidiProfile) -> None:
        self.profile = profile
        self._actions: dict[str, Callable[[MidiMessage], None]] = {}

    def register(self, action: str, callback: Callable[[MidiMessage], None]) -> None:
        if not action.strip():
            raise ValueError("Action name cannot be empty")
        self._actions[action] = callback

    def dispatch(self, message: MidiMessage) -> bool:
        """Run the mapped action; return False when no action is mapped/registered."""
        binding = self.profile.resolve(message)
        if binding is None or binding.action not in self._actions:
            return False
        self._actions[binding.action](message)
        return True
