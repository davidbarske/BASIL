from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOICE_DIR = ROOT / "voice"
OUTPUT_DIR = ROOT / "output"
SPEC_PATH = ROOT / "voice_spec.json"
SEED_PATH = ROOT / "seed_text.txt"
REFERENCE_PATH = VOICE_DIR / "basil_reference.wav"
LOCK_PATH = VOICE_DIR / "basil_voice_lock.json"

VOICE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def read_spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def seed_text() -> str:
    return SEED_PATH.read_text(encoding="utf-8").strip()


def runtime():
    import torch
    from qwen_tts import Qwen3TTSModel
    return torch, Qwen3TTSModel


def device_settings():
    torch, _ = runtime()
    if torch.cuda.is_available():
        return {
            "device_map": "cuda:0",
            "dtype": torch.bfloat16,
            "attn_implementation": "sdpa",
            "device_label": torch.cuda.get_device_name(0),
        }
    return {
        "device_map": "cpu",
        "dtype": torch.float32,
        "attn_implementation": "sdpa",
        "device_label": "CPU",
    }


def load_model(name: str):
    _, Model = runtime()
    settings = device_settings()
    print(f"Loading {name}")
    print(f"Device: {settings['device_label']}")
    return Model.from_pretrained(
        name,
        device_map=settings["device_map"],
        dtype=settings["dtype"],
        attn_implementation=settings["attn_implementation"],
    )


def doctor() -> int:
    print("BASIL VOICE CAPABILITY v0.1")
    print("Python:", sys.version.split()[0])
    print("Working directory:", ROOT)
    _, _, free = shutil.disk_usage(ROOT)
    print(f"Free disk: {free / (1024**3):.1f} GB")
    try:
        import torch
        import qwen_tts
        import soundfile
        print("PyTorch:", torch.__version__)
        print("CUDA available:", torch.cuda.is_available())
        if torch.cuda.is_available():
            print("GPU:", torch.cuda.get_device_name(0))
        else:
            print("No CUDA GPU detected. CPU mode is supported but may be slow.")
        print("qwen-tts import: PASS")
        print("soundfile import: PASS")
    except Exception as exc:
        print("Dependency check: FAIL:", exc)
        return 1
    if free < 12 * 1024**3:
        print("WARNING: less than 12 GB free disk. Model downloads may fail.")
    print("Doctor: PASS")
    return 0


def design() -> int:
    import soundfile as sf
    spec = read_spec()
    text = seed_text()
    model = load_model(spec["design_model"])
    print("Generating the initial original BASIL reference voice...")
    wavs, sr = model.generate_voice_design(
        text=text,
        language=spec["language"],
        instruct=spec["instruct"],
    )
    sf.write(str(REFERENCE_PATH), wavs[0], sr)
    digest = hashlib.sha256(REFERENCE_PATH.read_bytes()).hexdigest()
    lock = {
        "voice_name": spec["name"],
        "reference_file": REFERENCE_PATH.name,
        "reference_sha256": digest,
        "reference_text": text,
        "voice_spec_sha256": hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest(),
        "runtime_model": spec["runtime_model"],
        "state": "REFERENCE_GENERATED_NOT_CONFIRMED",
    }
    LOCK_PATH.write_text(json.dumps(lock, indent=2), encoding="utf-8")
    print("Created:", REFERENCE_PATH)
    print("SHA-256:", digest)
    print("Voice is now usable. Final benchmark confirmation remains later.")
    return 0


def require_reference() -> str:
    if not REFERENCE_PATH.exists():
        raise SystemExit("No BASIL reference voice exists. Run: python basil_voice.py design")
    return seed_text()


def make_prompt(model):
    return model.create_voice_clone_prompt(
        ref_audio=str(REFERENCE_PATH),
        ref_text=require_reference(),
        x_vector_only_mode=False,
    )


def generate(text: str, output_path: Path) -> Path:
    import soundfile as sf
    spec = read_spec()
    model = load_model(spec["runtime_model"])
    prompt = make_prompt(model)
    wavs, sr = model.generate_voice_clone(
        text=text,
        language=spec["language"],
        voice_clone_prompt=prompt,
    )
    sf.write(str(output_path), wavs[0], sr)
    return output_path


def speak(text: str, output: str | None) -> int:
    out = Path(output) if output else OUTPUT_DIR / "basil_speech.wav"
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    generate(text, out)
    print("Created:", out)
    return 0


def serve(host: str, port: int) -> int:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import Response
    from pydantic import BaseModel
    import soundfile as sf
    import uvicorn

    spec = read_spec()
    model = load_model(spec["runtime_model"])
    prompt = make_prompt(model)
    app = FastAPI(title="BASIL Voice API", version="0.1")

    class SpeakRequest(BaseModel):
        text: str

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "voice": spec["name"],
            "reference_exists": REFERENCE_PATH.exists(),
        }

    @app.post("/speak")
    def api_speak(req: SpeakRequest):
        if not req.text.strip():
            raise HTTPException(status_code=400, detail="text is required")
        wavs, sr = model.generate_voice_clone(
            text=req.text,
            language=spec["language"],
            voice_clone_prompt=prompt,
        )
        buf = io.BytesIO()
        sf.write(buf, wavs[0], sr, format="WAV")
        return Response(content=buf.getvalue(), media_type="audio/wav")

    print(f"BASIL Voice API: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="BASIL local voice capability")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    sub.add_parser("design")
    speak_parser = sub.add_parser("speak")
    speak_parser.add_argument("text")
    speak_parser.add_argument("--output")
    serve_parser = sub.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.cmd == "doctor":
        return doctor()
    if args.cmd == "design":
        return design()
    if args.cmd == "speak":
        return speak(args.text, args.output)
    if args.cmd == "serve":
        return serve(args.host, args.port)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
