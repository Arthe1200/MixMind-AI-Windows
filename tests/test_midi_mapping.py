from mixmind.core.hardware.midi import MidiBinding, MidiMappingDispatcher, MidiMessage, MidiProfile

def test_profile_replaces_existing_binding():
    profile = MidiProfile("Custom")
    profile.bind(MidiBinding("note_on", 0, 36, "sample_1"))
    profile.bind(MidiBinding("note_on", 0, 36, "sample_2"))
    assert len(profile.bindings) == 1
    assert profile.resolve(MidiMessage("note_on", 0, 36, 127)).action == "sample_2"

def test_dispatch_calls_registered_action():
    profile = MidiProfile("Custom")
    profile.bind(MidiBinding("control_change", 1, 10, "crossfader"))
    dispatcher = MidiMappingDispatcher(profile)
    seen = []
    dispatcher.register("crossfader", seen.append)
    message = MidiMessage("control_change", 1, 10, 64)
    assert dispatcher.dispatch(message)
    assert seen == [message]

def test_unmapped_message_returns_false():
    dispatcher = MidiMappingDispatcher(MidiProfile("Empty"))
    assert not dispatcher.dispatch(MidiMessage("note_on", 0, 1, 127))

def test_profile_round_trip(tmp_path):
    profile = MidiProfile("Custom", bindings=[
        MidiBinding("note_on", 0, 36, "sample_1", "Launch sample")])
    path = tmp_path / "profile.json"
    profile.save(path)
    assert MidiProfile.load(path) == profile
