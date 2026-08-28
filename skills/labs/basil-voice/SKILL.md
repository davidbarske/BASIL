# BASIL Voice Capability v0.1

**Status:** BUILT - runtime validation pending  
**Owner:** BASIL

## Objective
Provide BASIL with an actual reusable local speech capability. The Fawlty reference corpus is downstream evidence and a later confirmation benchmark, not the production voice identity.

## Runtime architecture
1. Qwen3-TTS 1.7B VoiceDesign creates one original BASIL reference from `voice_spec.json` and `seed_text.txt`.
2. The generated BASIL reference and exact transcript become the stable local identity anchor.
3. Qwen3-TTS 0.6B Base builds a reusable clone prompt from that generated original reference and synthesises arbitrary BASIL text.
4. `basil_voice.py serve` exposes `POST /speak` on `127.0.0.1:8765` and returns WAV audio.
5. Only after the capability works operationally is the separate reference corpus used for performance confirmation/tuning.

## Identity constraint
The production voice must remain a distinct fictional identity and must not imitate or clone any real identifiable person. External references may inform broad performance mechanics such as cadence, precision, irritation, escalation and recovery.

## Commands
`RUN_SETUP.cmd` -> `RUN_DESIGN_VOICE.cmd` -> `RUN_SPEAK_TEST.cmd` -> `START_LOCAL_API.cmd`

Direct Python path after dependencies are installed:

```text
python basil_voice.py doctor
python basil_voice.py design
python basil_voice.py speak "Text to speak."
python basil_voice.py serve
```

## Outputs
- `voice/basil_reference.wav`
- `voice/basil_voice_lock.json`
- `output/*.wav`
- local HTTP `POST /speak`

## Validation gate
Do not call this TESTED or DEPLOYED until setup, voice design, arbitrary speech and local API playback have succeeded on the target Windows machine. Final reference-corpus comparison is a confirmation step, not a build prerequisite.
