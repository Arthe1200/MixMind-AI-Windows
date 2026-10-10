# MixMind AI architecture and delivery contract

MixMind is a native Windows desktop project built with Python and PySide6. This document distinguishes implemented foundations from planned integrations.

## Runtime layers
- Desktop UI: PySide6 widgets, settings, library and controls. Expensive analysis and blocking network work must not run on the audio thread.
- Audio domain: deterministic DSP helpers and, as a separate integration step, a dedicated low-latency audio engine. The mixer module calculates equal-power deck/master gains; it is not itself a sample-buffer mixing engine.
- Library: local file scanning and metadata.
- Analysis: optional offline BPM estimation and waveform-envelope extraction. Estimates remain editable.
- Hardware: serializable MIDI bindings and callback dispatch. Device enumeration, controller-specific behavior and audio routing still require integration and hardware tests.
- AI: provider abstraction. AI/network tasks must never block audio callbacks.
- Integrations: service-specific OAuth/API clients only where terms and technical APIs permit.

## Design requirements
1. Audio processing is local and independent of remote APIs.
2. Never claim hardware or streaming service support until integration and tests confirm it.
3. Streaming OAuth, library metadata access and playable audio are separate capabilities.
4. Credentials belong in a protected OS credential store, not source code or public logs.
5. Analysis runs in a worker; BPM/key estimates are editable suggestions.
6. Hardware profiles are portable JSON and reject malformed MIDI values.
7. Failed analysis or unavailable devices must not crash the library UI.

## Delivery gates
- Unit tests and lint pass.
- Manual Windows smoke tests for install, startup, decoding, simultaneous playback, device changes and shutdown.
- Latency/glitch tests on physical audio hardware.
- Each controller profile tested on its actual model.
- Each streaming integration reviewed against current provider terms and playback restrictions.
- Packaging and clean-machine install verified before a release is called complete.

## Product target
The full target includes two/four decks, waveforms, cue/loop/sample pads, EQ/effects DSP, recording, MIDI learn and controller profiles, audio routing, track analysis, transition suggestions, optional AI stems, and authorized music integrations. These features are not all implemented yet; report each as complete only after its delivery gate passes.
