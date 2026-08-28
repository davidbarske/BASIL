from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

NEUTRAL = (
    "Right. We have established what happened. Now let us stop admiring the paperwork "
    "and do something useful about it."
)
STRESS = (
    "Yes, thank you, that is enormously helpful. Meanwhile the telephone is ringing, "
    "the booking has vanished, and apparently this is now my fault."
)

CANDIDATES = [
    ("01_GEORGE", "bm_george"),
    ("02_FABLE", "bm_fable"),
    ("03_LEWIS", "bm_lewis"),
    ("04_DANIEL", "bm_daniel"),
    ("05_GEORGE_FABLE", "bm_george,bm_fable"),
    ("06_GEORGE_LEWIS", "bm_george,bm_lewis"),
    ("07_FABLE_LEWIS", "bm_fable,bm_lewis"),
]

def join_audio(parts, sr=24000):
    if not parts:
        return np.zeros(1, dtype=np.float32)
    gap = np.zeros(int(sr * 0.22), dtype=np.float32)
    seq = []
    for i, a in enumerate(parts):
        if i:
            seq.append(gap)
        seq.append(np.asarray(a, dtype=np.float32))
    return np.concatenate(seq)

def f0_metrics(y, sr=24000):
    try:
        import librosa
        f0 = librosa.yin(y, fmin=70, fmax=420, sr=sr, frame_length=2048, hop_length=256)
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=256)[0]
        n = min(len(f0), len(rms))
        f0, rms = f0[:n], rms[:n]
        mask = np.isfinite(f0) & (rms > np.percentile(rms, 40))
        v = f0[mask]
        if len(v):
            return {
                "median_hz": round(float(np.median(v)), 1),
                "p10_hz": round(float(np.percentile(v, 10)), 1),
                "p90_hz": round(float(np.percentile(v, 90)), 1),
            }
    except Exception:
        pass
    return {}

def doctor():
    from kokoro import KPipeline
    print("kokoro import: OK")
    p = KPipeline(lang_code="b")
    print("British pipeline: OK")
    pack = p.load_voice("bm_george")
    print("bm_george voice pack: OK", tuple(pack.shape))
    print("Doctor: PASS")
    return 0

def generate():
    from kokoro import KPipeline
    print("Loading British English pipeline...")
    pipeline = KPipeline(lang_code="b")
    report = {
        "status": "GENERATED_NOT_SELECTED",
        "reference_context": {
            "best_of_basil_derived_pitch": {
                "median_hz": 261.0, "p10_hz": 120.3, "p90_hz": 388.4,
                "note": "Derived from user-supplied long reference; compilation contains other speakers/contexts, so use as a broad envelope only."
            },
            "bbc_audiobook_extract_derived_pitch": {
                "median_hz": 218.6, "p10_hz": 122.5, "p90_hz": 325.1,
                "note": "Derived from user-supplied extract; mixed programme material, so use as a broad envelope only."
            }
        },
        "candidates": []
    }

    for label, voice in CANDIDATES:
        print(f"Generating {label} ({voice})...")
        sections = []
        for text in (NEUTRAL, STRESS):
            parts = []
            for result in pipeline(text, voice=voice, speed=1.05, split_pattern=r"\n+"):
                if result.audio is not None:
                    parts.append(result.audio.detach().cpu().numpy())
            sections.append(join_audio(parts))
        full = join_audio(sections)
        out = OUT / f"{label}.wav"
        sf.write(out, full, 24000)
        m = f0_metrics(full, 24000)
        report["candidates"].append({
            "label": label,
            "voice": voice,
            "file": out.name,
            "metrics": m
        })
        print("  created", out.name, m)

    (OUT / "ANCHOR_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "LISTEN_IN_THIS_ORDER.txt").write_text(
        "BASIL BRITISH ANCHOR AUDITION v0.1\n\n"
        "This pass tests ACCENT + BASE VOCAL FAMILY only. Do not judge final panic/exasperation yet.\n\n"
        "Listen in numeric order and identify any candidate that is clearly in the right English/British ballpark.\n"
        "If two are promising, keep both. If none are promising, stop: we change anchor engine rather than prompt-tweak.\n\n"
        + "\n".join(f"{label}.wav = {voice}" for label, voice in CANDIDATES),
        encoding="utf-8"
    )
    print()
    print("COMPLETE:", OUT)
    return 0

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "generate"
    if cmd == "doctor":
        return doctor()
    if cmd == "generate":
        return generate()
    print("Usage: anchor_audition.py [doctor|generate]")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
