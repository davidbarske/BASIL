#!/usr/bin/env python3
"""
diarise_meetings_v2.py

Evidence-preserving speaker diarisation and quality-control runner for one or
more meeting recordings using pyannote/speaker-diarization-community-1.

Design goals
------------
1. Never modify the original source recording.
2. Make long-running inference observable with progress and run-state files.
3. Make reruns safe and resumable at the preparation/output level.
4. Preserve portable diarisation evidence (JSON/TSV/RTTM).
5. Add useful conversation/QC metrics without altering raw diarisation output.
6. Preserve representative speaker embeddings when pyannote exposes them.
7. Generate cross-meeting embedding similarity data when multiple recordings
   are processed in one batch.

Per-recording outputs
---------------------
  - source_manifest.json
  - run_status.json
  - run_history.jsonl
  - <name>_16k_mono.wav                     (working derivative, optional delete)
  - diarisation_regular.json
  - diarisation_regular.tsv
  - diarisation_regular.rttm
  - diarisation_exclusive.json              (when supported)
  - diarisation_exclusive.tsv               (when supported)
  - diarisation_exclusive.rttm               (when supported)
  - speaker_embeddings.npz                  (when supported)
  - speaker_embedding_index.json            (when supported)
  - diarisation_analysis.json
  - diarisation_summary.json                (compatibility summary)
  - diarisation_timeline.svg
  - artifact_manifest.json

Batch outputs
-------------
  - batch_summary.json
  - cross_meeting_speaker_similarity.tsv    (when >= 2 embedding sets exist)
  - cross_meeting_speaker_similarity.json   (when >= 2 embedding sets exist)

Requirements
------------
  pip install pyannote.audio torch numpy
  ffmpeg and ffprobe available on PATH

Authentication
--------------
  Recommended: run `hf auth login`
  or set HF_TOKEN in the environment.

Examples
--------
  python diarise_meetings_v2.py "Meeting 01.mp4" --num-speakers 2
  python diarise_meetings_v2.py "Meeting 02.m4a" --min-speakers 2 --max-speakers 4
  python diarise_meetings_v2.py "Meeting 01.mp4" "Meeting 02.mp4" --min-speakers 2 --max-speakers 4

Automatic speaker estimation is used when no speaker constraints are supplied.
Re-running an identical completed job is skipped unless --force is used.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
import traceback
import wave
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
from pyannote.audio import Pipeline

MODEL_ID = "pyannote/speaker-diarization-community-1"
SCRIPT_VERSION = "2.0.0"

# These are heuristics for directing human review, not claims of diarisation error.
QC_THRESHOLDS = {
    "high_overlap_fraction_of_speech": 0.15,
    "low_speech_coverage_fraction": 0.40,
    "high_short_turn_fraction": 0.25,
    "short_turn_seconds": 0.50,
    "very_long_unlabelled_gap_seconds": 60.0,
}


# ---------------------------------------------------------------------------
# Basic utilities
# ---------------------------------------------------------------------------


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def monotonic_seconds() -> float:
    return time.perf_counter()


def safe_stem(path: Path) -> str:
    """Return a filesystem-safe-ish deterministic stem without over-normalising."""
    stem = path.stem.strip() or "recording"
    return "".join(c if c not in '<>:"/\\|?*' else "_" for c in stem)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(data: Any) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_json(path: Path, data: Any) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def write_tsv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def package_version(package: str) -> Optional[str]:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def check_command(name: str) -> str:
    exe = shutil.which(name)
    if not exe:
        raise RuntimeError(
            f"{name} was not found on PATH. Install FFmpeg and ensure "
            f"`{name}` can be run from your terminal."
        )
    return exe


def command_version(name: str) -> Optional[str]:
    try:
        exe = check_command(name)
        proc = subprocess.run(
            [exe, "-version"],
            capture_output=True,
            text=True,
            check=True,
        )
        first = (proc.stdout or proc.stderr).splitlines()
        return first[0].strip() if first else None
    except Exception:
        return None


def human_duration(seconds: Optional[float]) -> str:
    if seconds is None or not math.isfinite(seconds):
        return "?"
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def round_float(value: Any, digits: int = 6) -> Any:
    if isinstance(value, float):
        if math.isfinite(value):
            return round(value, digits)
        return None
    return value


# ---------------------------------------------------------------------------
# Media preparation and diagnostics
# ---------------------------------------------------------------------------


def ffprobe_metadata(source: Path) -> Dict[str, Any]:
    check_command("ffprobe")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(source),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def extract_duration_seconds(metadata: Dict[str, Any]) -> Optional[float]:
    candidates: List[Any] = []
    fmt = metadata.get("format") or {}
    candidates.append(fmt.get("duration"))
    for stream in metadata.get("streams") or []:
        if stream.get("codec_type") == "audio":
            candidates.append(stream.get("duration"))
    for value in candidates:
        try:
            x = float(value)
            if x > 0 and math.isfinite(x):
                return x
        except (TypeError, ValueError):
            pass
    return None


def make_canonical_wav(source: Path, destination: Path) -> None:
    check_command("ffmpeg")
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_name(destination.stem + ".tmp.wav")
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(tmp),
    ]
    try:
        subprocess.run(cmd, check=True)
        os.replace(tmp, destination)
    finally:
        tmp.unlink(missing_ok=True)


def wav_metadata(path: Path) -> Dict[str, Any]:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return {
            "channels": wf.getnchannels(),
            "sample_width_bytes": wf.getsampwidth(),
            "sample_rate_hz": rate,
            "frame_count": frames,
            "duration_seconds": frames / rate if rate else None,
            "compression_type": wf.getcomptype(),
        }


def analyse_pcm16_wav(path: Path, chunk_frames: int = 16000 * 30) -> Dict[str, Any]:
    """
    Stream a canonical PCM16 WAV and calculate lightweight objective diagnostics.

    This deliberately avoids loading an entire multi-hour meeting into memory.
    """
    with wave.open(str(path), "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise RuntimeError("Expected canonical WAV to be mono 16-bit PCM.")

        rate = wf.getframerate()
        total_frames = 0
        sum_squares = 0.0
        peak_abs = 0
        clipped = 0
        zeros = 0

        while True:
            raw = wf.readframes(chunk_frames)
            if not raw:
                break
            samples = np.frombuffer(raw, dtype="<i2").astype(np.int32, copy=False)
            if samples.size == 0:
                continue

            total_frames += int(samples.size)
            abs_samples = np.abs(samples)
            local_peak = int(abs_samples.max(initial=0))
            peak_abs = max(peak_abs, local_peak)
            clipped += int(np.count_nonzero(abs_samples >= 32767))
            zeros += int(np.count_nonzero(samples == 0))
            # float64 accumulation avoids integer overflow.
            sum_squares += float(np.dot(samples.astype(np.float64), samples.astype(np.float64)))

    rms = math.sqrt(sum_squares / total_frames) if total_frames else 0.0
    full_scale = 32768.0
    rms_dbfs = 20.0 * math.log10(rms / full_scale) if rms > 0 else None
    peak_dbfs = 20.0 * math.log10(peak_abs / 32767.0) if peak_abs > 0 else None

    return {
        "sample_rate_hz": rate,
        "samples": total_frames,
        "duration_seconds": total_frames / rate if rate else None,
        "rms_amplitude": round_float(rms),
        "rms_dbfs": round_float(rms_dbfs),
        "peak_absolute_sample": peak_abs,
        "peak_dbfs": round_float(peak_dbfs),
        "clipped_sample_count": clipped,
        "clipped_sample_fraction": round_float(clipped / total_frames if total_frames else 0.0),
        "zero_sample_count": zeros,
        "zero_sample_fraction": round_float(zeros / total_frames if total_frames else 0.0),
        "notes": [
            "These are lightweight signal diagnostics, not perceptual audio-quality scores.",
            "Clipping uses absolute PCM16 samples >= 32767 as a conservative indicator.",
        ],
    }


# ---------------------------------------------------------------------------
# Pyannote serialisation and progress tracking
# ---------------------------------------------------------------------------


def annotation_to_rows(annotation: Any) -> List[Dict[str, Any]]:
    """Convert a pyannote Annotation-like object to portable JSON/TSV rows."""
    rows: List[Dict[str, Any]] = []

    if annotation is None:
        return rows

    if hasattr(annotation, "itertracks"):
        for item in annotation.itertracks(yield_label=True):
            if len(item) == 3:
                segment, track, speaker = item
            else:
                segment, speaker = item
                track = None
            rows.append(
                {
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "duration": float(segment.end - segment.start),
                    "speaker": str(speaker),
                    "track": None if track is None else str(track),
                }
            )
        rows.sort(key=lambda r: (r["start"], r["end"], r["speaker"]))
        return rows

    # Fallback for alternate pyannote output interfaces.
    try:
        for segment, speaker in annotation:
            rows.append(
                {
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "duration": float(segment.end - segment.start),
                    "speaker": str(speaker),
                    "track": None,
                }
            )
    except Exception as exc:
        raise RuntimeError(
            "Could not serialise the diarisation output. "
            "Inspect the installed pyannote.audio version/API."
        ) from exc

    rows.sort(key=lambda r: (r["start"], r["end"], r["speaker"]))
    return rows


def write_diarisation_tsv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    write_tsv(path, rows, ["start", "end", "duration", "speaker", "track"])


def write_rttm(path: Path, annotation: Any) -> bool:
    if annotation is None or not hasattr(annotation, "write_rttm"):
        return False
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        annotation.write_rttm(f)
    os.replace(tmp, path)
    return True


@dataclass
class RunState:
    path: Path
    history_path: Path
    recording_name: str
    started_monotonic: float = field(default_factory=monotonic_seconds)
    started_utc: str = field(default_factory=utc_now)
    current: Dict[str, Any] = field(default_factory=dict)

    def update(self, status: str, **extra: Any) -> None:
        elapsed = monotonic_seconds() - self.started_monotonic
        self.current.update(
            {
                "status": status,
                "recording": self.recording_name,
                "started_utc": self.started_utc,
                "last_update_utc": utc_now(),
                "elapsed_seconds": round_float(elapsed, 3),
            }
        )
        self.current.update(extra)
        write_json(self.path, self.current)

    def event(self, event: str, **extra: Any) -> None:
        payload = {
            "utc": utc_now(),
            "elapsed_seconds": round_float(monotonic_seconds() - self.started_monotonic, 3),
            "event": event,
        }
        payload.update(extra)
        append_jsonl(self.history_path, payload)


class PipelineProgressReporter:
    """
    Lightweight pyannote pipeline hook.

    Current pyannote pipelines call hooks as:
      hook(step_name, artefact, file=file, completed=..., total=...)

    Time-consuming stages may invoke the same step repeatedly with progress.
    This reporter persists state and throttles terminal updates to avoid spam.
    """

    def __init__(self, run_state: RunState, min_percent_step: int = 5, min_seconds_step: float = 10.0):
        self.run_state = run_state
        self.min_percent_step = max(1, min_percent_step)
        self.min_seconds_step = max(1.0, min_seconds_step)
        self.last_print_percent: Dict[str, int] = {}
        self.last_print_time: Dict[str, float] = {}
        self.step_first_seen: Dict[str, float] = {}
        self.step_last_seen: Dict[str, float] = {}
        self.step_progress: Dict[str, Dict[str, Any]] = {}
        self.last_step: Optional[str] = None

    def __call__(
        self,
        step_name: str,
        step_artefact: Any = None,
        file: Any = None,
        completed: Optional[int] = None,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        now = monotonic_seconds()
        step = str(step_name)
        self.step_first_seen.setdefault(step, now)
        self.step_last_seen[step] = now

        pct: Optional[int] = None
        if completed is not None and total not in (None, 0):
            try:
                pct = int(max(0.0, min(100.0, 100.0 * float(completed) / float(total))))
            except Exception:
                pct = None

        try:
            completed_json = None if completed is None else int(completed)
        except Exception:
            completed_json = None
        try:
            total_json = None if total is None else int(total)
        except Exception:
            total_json = None

        entry: Dict[str, Any] = {
            "step": step,
            "completed": completed_json,
            "total": total_json,
            "percent": pct,
            "first_seen_elapsed_seconds": round_float(self.step_first_seen[step] - self.run_state.started_monotonic, 3),
            "last_seen_elapsed_seconds": round_float(now - self.run_state.started_monotonic, 3),
        }
        self.step_progress[step] = entry

        last_pct = self.last_print_percent.get(step, -self.min_percent_step)
        last_time = self.last_print_time.get(step, 0.0)
        stage_changed = step != self.last_step
        should_print = stage_changed

        if pct is None:
            # Major step completion events often arrive without completed/total.
            should_print = should_print or (now - last_time >= 1.0)
        else:
            if pct >= 100 or pct - last_pct >= self.min_percent_step:
                should_print = True
            elif now - last_time >= self.min_seconds_step:
                should_print = True

        if should_print:
            # Persist on the same throttled cadence as terminal reporting. This
            # keeps crash-state useful without turning every model batch into a
            # disk fsync/write cycle.
            self.run_state.update(
                "DIARISING",
                current_stage=step,
                stage_progress=entry,
            )
            elapsed = now - self.run_state.started_monotonic
            if pct is None:
                message = f"  {step:<24} update         elapsed {human_duration(elapsed)}"
            else:
                message = f"  {step:<24} {pct:>3}%           elapsed {human_duration(elapsed)}"
            print(message, flush=True)
            if pct is not None:
                self.last_print_percent[step] = pct
            self.last_print_time[step] = now
            self.last_step = step

    def summary(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for step, first in self.step_first_seen.items():
            last = self.step_last_seen.get(step, first)
            result[step] = {
                "observed_hook_span_seconds": round_float(last - first, 3),
                "last_progress": self.step_progress.get(step),
                "note": "Hook span is observational and is not guaranteed to equal full stage runtime.",
            }
        return result


# ---------------------------------------------------------------------------
# Conversation statistics
# ---------------------------------------------------------------------------


def merge_intervals(intervals: Iterable[Tuple[float, float]]) -> List[Tuple[float, float]]:
    cleaned = sorted((float(s), float(e)) for s, e in intervals if float(e) > float(s))
    if not cleaned:
        return []
    merged: List[List[float]] = [[cleaned[0][0], cleaned[0][1]]]
    for start, end in cleaned[1:]:
        last = merged[-1]
        if start <= last[1]:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return [(s, e) for s, e in merged]


def interval_total(intervals: Iterable[Tuple[float, float]]) -> float:
    return sum(e - s for s, e in merge_intervals(intervals))


def overlap_seconds(rows: Sequence[Dict[str, Any]]) -> float:
    """Duration where at least two distinct speakers are active."""
    events: List[Tuple[float, int, str]] = []
    for row in rows:
        s, e, speaker = float(row["start"]), float(row["end"]), str(row["speaker"])
        if e <= s:
            continue
        # Process endings before starts at identical timestamps.
        events.append((s, 1, speaker))
        events.append((e, -1, speaker))
    events.sort(key=lambda x: (x[0], x[1]))

    active_counts: Dict[str, int] = defaultdict(int)
    last_t: Optional[float] = None
    overlap = 0.0

    for t, delta, speaker in events:
        if last_t is not None and t > last_t:
            active_speakers = sum(1 for c in active_counts.values() if c > 0)
            if active_speakers >= 2:
                overlap += t - last_t
        active_counts[speaker] += delta
        if active_counts[speaker] <= 0:
            active_counts.pop(speaker, None)
        last_t = t
    return overlap


def unlabelled_gaps(rows: Sequence[Dict[str, Any]], recording_duration: float) -> List[Tuple[float, float]]:
    speech = merge_intervals((float(r["start"]), float(r["end"])) for r in rows)
    gaps: List[Tuple[float, float]] = []
    cursor = 0.0
    for start, end in speech:
        start = max(0.0, min(recording_duration, start))
        end = max(0.0, min(recording_duration, end))
        if start > cursor:
            gaps.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < recording_duration:
        gaps.append((cursor, recording_duration))
    return [(s, e) for s, e in gaps if e > s]


def speaker_statistics(rows: Sequence[Dict[str, Any]], denominator_seconds: Optional[float] = None) -> Dict[str, Any]:
    by: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        by[str(row["speaker"])].append(float(row["duration"]))

    result: Dict[str, Any] = {}
    short_threshold = QC_THRESHOLDS["short_turn_seconds"]
    for speaker, durations in sorted(by.items()):
        total = sum(durations)
        short_count = sum(1 for x in durations if x < short_threshold)
        result[speaker] = {
            "turn_count": len(durations),
            "labelled_seconds": round_float(total),
            "share_of_denominator": round_float(total / denominator_seconds if denominator_seconds else None),
            "mean_turn_seconds": round_float(mean(durations) if durations else 0.0),
            "median_turn_seconds": round_float(median(durations) if durations else 0.0),
            "longest_turn_seconds": round_float(max(durations) if durations else 0.0),
            "short_turn_count_lt_0_5s": short_count,
            "short_turn_fraction_lt_0_5s": round_float(short_count / len(durations) if durations else 0.0),
        }
    return result


def transition_statistics(rows: Sequence[Dict[str, Any]], recording_duration: float) -> Dict[str, Any]:
    ordered = sorted(rows, key=lambda r: (float(r["start"]), float(r["end"])))
    matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    switches = 0
    previous: Optional[str] = None

    for row in ordered:
        speaker = str(row["speaker"])
        if previous is not None and speaker != previous:
            matrix[previous][speaker] += 1
            switches += 1
        previous = speaker

    minutes = recording_duration / 60.0 if recording_duration > 0 else None
    return {
        "speaker_switches": switches,
        "speaker_switches_per_minute": round_float(switches / minutes if minutes else None),
        "transition_matrix": {
            source: dict(sorted(targets.items())) for source, targets in sorted(matrix.items())
        },
        "note": "Transitions use adjacent exclusive diarisation segments and are descriptive, not semantic turn-taking inference.",
    }


def conversation_analysis(
    regular_rows: Sequence[Dict[str, Any]],
    exclusive_rows: Sequence[Dict[str, Any]],
    recording_duration: float,
    min_speakers: Optional[int],
    max_speakers: Optional[int],
    num_speakers: Optional[int],
) -> Dict[str, Any]:
    base_rows = list(regular_rows)
    exclusive = list(exclusive_rows) if exclusive_rows else list(regular_rows)

    regular_union = interval_total((r["start"], r["end"]) for r in base_rows)
    overlap = overlap_seconds(base_rows)
    gaps = unlabelled_gaps(base_rows, recording_duration)
    longest_gap = max((e - s for s, e in gaps), default=0.0)
    longest_gap_interval = max(gaps, key=lambda x: x[1] - x[0]) if gaps else None

    exclusive_total = sum(float(r["duration"]) for r in exclusive)
    speakers = sorted({str(r["speaker"]) for r in exclusive})
    spk_stats = speaker_statistics(exclusive, denominator_seconds=exclusive_total if exclusive_total > 0 else None)
    shares = [
        v.get("share_of_denominator")
        for v in spk_stats.values()
        if isinstance(v.get("share_of_denominator"), (int, float))
    ]
    hhi = sum(float(x) ** 2 for x in shares)
    dominant = max(shares, default=0.0)

    transition = transition_statistics(exclusive, recording_duration)

    qc_flags: List[Dict[str, Any]] = []
    speech_coverage = regular_union / recording_duration if recording_duration > 0 else 0.0
    overlap_fraction = overlap / regular_union if regular_union > 0 else 0.0

    if overlap_fraction >= QC_THRESHOLDS["high_overlap_fraction_of_speech"]:
        qc_flags.append(
            {
                "code": "HIGH_OVERLAP",
                "severity": "review",
                "value": round_float(overlap_fraction),
                "message": "A high fraction of detected speech contains simultaneous speakers; inspect overlap-heavy regions if attribution matters.",
            }
        )

    if speech_coverage < QC_THRESHOLDS["low_speech_coverage_fraction"]:
        qc_flags.append(
            {
                "code": "LOW_SPEECH_COVERAGE",
                "severity": "review",
                "value": round_float(speech_coverage),
                "message": "A relatively small fraction of the recording is diarised as speech; this may be legitimate or may indicate audio/VAD issues.",
            }
        )

    for speaker, stats in spk_stats.items():
        fraction = stats["short_turn_fraction_lt_0_5s"]
        if isinstance(fraction, (int, float)) and fraction >= QC_THRESHOLDS["high_short_turn_fraction"]:
            qc_flags.append(
                {
                    "code": "FRAGMENTED_SPEAKER",
                    "severity": "review",
                    "speaker": speaker,
                    "value": fraction,
                    "message": "Many very short segments were assigned to this speaker; inspect for fragmentation or backchannel-heavy speech.",
                }
            )

    if longest_gap >= QC_THRESHOLDS["very_long_unlabelled_gap_seconds"]:
        qc_flags.append(
            {
                "code": "LONG_UNLABELLED_REGION",
                "severity": "review",
                "value_seconds": round_float(longest_gap),
                "interval": {
                    "start": round_float(longest_gap_interval[0]) if longest_gap_interval else None,
                    "end": round_float(longest_gap_interval[1]) if longest_gap_interval else None,
                },
                "message": "The recording contains a long region with no detected speech; verify whether this is expected silence, a break or an audio issue.",
            }
        )

    detected_count = len(speakers)
    if num_speakers is None:
        if min_speakers is not None and detected_count == min_speakers:
            qc_flags.append(
                {
                    "code": "SPEAKER_COUNT_AT_MIN_BOUNDARY",
                    "severity": "informational",
                    "value": detected_count,
                    "message": "Detected speaker count sits exactly on the supplied minimum boundary.",
                }
            )
        if max_speakers is not None and detected_count == max_speakers:
            qc_flags.append(
                {
                    "code": "SPEAKER_COUNT_AT_MAX_BOUNDARY",
                    "severity": "informational",
                    "value": detected_count,
                    "message": "Detected speaker count sits exactly on the supplied maximum boundary.",
                }
            )

    return {
        "recording_duration_seconds": round_float(recording_duration),
        "detected_speaker_count": detected_count,
        "detected_speakers": speakers,
        "speech": {
            "detected_speech_union_seconds": round_float(regular_union),
            "speech_coverage_fraction": round_float(speech_coverage),
            "unlabelled_seconds": round_float(max(0.0, recording_duration - regular_union)),
            "unlabelled_fraction": round_float(max(0.0, 1.0 - speech_coverage)),
            "longest_unlabelled_gap_seconds": round_float(longest_gap),
            "longest_unlabelled_gap": {
                "start": round_float(longest_gap_interval[0]) if longest_gap_interval else None,
                "end": round_float(longest_gap_interval[1]) if longest_gap_interval else None,
            },
        },
        "overlap": {
            "overlap_seconds": round_float(overlap),
            "overlap_fraction_of_detected_speech": round_float(overlap_fraction),
            "note": "Calculated from regular diarisation where simultaneous speakers are retained.",
        },
        "speaker_statistics": spk_stats,
        "speaker_balance": {
            "dominant_speaker_share": round_float(dominant),
            "herfindahl_hirschman_index": round_float(hhi),
            "effective_speaker_count": round_float((1.0 / hhi) if hhi > 0 else None),
            "note": "Descriptive concentration metrics based on exclusive diarisation talk-time shares; they do not imply social or organisational dominance.",
        },
        "turn_taking": transition,
        "quality_control": {
            "thresholds": QC_THRESHOLDS,
            "flags": qc_flags,
            "flag_count": len(qc_flags),
            "note": "QC flags are heuristics that direct review; they are not ground-truth error labels.",
        },
    }


# ---------------------------------------------------------------------------
# Timeline visualisation
# ---------------------------------------------------------------------------


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_timeline_svg(
    path: Path,
    rows: Sequence[Dict[str, Any]],
    duration: float,
    title: str,
) -> None:
    if duration <= 0:
        return

    speakers = sorted({str(r["speaker"]) for r in rows})
    if not speakers:
        return

    width = 1600
    left = 170
    right = 40
    top = 60
    row_height = 34
    bottom = 70
    plot_width = width - left - right
    height = top + len(speakers) * row_height + bottom
    palette = [
        "#2563eb",
        "#dc2626",
        "#059669",
        "#7c3aed",
        "#ea580c",
        "#0891b2",
        "#be185d",
        "#4d7c0f",
    ]
    colour = {speaker: palette[i % len(palette)] for i, speaker in enumerate(speakers)}

    def x_for(t: float) -> float:
        return left + plot_width * max(0.0, min(duration, t)) / duration

    lines: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{left}" y="30" font-family="Arial, sans-serif" font-size="20" font-weight="bold">{xml_escape(title)}</text>',
    ]

    for i, speaker in enumerate(speakers):
        y = top + i * row_height
        lines.append(
            f'<text x="10" y="{y + 20}" font-family="Arial, sans-serif" font-size="14">{xml_escape(speaker)}</text>'
        )
        lines.append(
            f'<line x1="{left}" y1="{y + row_height / 2}" x2="{left + plot_width}" y2="{y + row_height / 2}" stroke="#d1d5db" stroke-width="1"/>'
        )

    speaker_y = {speaker: top + i * row_height + 6 for i, speaker in enumerate(speakers)}
    for row in rows:
        speaker = str(row["speaker"])
        start = float(row["start"])
        end = float(row["end"])
        if end <= start:
            continue
        x = x_for(start)
        w = max(1.0, x_for(end) - x)
        y = speaker_y[speaker]
        lines.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="22" fill="{colour[speaker]}" opacity="0.85"/>'
        )

    tick_count = 10
    axis_y = top + len(speakers) * row_height + 12
    for i in range(tick_count + 1):
        t = duration * i / tick_count
        x = x_for(t)
        lines.append(
            f'<line x1="{x:.2f}" y1="{axis_y}" x2="{x:.2f}" y2="{axis_y + 7}" stroke="#111827" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{x:.2f}" y="{axis_y + 28}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">{human_duration(t)}</text>'
        )

    lines.append(
        f'<text x="{left}" y="{height - 12}" font-family="Arial, sans-serif" font-size="11" fill="#4b5563">Regular diarisation timeline. Overlap is visible when multiple speaker rows contain segments at the same time.</text>'
    )
    lines.append("</svg>")
    atomic_write_text(path, "\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Embeddings and cross-recording comparison
# ---------------------------------------------------------------------------


def extract_speaker_labels(annotation: Any, rows: Sequence[Dict[str, Any]]) -> List[str]:
    if annotation is not None and hasattr(annotation, "labels"):
        try:
            return [str(x) for x in annotation.labels()]
        except Exception:
            pass
    return sorted({str(r["speaker"]) for r in rows})


def save_speaker_embeddings(
    run_dir: Path,
    output: Any,
    regular_annotation: Any,
    regular_rows: Sequence[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    embeddings = getattr(output, "speaker_embeddings", None)
    if embeddings is None:
        return None

    array = np.asarray(embeddings)
    if array.ndim != 2:
        return {
            "available": False,
            "reason": f"Unexpected speaker_embeddings shape: {array.shape!r}",
        }

    labels = extract_speaker_labels(regular_annotation, regular_rows)
    if len(labels) != array.shape[0]:
        # Preserve evidence, but avoid claiming an incorrect label mapping.
        np.savez_compressed(run_dir / "speaker_embeddings.npz", embeddings=array)
        info = {
            "available": True,
            "mapped": False,
            "shape": list(array.shape),
            "speaker_labels": labels,
            "warning": "Embedding row count did not match diarisation label count; raw embedding matrix preserved without row-to-speaker mapping.",
        }
        write_json(run_dir / "speaker_embedding_index.json", info)
        return info

    np.savez_compressed(
        run_dir / "speaker_embeddings.npz",
        embeddings=array,
        labels=np.asarray(labels, dtype=str),
    )
    mapping = {speaker: i for i, speaker in enumerate(labels)}
    info = {
        "available": True,
        "mapped": True,
        "shape": list(array.shape),
        "speaker_labels": labels,
        "speaker_to_embedding_row": mapping,
        "notes": [
            "Representative speaker embeddings are recording-local model artefacts.",
            "Embedding similarity can support cross-recording speaker matching but does not prove identity.",
        ],
    }
    write_json(run_dir / "speaker_embedding_index.json", info)
    return info


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 0 or not math.isfinite(denom):
        return None
    value = float(np.dot(a, b) / denom)
    return max(-1.0, min(1.0, value))


def load_embedding_set(run_dir: Path, recording_name: str) -> Optional[Dict[str, Any]]:
    path = run_dir / "speaker_embeddings.npz"
    index_path = run_dir / "speaker_embedding_index.json"
    if not path.exists() or not index_path.exists():
        return None
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        if not index.get("mapped"):
            return None
        with np.load(path, allow_pickle=False) as data:
            embeddings = np.asarray(data["embeddings"])
            labels = [str(x) for x in data["labels"].tolist()]
        if embeddings.ndim != 2 or len(labels) != embeddings.shape[0]:
            return None
        return {
            "recording": recording_name,
            "run_dir": run_dir,
            "labels": labels,
            "embeddings": embeddings,
        }
    except Exception:
        return None


def write_cross_meeting_similarity(output_root: Path, sets: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(sets) < 2:
        return None

    rows: List[Dict[str, Any]] = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            a = sets[i]
            b = sets[j]
            for ia, label_a in enumerate(a["labels"]):
                for ib, label_b in enumerate(b["labels"]):
                    sim = cosine_similarity(a["embeddings"][ia], b["embeddings"][ib])
                    rows.append(
                        {
                            "recording_a": a["recording"],
                            "speaker_a": label_a,
                            "recording_b": b["recording"],
                            "speaker_b": label_b,
                            "cosine_similarity": "" if sim is None else f"{sim:.6f}",
                        }
                    )

    write_tsv(
        output_root / "cross_meeting_speaker_similarity.tsv",
        rows,
        ["recording_a", "speaker_a", "recording_b", "speaker_b", "cosine_similarity"],
    )

    # Determine best candidate per speaker in each cross-recording pairing.
    best_matches: List[Dict[str, Any]] = []
    pair_groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        pair_groups[(row["recording_a"], row["speaker_a"], row["recording_b"])].append(row)
        # Reverse orientation as well so each speaker gets a candidate summary.
        reverse = {
            "recording_a": row["recording_b"],
            "speaker_a": row["speaker_b"],
            "recording_b": row["recording_a"],
            "speaker_b": row["speaker_a"],
            "cosine_similarity": row["cosine_similarity"],
        }
        pair_groups[(reverse["recording_a"], reverse["speaker_a"], reverse["recording_b"])].append(reverse)

    for key, candidates in sorted(pair_groups.items()):
        numeric = [c for c in candidates if c["cosine_similarity"] != ""]
        if not numeric:
            continue
        best = max(numeric, key=lambda c: float(c["cosine_similarity"]))
        best_matches.append(
            {
                "recording": key[0],
                "speaker": key[1],
                "compared_recording": key[2],
                "best_candidate_speaker": best["speaker_b"],
                "cosine_similarity": float(best["cosine_similarity"]),
            }
        )

    payload = {
        "created_utc": utc_now(),
        "comparison_count": len(rows),
        "best_matches": best_matches,
        "notes": [
            "Cosine similarity is a model-space similarity measure, not proof of human identity.",
            "Use known speakers or manual review before assigning persistent names across meetings.",
            "No universal identity threshold is imposed by this script because recording conditions and embedding models affect calibration.",
        ],
    }
    write_json(output_root / "cross_meeting_speaker_similarity.json", payload)
    return payload


# ---------------------------------------------------------------------------
# Environment and evidence manifests
# ---------------------------------------------------------------------------


def environment_manifest(device: torch.device) -> Dict[str, Any]:
    gpu: Optional[Dict[str, Any]] = None
    if device.type == "cuda" and torch.cuda.is_available():
        gpu = {
            "name": torch.cuda.get_device_name(0),
            "device_count": torch.cuda.device_count(),
            "cuda_runtime_reported_by_torch": torch.version.cuda,
        }

    return {
        "script_version": SCRIPT_VERSION,
        "script_file": str(Path(__file__).resolve()),
        "command_line": list(sys.argv),
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "device": str(device),
        "gpu": gpu,
        "software": {
            "torch": torch.__version__,
            "numpy": np.__version__,
            "pyannote.audio": package_version("pyannote.audio"),
            "huggingface_hub": package_version("huggingface_hub"),
        },
        "ffmpeg": command_version("ffmpeg"),
        "ffprobe": command_version("ffprobe"),
    }


def create_artifact_manifest(run_dir: Path, exclude_names: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    excluded = set(exclude_names or []) | {"artifact_manifest.json"}
    artifacts: List[Dict[str, Any]] = []
    for path in sorted(run_dir.iterdir()):
        if not path.is_file() or path.name in excluded or path.name.endswith(".tmp"):
            continue
        artifacts.append(
            {
                "file": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    payload = {
        "created_utc": utc_now(),
        "artifacts": artifacts,
        "notes": [
            "Hashes cover generated evidence/derivative files present at manifest creation time.",
            "The original source hash is recorded separately in source_manifest.json.",
        ],
    }
    write_json(run_dir / "artifact_manifest.json", payload)
    return payload


# ---------------------------------------------------------------------------
# Device/pipeline
# ---------------------------------------------------------------------------


def resolve_device(requested: str) -> torch.device:
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("--device cuda requested but CUDA is not available.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_pipeline(device: torch.device, model_id: str) -> Pipeline:
    token = os.getenv("HF_TOKEN")
    pipeline = Pipeline.from_pretrained(model_id, token=token)
    pipeline.to(device)
    return pipeline


@dataclass
class PipelineProvider:
    """Load the pyannote pipeline only when a recording actually needs inference."""

    device: torch.device
    model_id: str
    _pipeline: Optional[Pipeline] = None

    def get(self) -> Pipeline:
        if self._pipeline is None:
            print(f"Loading model/pipeline: {self.model_id}", flush=True)
            try:
                self._pipeline = load_pipeline(self.device, self.model_id)
            except Exception:
                print("\nCould not load the pyannote model/pipeline.", file=sys.stderr)
                print(
                    "If using a gated Hugging Face model, confirm that you have accepted its access conditions "
                    "and authenticated with `hf auth login` or HF_TOKEN.",
                    file=sys.stderr,
                )
                raise
        return self._pipeline


# ---------------------------------------------------------------------------
# Core run
# ---------------------------------------------------------------------------


def build_config(
    model_id: str,
    device: torch.device,
    num_speakers: Optional[int],
    min_speakers: Optional[int],
    max_speakers: Optional[int],
) -> Dict[str, Any]:
    return {
        "model_id": model_id,
        "device": str(device),
        "speaker_constraints": {
            "num_speakers": num_speakers,
            "min_speakers": min_speakers,
            "max_speakers": max_speakers,
        },
        "pyannote.audio_version": package_version("pyannote.audio"),
    }


def expected_core_outputs(run_dir: Path, exclusive_required: bool = False) -> List[Path]:
    required = [
        run_dir / "source_manifest.json",
        run_dir / "diarisation_regular.json",
        run_dir / "diarisation_regular.tsv",
        run_dir / "diarisation_summary.json",
        run_dir / "diarisation_analysis.json",
        run_dir / "artifact_manifest.json",
    ]
    if exclusive_required:
        required.extend(
            [
                run_dir / "diarisation_exclusive.json",
                run_dir / "diarisation_exclusive.tsv",
            ]
        )
    return required


def completed_run_is_reusable(run_dir: Path, source_hash: str, config_hash: str) -> bool:
    status_path = run_dir / "run_status.json"
    manifest_path = run_dir / "source_manifest.json"
    if not status_path.exists() or not manifest_path.exists():
        return False
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return False

    if status.get("status") != "COMPLETE":
        return False
    if manifest.get("source_sha256") != source_hash:
        return False
    if manifest.get("configuration_sha256") != config_hash:
        return False

    exclusive_required = bool(status.get("exclusive_available"))
    return all(path.exists() for path in expected_core_outputs(run_dir, exclusive_required))


def legacy_summary(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_speaker = defaultdict(lambda: {"turns": 0, "labelled_seconds": 0.0})
    max_end = 0.0
    for row in rows:
        speaker = row["speaker"]
        by_speaker[speaker]["turns"] += 1
        by_speaker[speaker]["labelled_seconds"] += float(row["duration"])
        max_end = max(max_end, float(row["end"]))
    return {
        "segment_count": len(rows),
        "approx_last_segment_end_seconds": max_end,
        "speakers": dict(sorted(by_speaker.items())),
    }


def run_one(
    pipeline_provider: PipelineProvider,
    source: Path,
    output_root: Path,
    device: torch.device,
    model_id: str,
    num_speakers: Optional[int],
    min_speakers: Optional[int],
    max_speakers: Optional[int],
    keep_wav: bool,
    force: bool,
) -> Dict[str, Any]:
    source = source.resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    if not source.is_file():
        raise RuntimeError(f"Input is not a file: {source}")

    batch_start = monotonic_seconds()
    print(f"\n=== {source.name} ===", flush=True)

    print("[1] Hashing source...", flush=True)
    source_hash = sha256_file(source)

    config = build_config(model_id, device, num_speakers, min_speakers, max_speakers)
    config_hash = sha256_json(config)
    run_name = f"{safe_stem(source)}__{source_hash[:12]}__{config_hash[:10]}"
    base_run_dir = output_root / run_name

    # A normal rerun reuses/repairs the deterministic content/configuration
    # directory. An explicit --force rerun gets a new timestamped directory so
    # a prior COMPLETE evidence set is never silently overwritten.
    if force and base_run_dir.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = output_root / f"{run_name}__rerun_{stamp}"
        suffix = 1
        while run_dir.exists():
            run_dir = output_root / f"{run_name}__rerun_{stamp}_{suffix:02d}"
            suffix += 1
    else:
        run_dir = base_run_dir

    run_dir.mkdir(parents=True, exist_ok=True)

    run_state = RunState(
        path=run_dir / "run_status.json",
        history_path=run_dir / "run_history.jsonl",
        recording_name=source.name,
    )

    if completed_run_is_reusable(run_dir, source_hash, config_hash) and not force:
        print(f"Existing complete matching result found. Skipping: {run_dir}", flush=True)
        existing_summary = json.loads((run_dir / "diarisation_summary.json").read_text(encoding="utf-8"))
        return {
            "status": "SKIPPED_EXISTING",
            "source_file": str(source),
            "source_sha256": source_hash,
            "run_dir": str(run_dir),
            "summary": existing_summary,
        }

    run_state.update(
        "PREPARING",
        source_file=str(source),
        source_sha256=source_hash,
        configuration=config,
        configuration_sha256=config_hash,
    )
    run_state.event("RUN_STARTED", source_file=str(source), configuration_sha256=config_hash)

    timings: Dict[str, float] = {}

    try:
        stage = monotonic_seconds()
        print("[2] Reading source metadata...", flush=True)
        media_metadata = ffprobe_metadata(source)
        timings["source_metadata_seconds"] = monotonic_seconds() - stage
        source_duration = extract_duration_seconds(media_metadata)

        canonical_wav = run_dir / f"{safe_stem(source)}_16k_mono.wav"
        if canonical_wav.exists() and canonical_wav.stat().st_size > 44 and not force:
            print("[3] Reusing existing canonical WAV...", flush=True)
        else:
            print("[3] Creating canonical mono 16 kHz PCM WAV...", flush=True)
            run_state.update("PREPARING", current_stage="canonical_wav")
            stage = monotonic_seconds()
            make_canonical_wav(source, canonical_wav)
            timings["canonical_wav_creation_seconds"] = monotonic_seconds() - stage

        print("[4] Hashing and analysing canonical WAV...", flush=True)
        stage = monotonic_seconds()
        canonical_hash = sha256_file(canonical_wav)
        canonical_meta = wav_metadata(canonical_wav)
        audio_quality = analyse_pcm16_wav(canonical_wav)
        timings["canonical_wav_analysis_seconds"] = monotonic_seconds() - stage
        recording_duration = float(canonical_meta.get("duration_seconds") or source_duration or 0.0)

        manifest = {
            "created_utc": utc_now(),
            "source_file": str(source),
            "source_sha256": source_hash,
            "source_size_bytes": source.stat().st_size,
            "source_ffprobe": media_metadata,
            "source_duration_seconds": source_duration,
            "canonical_wav": {
                "file": canonical_wav.name,
                "sha256": canonical_hash,
                "size_bytes": canonical_wav.stat().st_size,
                "metadata": canonical_meta,
            },
            "model_id": model_id,
            "configuration": config,
            "configuration_sha256": config_hash,
            "runtime_environment": environment_manifest(device),
        }
        write_json(run_dir / "source_manifest.json", manifest)

        kwargs: Dict[str, Any] = {}
        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers
        else:
            if min_speakers is not None:
                kwargs["min_speakers"] = min_speakers
            if max_speakers is not None:
                kwargs["max_speakers"] = max_speakers

        print(f"[5] Running {model_id} on {device}...", flush=True)
        run_state.update("DIARISING", current_stage="pipeline_start", speaker_constraints=kwargs)
        run_state.event("DIARISATION_STARTED", speaker_constraints=kwargs)

        if device.type == "cuda" and torch.cuda.is_available():
            try:
                torch.cuda.reset_peak_memory_stats()
            except Exception:
                pass

        progress = PipelineProgressReporter(run_state)
        stage = monotonic_seconds()
        pipeline = pipeline_provider.get()
        output = pipeline(str(canonical_wav), hook=progress, **kwargs)
        timings["diarisation_seconds"] = monotonic_seconds() - stage
        run_state.event("DIARISATION_COMPLETED", diarisation_seconds=round_float(timings["diarisation_seconds"], 3))

        regular = getattr(output, "speaker_diarization", output)
        exclusive = getattr(output, "exclusive_speaker_diarization", None)

        print("[6] Serialising diarisation evidence...", flush=True)
        run_state.update("SERIALISING", current_stage="diarisation_outputs")
        stage = monotonic_seconds()

        regular_rows = annotation_to_rows(regular)
        exclusive_rows = annotation_to_rows(exclusive) if exclusive is not None else []

        write_json(run_dir / "diarisation_regular.json", regular_rows)
        write_diarisation_tsv(run_dir / "diarisation_regular.tsv", regular_rows)
        write_rttm(run_dir / "diarisation_regular.rttm", regular)

        if exclusive is not None:
            write_json(run_dir / "diarisation_exclusive.json", exclusive_rows)
            write_diarisation_tsv(run_dir / "diarisation_exclusive.tsv", exclusive_rows)
            write_rttm(run_dir / "diarisation_exclusive.rttm", exclusive)

        embedding_info = save_speaker_embeddings(run_dir, output, regular, regular_rows)

        analysis = conversation_analysis(
            regular_rows=regular_rows,
            exclusive_rows=exclusive_rows,
            recording_duration=recording_duration,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
            num_speakers=num_speakers,
        )
        analysis["created_utc"] = utc_now()
        analysis["source_file"] = str(source)
        analysis["source_sha256"] = source_hash
        analysis["model_id"] = model_id
        analysis["speaker_constraints"] = kwargs
        analysis["audio_quality"] = audio_quality
        analysis["performance"] = {
            "timings_seconds": {k: round_float(v, 3) for k, v in timings.items()},
            "audio_duration_seconds": round_float(recording_duration),
            "diarisation_realtime_factor": round_float(
                timings.get("diarisation_seconds", 0.0) / recording_duration
                if recording_duration > 0
                else None
            ),
            "pipeline_hook_observations": progress.summary(),
        }
        if device.type == "cuda" and torch.cuda.is_available():
            try:
                analysis["performance"]["peak_gpu_memory_bytes"] = int(torch.cuda.max_memory_allocated())
            except Exception:
                analysis["performance"]["peak_gpu_memory_bytes"] = None
        analysis["speaker_embeddings"] = embedding_info or {
            "available": False,
            "reason": "Installed pipeline output did not expose representative speaker embeddings.",
        }
        analysis["evidence_notes"] = [
            "Machine speaker labels such as SPEAKER_00 are recording-local and are not named identities.",
            "Do not assume the same local label denotes the same person across different recordings.",
            "Retain regular diarisation for overlap evidence.",
            "Use exclusive diarisation preferentially for transcript timestamp reconciliation and non-double-counted talk-time statistics.",
            "Cross-meeting embedding similarity, when present, is supporting evidence for speaker matching and not identity proof.",
        ]
        write_json(run_dir / "diarisation_analysis.json", analysis)

        summary = {
            "created_utc": utc_now(),
            "source_file": str(source),
            "source_sha256": source_hash,
            "model_id": model_id,
            "device": str(device),
            "speaker_constraints": kwargs,
            "regular": legacy_summary(regular_rows),
            "exclusive_available": exclusive is not None,
            "exclusive": legacy_summary(exclusive_rows) if exclusive is not None else None,
            "detected_speaker_count": analysis["detected_speaker_count"],
            "speech_coverage_fraction": analysis["speech"]["speech_coverage_fraction"],
            "overlap_fraction_of_detected_speech": analysis["overlap"]["overlap_fraction_of_detected_speech"],
            "dominant_speaker_share": analysis["speaker_balance"]["dominant_speaker_share"],
            "qc_flag_count": analysis["quality_control"]["flag_count"],
            "diarisation_seconds": round_float(timings.get("diarisation_seconds"), 3),
            "diarisation_realtime_factor": analysis["performance"]["diarisation_realtime_factor"],
            "run_dir": str(run_dir),
            "notes": analysis["evidence_notes"],
        }
        write_json(run_dir / "diarisation_summary.json", summary)

        try:
            write_timeline_svg(
                run_dir / "diarisation_timeline.svg",
                regular_rows,
                recording_duration,
                source.name,
            )
        except Exception as exc:
            run_state.event("TIMELINE_WARNING", message=str(exc))

        timings["serialization_and_analysis_seconds"] = monotonic_seconds() - stage
        timings["total_wall_seconds"] = monotonic_seconds() - batch_start

        if not keep_wav:
            canonical_wav.unlink(missing_ok=True)
            manifest["canonical_wav"]["retained"] = False
            write_json(run_dir / "source_manifest.json", manifest)
        else:
            manifest["canonical_wav"]["retained"] = True
            write_json(run_dir / "source_manifest.json", manifest)

        create_artifact_manifest(run_dir)

        run_state.update(
            "COMPLETE",
            completed_utc=utc_now(),
            current_stage="complete",
            exclusive_available=exclusive is not None,
            detected_speaker_count=analysis["detected_speaker_count"],
            qc_flag_count=analysis["quality_control"]["flag_count"],
            total_wall_seconds=round_float(timings["total_wall_seconds"], 3),
        )
        run_state.event("RUN_COMPLETED", total_wall_seconds=round_float(timings["total_wall_seconds"], 3))

        # Recreate artifact manifest once status has reached COMPLETE so its hash
        # reflects the final run_status contents.
        create_artifact_manifest(run_dir)

        print(f"Finished. Outputs: {run_dir}", flush=True)
        print(f"Regular segments:   {len(regular_rows)}", flush=True)
        print(
            f"Exclusive segments: {len(exclusive_rows) if exclusive is not None else 'not exposed'}",
            flush=True,
        )
        print(f"Detected speakers:  {analysis['detected_speaker_count']}", flush=True)
        print(f"Speech coverage:    {analysis['speech']['speech_coverage_fraction']:.1%}", flush=True)
        print(f"Overlap of speech:  {analysis['overlap']['overlap_fraction_of_detected_speech']:.1%}", flush=True)
        print(f"QC review flags:    {analysis['quality_control']['flag_count']}", flush=True)
        print(f"Diarisation time:   {human_duration(timings.get('diarisation_seconds'))}", flush=True)
        rtf = analysis["performance"]["diarisation_realtime_factor"]
        if isinstance(rtf, (int, float)):
            print(f"Real-time factor:   {rtf:.3f}x", flush=True)

        return {
            "status": "COMPLETE",
            "source_file": str(source),
            "source_sha256": source_hash,
            "run_dir": str(run_dir),
            "summary": summary,
        }

    except Exception as exc:
        failure = {
            "failed_utc": utc_now(),
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "traceback": traceback.format_exc(),
        }
        try:
            run_state.update("FAILED", current_stage=run_state.current.get("current_stage"), **failure)
            run_state.event("RUN_FAILED", exception_type=type(exc).__name__, exception=str(exc))
        except Exception:
            pass
        print(f"FAILED: {source.name}: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run evidence-preserving pyannote speaker diarisation with progress, QC and resumable outputs."
    )
    p.add_argument("inputs", nargs="+", help="Audio/video meeting file(s).")
    p.add_argument(
        "--output-dir",
        default="DIARISATION_OUTPUT",
        help="Root output directory (default: DIARISATION_OUTPUT).",
    )
    p.add_argument(
        "--device",
        choices=["auto", "cuda", "cpu"],
        default="auto",
        help="Processing device (default: auto).",
    )
    p.add_argument(
        "--model",
        default=MODEL_ID,
        help=f"Pyannote pipeline ID or local pipeline path (default: {MODEL_ID}).",
    )

    p.add_argument(
        "--num-speakers",
        type=int,
        help="Exact known speaker count.",
    )
    p.add_argument("--min-speakers", type=int, default=None, help="Minimum expected speaker count.")
    p.add_argument("--max-speakers", type=int, default=None, help="Maximum expected speaker count.")
    p.add_argument(
        "--estimate-speakers",
        action="store_true",
        help="Deprecated compatibility alias. Automatic estimation is already the default when no constraints are supplied.",
    )
    p.add_argument(
        "--delete-working-wav",
        action="store_true",
        help="Delete the generated 16 kHz WAV after successful processing.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Rerun even when an identical completed result already exists.",
    )
    p.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop the batch immediately if one recording fails. Default: continue and report all failures.",
    )

    args = p.parse_args()

    if args.num_speakers is not None and (
        args.min_speakers is not None or args.max_speakers is not None
    ):
        p.error("Use either --num-speakers OR --min-speakers/--max-speakers, not both.")

    if args.estimate_speakers and (
        args.num_speakers is not None
        or args.min_speakers is not None
        or args.max_speakers is not None
    ):
        p.error("--estimate-speakers cannot be combined with explicit speaker constraints.")

    for label, value in [
        ("--num-speakers", args.num_speakers),
        ("--min-speakers", args.min_speakers),
        ("--max-speakers", args.max_speakers),
    ]:
        if value is not None and value < 1:
            p.error(f"{label} must be >= 1.")

    if (
        args.min_speakers is not None
        and args.max_speakers is not None
        and args.min_speakers > args.max_speakers
    ):
        p.error("--min-speakers cannot exceed --max-speakers.")

    if args.estimate_speakers:
        print(
            "Note: --estimate-speakers is deprecated; automatic estimation is now the default.",
            file=sys.stderr,
        )

    return args


def main() -> int:
    args = parse_args()

    output_root = Path(args.output_dir).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    check_command("ffmpeg")
    check_command("ffprobe")

    device = resolve_device(args.device)

    print(f"Script: {Path(__file__).name} v{SCRIPT_VERSION}")
    print(f"Model:  {args.model}")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU:    {torch.cuda.get_device_name(0)}")

    pipeline_provider = PipelineProvider(device=device, model_id=args.model)

    batch_started = monotonic_seconds()
    results: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    for item in args.inputs:
        source = Path(item)
        try:
            result = run_one(
                pipeline_provider=pipeline_provider,
                source=source,
                output_root=output_root,
                device=device,
                model_id=args.model,
                num_speakers=args.num_speakers,
                min_speakers=args.min_speakers,
                max_speakers=args.max_speakers,
                keep_wav=not args.delete_working_wav,
                force=args.force,
            )
            results.append(result)
        except Exception as exc:
            failures.append(
                {
                    "source_file": str(source),
                    "exception_type": type(exc).__name__,
                    "exception": str(exc),
                }
            )
            if args.fail_fast:
                break

    embedding_sets: List[Dict[str, Any]] = []
    for result in results:
        run_dir_value = result.get("run_dir")
        if not run_dir_value:
            continue
        embedding_set = load_embedding_set(Path(run_dir_value), Path(result["source_file"]).name)
        if embedding_set is not None:
            embedding_sets.append(embedding_set)

    similarity = write_cross_meeting_similarity(output_root, embedding_sets)

    batch_summary = {
        "created_utc": utc_now(),
        "script_version": SCRIPT_VERSION,
        "model_id": args.model,
        "device": str(device),
        "speaker_constraints": {
            "num_speakers": args.num_speakers,
            "min_speakers": args.min_speakers,
            "max_speakers": args.max_speakers,
        },
        "total_wall_seconds": round_float(monotonic_seconds() - batch_started, 3),
        "recordings_requested": len(args.inputs),
        "recordings_completed_or_reused": len(results),
        "recordings_failed": len(failures),
        "recordings": results,
        "failures": failures,
        "cross_meeting_embedding_comparison_available": similarity is not None,
        "notes": [
            "A skipped existing run means source hash, configuration hash and core output checks matched a prior COMPLETE run.",
            "Batch exit code is non-zero when any recording failed, even if later recordings were still attempted.",
        ],
    }
    write_json(output_root / "batch_summary.json", batch_summary)

    print("\nBatch complete.")
    print(f"Root output directory: {output_root}")
    print(f"Completed/reused:      {len(results)}")
    print(f"Failed:                {len(failures)}")
    if similarity is not None:
        print("Cross-meeting speaker similarity files: created")

    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
