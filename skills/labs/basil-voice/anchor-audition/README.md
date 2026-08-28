BASIL BRITISH ANCHOR AUDITION v0.1

OBJECTIVE
Stop open-loop Qwen VoiceDesign guessing. Establish a clearly British male synthetic anchor first.

WHY THIS PASS
The first Qwen BASIL identity and all three refinement candidates were rejected as outside
the target vocal family. The user-supplied longer references confirm a wide, high-register,
high-dynamic performance envelope, but the previous model never heard that evidence.

This pass tests only:
1. British/English accent credibility
2. male age/register family
3. timbre/placement
4. whether the base voice is worth carrying into an expressive engine

It does NOT attempt the final Basil-style panic/exasperation layer yet.

ENGINE
Kokoro 82M, Apache-2.0 weights, British English pipeline ('b').
Official British male voices:
bm_george, bm_fable, bm_lewis, bm_daniel.
Kokoro's official pipeline also supports comma-separated voices, which it averages, so
three synthetic blends are included.

RUN
1. RUN_SETUP.cmd
2. RUN_ANCHOR_AUDITION.cmd
3. Listen to output\01...07 WAVs.
4. Return the best one or two to ChatGPT.

DECISION GATE
If none sound unmistakably British and roughly in the right vocal family, do not keep
tweaking Kokoro. Change anchor engine.

REFERENCE MATERIAL
The user supplied two longer Fawlty/BBC audio references. They are used only to derive
broad acoustic/performance observations and are NOT copied, trained on or used as a
real-person cloning source.
