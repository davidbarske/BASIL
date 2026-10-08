"""Synthetic cross-language proof; no persistence or private operational data."""
import json
from pathlib import Path
import sys

from basil.sybil_exchange import dumps, loads

FIXTURES = Path("fixtures/sybil")
PROOF = Path("clients/android/v0.1/source/app/build/sybil-proof")


def main():
    if sys.argv[1:] == ["--prepare"]:
        PROOF.mkdir(parents=True, exist_ok=True)
        shared = (FIXTURES / "canonical-v1.json").read_text()
        emitted = dumps(loads(shared))
        assert json.loads(emitted) == json.loads(shared)
        (PROOF / "python-origin.json").write_text(emitted, encoding="utf-8")
        print("PASS: Python generated canonical fixture JSON for Android decoding")
        return
    for name in ("canonical-v1.json", "android-origin.json", "android-v01-expected.json"):
        expected = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
        emitted = json.loads((PROOF / name).read_text(encoding="utf-8"))
        assert emitted == expected, name
        assert json.loads(dumps(loads(json.dumps(emitted)))) == expected, name
        print("PASS: Android-produced JSON -> Python -> equivalent canonical JSON:", name)
    print("PASS: Python -> Android -> canonical JSON has exact semantic equality")


if __name__ == "__main__":
    main()
