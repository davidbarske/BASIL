#!/usr/bin/env python3
"""Case-neutral BASIL acoustic enrichment processor.

This is the reusable form of the empirically tested Meeting 02 acoustic pass.
It preserves the acoustic algorithms while removing meeting-specific paths,
participants, source IDs and skill-learning side effects.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import shutil
import sqlite3
import subprocess
import wave
from pathlib import Path
from typing import Any

import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import webrtcvad
from scipy.fft import dct

DEFAULT_SR = 16000
DEFAULT_HOP = 800
DEFAULT_NFFT = 1024
DEFAULT_FRAME_RES_MS = 50
DEFAULT_CHUNK_SEC = 300


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def ffprobe_audio(path: Path) -> tuple[dict[str, Any], float]:
    raw = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    probe = json.loads(raw)
    stream = next(s for s in probe["streams"] if s.get("codec_type") == "audio")
    duration = float(stream.get("duration") or probe["format"]["duration"])
    return stream, duration


def load_vad_flags(wav_path: Path, sr: int, mode: int = 2) -> tuple[np.ndarray, float]:
    if sr != 16000:
        raise ValueError("WebRTC VAD input must currently use 16 kHz PCM WAV")
    vad = webrtcvad.Vad(mode)
    vad_hop = 0.03
    flags: list[bool] = []
    with wave.open(str(wav_path), "rb") as wf:
        if not (wf.getframerate() == sr and wf.getnchannels() == 1 and wf.getsampwidth() == 2):
            raise ValueError("analysis WAV must be 16 kHz, mono, 16-bit PCM")
        n = 480
        while True:
            raw = wf.readframes(n)
            if len(raw) < n * 2:
                break
            try:
                flag = vad.is_speech(raw, sr)
            except Exception:
                flag = False
            flags.append(flag)
    if not flags:
        raise ValueError("analysis WAV produced no complete 30 ms VAD frames")
    return np.asarray(flags, dtype=np.float32), vad_hop


def _vad_prob_for_starts(starts: np.ndarray, vad_flags: np.ndarray, vad_hop: float) -> np.ndarray:
    offs = np.array([0.005, 0.015, 0.025, 0.035, 0.045])
    idx = ((starts[:, None] + offs[None, :]) / vad_hop).astype(int)
    idx = np.clip(idx, 0, len(vad_flags) - 1)
    return vad_flags[idx].mean(axis=1)


def extract_frames(
    wav_path: Path,
    duration: float,
    vad_flags: np.ndarray,
    vad_hop: float,
    run_id: int,
    sr: int = DEFAULT_SR,
    hop: int = DEFAULT_HOP,
    nfft: int = DEFAULT_NFFT,
    frame_res_ms: int = DEFAULT_FRAME_RES_MS,
    chunk_sec: int = DEFAULT_CHUNK_SEC,
    noise_floor_override: float | None = None,
) -> pd.DataFrame:
    mel_basis = librosa.filters.mel(sr=sr, n_fft=nfft, n_mels=40, fmin=50, fmax=7600)
    window = np.hanning(nfft).astype(np.float32)
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    lag_min = max(1, int(sr / 400))
    lag_max = int(sr / 60)

    parts: list[pd.DataFrame] = []
    prev_norm = None
    with sf.SoundFile(str(wav_path)) as snd:
        total = snd.frames
        chunk_frames = int(chunk_sec * sr)
        sample0 = 0
        while sample0 < total:
            read_n = min(chunk_frames + nfft, total - sample0)
            snd.seek(sample0)
            y = snd.read(read_n, dtype="float32", always_2d=False)
            if y.ndim > 1:
                y = y.mean(axis=1)
            nominal = min(chunk_frames, total - sample0)
            nframes = max(0, int(math.ceil(nominal / hop)))
            need = (nframes - 1) * hop + nfft if nframes else 0
            if len(y) < need:
                y = np.pad(y, (0, need - len(y)))
            if nframes == 0:
                break

            raw_frames = librosa.util.frame(y, frame_length=nfft, hop_length=hop)[:, :nframes].T.copy()
            starts = (sample0 + np.arange(nframes) * hop) / sr
            ends = np.minimum(starts + frame_res_ms / 1000, duration)
            vprob = _vad_prob_for_starts(starts, vad_flags, vad_hop)

            rms = np.sqrt(np.mean(raw_frames * raw_frames, axis=1) + 1e-20)
            rms_db = 20 * np.log10(np.maximum(rms, 1e-10))
            peak = np.max(np.abs(raw_frames), axis=1)
            peak_db = 20 * np.log10(np.maximum(peak, 1e-10))
            zcr = np.mean(np.abs(np.diff(np.signbit(raw_frames), axis=1)), axis=1)
            clipping = np.mean(np.abs(raw_frames) >= 0.999, axis=1)

            weighted = raw_frames * window
            spec = np.fft.rfft(weighted, n=nfft, axis=1)
            mag = np.abs(spec) + 1e-12
            power = mag * mag
            sm = mag.sum(axis=1) + 1e-12
            centroid = (mag * freqs).sum(axis=1) / sm
            bandwidth = np.sqrt((mag * ((freqs[None, :] - centroid[:, None]) ** 2)).sum(axis=1) / sm)
            cum = np.cumsum(power, axis=1)
            thr = 0.85 * cum[:, -1]
            ridx = (cum >= thr[:, None]).argmax(axis=1)
            rolloff = freqs[ridx]
            flat = np.exp(np.mean(np.log(mag), axis=1)) / (np.mean(mag, axis=1) + 1e-12)
            norm = mag / (np.linalg.norm(mag, axis=1, keepdims=True) + 1e-12)
            flux = np.zeros(nframes, dtype=np.float32)
            if prev_norm is not None:
                flux[0] = np.linalg.norm(norm[0] - prev_norm)
            if nframes > 1:
                flux[1:] = np.linalg.norm(norm[1:] - norm[:-1], axis=1)
            prev_norm = norm[-1].copy()

            acf = np.fft.irfft(power, n=2 * nfft, axis=1)[:, : lag_max + 1]
            ac0 = np.maximum(acf[:, 0], 1e-12)
            region = acf[:, lag_min : lag_max + 1]
            imax = np.argmax(region, axis=1) + lag_min
            rmax = region[np.arange(nframes), imax - lag_min]
            conf = np.clip(rmax / ac0, 0, 0.999)
            f0 = sr / imax.astype(np.float64)
            voiced = (conf > 0.32) & (vprob >= 0.2) & (rms_db > -65)
            f0 = np.where(voiced, f0, np.nan)
            voiced_prob = np.where(vprob > 0, np.clip((conf - 0.15) / 0.6, 0, 1) * vprob, 0)
            hnr = 10 * np.log10(np.maximum(conf, 1e-6) / np.maximum(1 - conf, 1e-6))
            hnr = np.where(voiced, hnr, np.nan)

            mel = np.maximum(power @ mel_basis.T, 1e-12)
            mfcc = dct(np.log(mel), type=2, axis=1, norm="ortho")[:, :13]

            part = pd.DataFrame(
                {
                    "start_ms": np.rint(starts * 1000).astype(np.int64),
                    "end_ms": np.rint(ends * 1000).astype(np.int64),
                    "rms_dbfs": rms_db,
                    "peak_dbfs": peak_db,
                    "zero_crossing_rate": zcr,
                    "f0_hz": f0,
                    "f0_confidence": conf,
                    "intensity_db": rms_db,
                    "hnr_db": hnr,
                    "spectral_centroid_hz": centroid,
                    "spectral_bandwidth_hz": bandwidth,
                    "spectral_rolloff_hz": rolloff,
                    "spectral_flatness": flat,
                    "spectral_flux": flux,
                    "speech_probability": vprob,
                    "voiced_probability": voiced_prob,
                    "clipping_fraction": clipping,
                }
            )
            for j in range(13):
                part[f"mfcc_{j + 1:02d}"] = mfcc[:, j]
            parts.append(part)
            sample0 += nominal

    frames = pd.concat(parts, ignore_index=True)
    frames = frames[frames.start_ms < int(math.ceil(duration * 1000))].copy()
    non = frames.loc[
        (frames.speech_probability < 0.2) & np.isfinite(frames.rms_dbfs), "rms_dbfs"
    ]
    if len(non) < 100:
        non = frames.rms_dbfs
    noise_floor = float(noise_floor_override) if noise_floor_override is not None else float(np.percentile(non, 25))
    frames["noise_floor_dbfs"] = noise_floor
    frames["snr_db"] = frames["rms_dbfs"] - noise_floor
    frames["frame_resolution_ms"] = frame_res_ms
    frames["run_id"] = run_id
    frames["f1_hz"] = np.nan
    frames["f2_hz"] = np.nan
    frames["f3_hz"] = np.nan
    frames["extra_features_json"] = "{}"
    return frames


def build_second_summaries(
    frames: pd.DataFrame,
    wav_path: Path,
    duration: float,
    run_id: int,
    sr: int = DEFAULT_SR,
) -> pd.DataFrame:
    noise_floor = float(frames["noise_floor_dbfs"].iloc[0])
    rows: list[dict[str, Any]] = []
    with sf.SoundFile(str(wav_path)) as snd:
        for sec in range(int(math.ceil(duration))):
            g = frames[(frames.start_ms >= sec * 1000) & (frames.start_ms < (sec + 1) * 1000)]
            if g.empty:
                continue
            vals = g.f0_hz.dropna().to_numpy()
            formants: list[float | None] = [None, None, None]
            if g.speech_probability.mean() >= 0.25:
                r = g.loc[g.rms_dbfs.idxmax()]
                st = max(0, int(r.start_ms / 1000 * sr))
                snd.seek(min(st, snd.frames - 1))
                x = snd.read(min(800, snd.frames - st), dtype="float64")
                if len(x) >= 400:
                    x = x - np.mean(x)
                    x = np.append(x[0], x[1:] - 0.97 * x[:-1])
                    try:
                        a = librosa.lpc(x, order=12)
                        roots = np.roots(a)
                        roots = roots[np.imag(roots) >= 0]
                        fr = np.sort(np.angle(roots) * sr / (2 * np.pi))
                        fr = fr[(fr > 90) & (fr < 5500)]
                        for i in range(min(3, len(fr))):
                            formants[i] = float(fr[i])
                    except Exception:
                        pass
            snr = float(g.snr_db.mean())
            clip = float(g.clipping_fraction.mean())
            q = float(np.clip((snr + 5) / 35, 0, 1) * (1 - min(1, clip * 100)))
            rows.append(
                {
                    "run_id": run_id,
                    "start_ms": sec * 1000,
                    "end_ms": min((sec + 1) * 1000, int(duration * 1000)),
                    "rms_mean_dbfs": float(g.rms_dbfs.mean()),
                    "rms_max_dbfs": float(g.rms_dbfs.max()),
                    "peak_dbfs": float(g.peak_dbfs.max()),
                    "loudness_short_lufs": None,
                    "f0_median_hz": float(np.median(vals)) if len(vals) else None,
                    "f0_mean_hz": float(np.mean(vals)) if len(vals) else None,
                    "f0_sd_hz": float(np.std(vals)) if len(vals) else None,
                    "f0_min_hz": float(np.min(vals)) if len(vals) else None,
                    "f0_max_hz": float(np.max(vals)) if len(vals) else None,
                    "intensity_mean_db": float(g.intensity_db.mean()),
                    "hnr_mean_db": float(g.hnr_db.dropna().mean()) if g.hnr_db.notna().any() else None,
                    "speech_fraction": float(g.speech_probability.mean()),
                    "voiced_fraction": float(g.voiced_probability.mean()),
                    "silence_fraction": float(1 - g.speech_probability.mean()),
                    "noise_floor_dbfs": noise_floor,
                    "snr_db": snr,
                    "spectral_centroid_mean_hz": float(g.spectral_centroid_hz.mean()),
                    "spectral_flux_mean": float(g.spectral_flux.mean()),
                    "clipping_fraction": clip,
                    "quality_score": q,
                    "extra_features_json": json.dumps(
                        {"f1_hz": formants[0], "f2_hz": formants[1], "f3_hz": formants[2]},
                        separators=(",", ":"),
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_speech_segments(
    vad_flags: np.ndarray, vad_hop: float, duration: float, run_id: int
) -> pd.DataFrame:
    segments: list[list[float]] = []
    start = None
    last = None
    for i, flag in enumerate(vad_flags):
        t0 = i * vad_hop
        t1 = t0 + vad_hop
        if flag:
            if start is None:
                start = t0
            last = t1
        elif start is not None and last is not None:
            segments.append([start, last])
            start = last = None
    if start is not None and last is not None:
        segments.append([start, last])
    merged: list[list[float]] = []
    for s, e in segments:
        if merged and s - merged[-1][1] <= 0.09:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    merged = [x for x in merged if x[1] - x[0] >= 0.15]
    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "start_ms": round(s * 1000),
                "end_ms": round(min(e, duration) * 1000),
                "detector": "webrtcvad",
                "speech_probability": 1.0,
                "status": "DETECTED",
            }
            for s, e in merged
        ]
    )


def build_events(frames: pd.DataFrame, run_id: int) -> pd.DataFrame:
    events: list[dict[str, Any]] = []

    def merge_mask(mask: np.ndarray, event_type: str, score_func, detector: str, min_len_frames: int = 1):
        idx = np.flatnonzero(mask)
        if len(idx) == 0:
            return
        groups = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
        for g in groups:
            if len(g) < min_len_frames:
                continue
            events.append(
                {
                    "run_id": run_id,
                    "start_ms": int(frames.iloc[g[0]].start_ms),
                    "end_ms": int(frames.iloc[g[-1]].end_ms),
                    "event_type": event_type,
                    "severity_or_score": float(score_func(g)),
                    "detector": detector,
                    "metrics_json": "{}",
                    "related_transcript_segments_json": "[]",
                }
            )

    merge_mask(
        (frames.speech_probability < 0.2).to_numpy(),
        "silence_interval",
        lambda g: min(1, len(g) * 0.05 / 5),
        "webrtcvad",
        min_len_frames=40,
    )
    merge_mask(
        (frames.clipping_fraction > 0.001).to_numpy(),
        "clipping",
        lambda g: float(np.clip(frames.iloc[g].clipping_fraction.max() * 100, 0, 1)),
        "pcm_threshold",
    )
    merge_mask(
        (frames.rms_dbfs < -75).to_numpy(),
        "probable_dropout",
        lambda g: min(1, len(g) * 0.05),
        "rms_threshold",
        min_len_frames=2,
    )
    dl = np.abs(np.diff(frames.rms_dbfs.to_numpy(), prepend=frames.rms_dbfs.iloc[0]))
    merge_mask(
        (dl > 18) & (frames.speech_probability.to_numpy() > 0.2),
        "abrupt_loudness_change",
        lambda g: float(min(1, dl[g].max() / 40)),
        "delta_rms",
    )
    return pd.DataFrame(events)


def load_label_map(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("label map must be a JSON object")
    return {str(k).strip().casefold(): str(v).strip() for k, v in data.items()}


def canonical_label(value: Any, label_map: dict[str, str]) -> str | None:
    if value is None or pd.isna(value):
        return None
    raw = str(value).strip()
    if not raw:
        return None
    return label_map.get(raw.casefold(), raw)


def build_method_comparison(
    con: sqlite3.Connection,
    light_path: Path | None,
    run_id: int,
    label_map: dict[str, str],
    light_id_col: str,
    light_label_col: str,
    light_score_col: str,
    light_status_col: str,
) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    if light_path is None:
        return None, {"enabled": False}
    if not (table_exists(con, "attribution_candidates") and table_exists(con, "transcript_segments")):
        return None, {"enabled": False, "reason": "required database tables absent"}

    light = pd.read_csv(light_path, sep="\t")
    required = {light_id_col, light_label_col, light_score_col}
    missing = required - set(light.columns)
    if missing:
        raise ValueError(f"lightweight TSV missing columns: {sorted(missing)}")

    attr = pd.read_sql_query(
        "select attribution_id,start_ms,end_ms,candidate_person_id,status,combined_score,evidence_json "
        "from attribution_candidates order by attribution_id",
        con,
    )
    trans = pd.read_sql_query(
        "select transcript_segment_id,source_segment_id,start_ms,end_ms,original_text "
        "from transcript_segments order by transcript_segment_id",
        con,
    )
    cmp = (
        trans.merge(light, left_on="source_segment_id", right_on=light_id_col, how="left")
        .merge(attr, left_on="transcript_segment_id", right_on="attribution_id", suffixes=("", "_a"))
    )
    cmp["full_name"] = cmp.candidate_person_id.map(lambda x: canonical_label(x, label_map))
    cmp["light_name"] = cmp[light_label_col].map(lambda x: canonical_label(x, label_map))
    cmp["agreement"] = cmp.apply(
        lambda r: bool(r.full_name and r.light_name and r.full_name.casefold() == r.light_name.casefold()), axis=1
    )
    comparable = cmp[cmp.full_name.notna() & cmp.light_name.notna()]
    agreement = float(comparable.agreement.mean()) if len(comparable) else None

    con.execute(
        """CREATE TABLE IF NOT EXISTS method_comparisons (
         comparison_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER, segment_id INTEGER,
         start_ms INTEGER, end_ms INTEGER, method_a TEXT, label_a TEXT, score_a REAL,
         method_b TEXT, label_b TEXT, score_b REAL, agreement INTEGER, evidence_json TEXT)"""
    )
    con.execute("DELETE FROM method_comparisons WHERE run_id=?", (run_id,))
    rows = []
    for _, r in cmp.iterrows():
        status_light = r.get(light_status_col) if light_status_col in cmp.columns else None
        rows.append(
            (
                run_id,
                int(r.transcript_segment_id),
                int(r.start_ms),
                int(r.end_ms),
                "community1_reconciled",
                r.full_name,
                float(r.combined_score or 0),
                "basil_lightweight",
                r.light_name,
                float(r.get(light_score_col) or 0),
                1 if r.agreement else 0,
                json.dumps(
                    {"light_status": None if pd.isna(status_light) else str(status_light), "full_status": str(r.status)},
                    separators=(",", ":"),
                ),
            )
        )
    con.executemany(
        "INSERT INTO method_comparisons(run_id,segment_id,start_ms,end_ms,method_a,label_a,score_a,"
        "method_b,label_b,score_b,agreement,evidence_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    return cmp, {
        "enabled": True,
        "segments": int(len(cmp)),
        "comparable": int(len(comparable)),
        "agreement": agreement,
        "disagreements": int((~comparable.agreement).sum()) if len(comparable) else 0,
    }


def _cos(a: np.ndarray, b: np.ndarray) -> float | None:
    den = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / den) if den > 0 else None


def write_speaker_fingerprints(
    con: sqlite3.Connection,
    frames: pd.DataFrame,
    cmp: pd.DataFrame | None,
    run_id: int,
    attribution_threshold: float = 0.95,
) -> int:
    if cmp is None or not table_exists(con, "speaker_embeddings"):
        return 0
    embed_rows = []
    for _, r in cmp.iterrows():
        person = r.full_name
        if not person or float(r.combined_score or 0) < attribution_threshold:
            continue
        st = int(r.start_ms)
        en = int(r.end_ms)
        if en - st < 2000:
            continue
        g = frames[
            (frames.start_ms >= st)
            & (frames.end_ms <= en)
            & (frames.speech_probability >= 0.4)
        ]
        if len(g) < 20:
            continue
        x = g[[f"mfcc_{i:02d}" for i in range(1, 14)]].to_numpy(np.float32)
        vec = np.concatenate([x.mean(0), x.std(0)]).astype("<f4")
        quality = float(
            np.clip((g.speech_probability.mean() + np.clip(g.snr_db.mean() / 30, 0, 1)) / 2, 0, 1)
        )
        machine_label = None
        try:
            machine_label = json.loads(r.evidence_json).get("machine_speaker")
        except Exception:
            pass
        embed_rows.append(
            (
                run_id,
                st,
                en,
                "BASIL_MFCC_STAT_FINGERPRINT",
                "1.0",
                len(vec),
                "float32",
                vec.tobytes(),
                machine_label,
                person,
                quality,
            )
        )
    con.execute(
        "DELETE FROM speaker_embeddings WHERE run_id=? AND model_name='BASIL_MFCC_STAT_FINGERPRINT'",
        (run_id,),
    )
    if embed_rows:
        con.executemany(
            "INSERT INTO speaker_embeddings(run_id,start_ms,end_ms,model_name,model_version,dimensions,dtype,"
            "embedding_blob,machine_speaker_label,candidate_person_id,quality_score) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            embed_rows,
        )

    if table_exists(con, "speaker_similarity_matrices"):
        con.execute("DELETE FROM speaker_similarity_matrices WHERE run_id=? AND model_name='BASIL_MFCC_STAT_FINGERPRINT'", (run_id,))
        groups: dict[str, list[np.ndarray]] = {}
        for row in embed_rows:
            person = str(row[9])
            vec = np.frombuffer(row[7], dtype="<f4").astype(np.float64)
            groups.setdefault(person, []).append(vec)
        centroids: dict[str, np.ndarray] = {}
        within: dict[str, float | None] = {}
        for person, vectors in groups.items():
            x = np.vstack(vectors)
            centroid = x.mean(axis=0)
            centroids[person] = centroid
            sims = [_cos(v, centroid) for v in x]
            valid = [v for v in sims if v is not None]
            within[person] = float(np.mean(valid)) if valid else None
        people = sorted(groups)
        for person in people:
            con.execute(
                "INSERT INTO speaker_similarity_matrices(run_id,model_name,person_a,person_b,cosine_similarity,"
                "within_a_mean,within_b_mean,between_mean,evidence_count_a,evidence_count_b,data_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    run_id,
                    "BASIL_MFCC_STAT_FINGERPRINT",
                    person,
                    person,
                    1.0,
                    within.get(person),
                    within.get(person),
                    None,
                    len(groups[person]),
                    len(groups[person]),
                    json.dumps({"kind": "within_centroid_stability"}),
                ),
            )
        for i in range(len(people)):
            for j in range(i + 1, len(people)):
                a, b = people[i], people[j]
                sim = _cos(centroids[a], centroids[b])
                con.execute(
                    "INSERT INTO speaker_similarity_matrices(run_id,model_name,person_a,person_b,cosine_similarity,"
                    "within_a_mean,within_b_mean,between_mean,evidence_count_a,evidence_count_b,data_json) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        run_id,
                        "BASIL_MFCC_STAT_FINGERPRINT",
                        a,
                        b,
                        sim,
                        within.get(a),
                        within.get(b),
                        sim,
                        len(groups[a]),
                        len(groups[b]),
                        json.dumps({"kind": "between_centroid_similarity"}),
                    ),
                )
    return len(embed_rows)


def replace_run_rows(con: sqlite3.Connection, table: str, df: pd.DataFrame, run_id: int) -> None:
    if not table_exists(con, table):
        raise RuntimeError(f"required evidence table absent: {table}")
    con.execute(f"DELETE FROM {table} WHERE run_id=?", (run_id,))
    if not df.empty:
        df.to_sql(table, con, if_exists="append", index=False, method="multi", chunksize=500)


def update_processor_metadata(
    con: sqlite3.Connection, run_id: int, duration: float, frame_res_ms: int, nfft: int, hop: int
) -> None:
    if table_exists(con, "processor_status"):
        processors = [
            (
                "webrtcvad",
                "2.0.14",
                None,
                None,
                "COMPLETE",
                {"mode": 2, "frame_ms": 30},
                None,
            ),
            (
                "acoustic_telemetry",
                "numpy/librosa/scipy",
                "BASIL acoustic telemetry",
                "1.0",
                "COMPLETE",
                {"frame_resolution_ms": frame_res_ms, "n_fft": nfft, "hop_samples": hop, "mfcc": 13},
                None,
            ),
            (
                "pitch_hnr",
                "autocorrelation",
                "BASIL autocorrelation F0/HNR proxy",
                "1.0",
                "COMPLETE",
                {"f0_min": 60, "f0_max": 400, "voicing_threshold": 0.32},
                "HNR is an autocorrelation-derived proxy, not Praat harmonicity.",
            ),
            (
                "formant_estimation",
                "librosa LPC",
                "BASIL LPC formants",
                "1.0",
                "COMPLETE",
                {"resolution": "1s representative voiced frame", "lpc_order": 12},
                "Formants are retained in audio_summary_1s.extra_features_json, not as Praat Burg tracks.",
            ),
        ]
        for name, ver, model, model_ver, status, params, note in processors:
            row = con.execute(
                "SELECT processor_status_id FROM processor_status WHERE run_id=? AND processor_name=?",
                (run_id, name),
            ).fetchone()
            values = (ver, model, model_ver, status, json.dumps(params), note)
            if row:
                con.execute(
                    "UPDATE processor_status SET processor_version=?,model_name=?,model_version=?,status=?,"
                    "parameters_json=?,error_or_note=? WHERE processor_status_id=?",
                    values + (row[0],),
                )
            else:
                con.execute(
                    "INSERT INTO processor_status(run_id,processor_name,processor_version,model_name,model_version,"
                    "status,parameters_json,error_or_note) VALUES(?,?,?,?,?,?,?,?)",
                    (run_id, name) + values,
                )
    if table_exists(con, "coverage_status"):
        for name, profile in [
            ("webrtcvad", "ENHANCED"),
            ("acoustic_telemetry", "ENHANCED"),
        ]:
            con.execute("DELETE FROM coverage_status WHERE run_id=? AND processor_name=?", (run_id, name))
            con.execute(
                "INSERT INTO coverage_status(run_id,processor_name,required_by_profile,covered_seconds,expected_seconds,"
                "coverage_fraction,gap_count,overlap_count,status) VALUES(?,?,?,?,?,?,?,?,?)",
                (run_id, name, profile, duration, duration, 1.0, 0, 0, "COMPLETE"),
            )


def run(args: argparse.Namespace) -> dict[str, Any]:
    src_db = Path(args.db_input).resolve()
    out_db = Path(args.db_output).resolve()
    audio = Path(args.audio).resolve()
    wav = Path(args.analysis_wav).resolve()
    light = Path(args.light_segments).resolve() if args.light_segments else None
    label_map_path = Path(args.label_map).resolve() if args.label_map else None

    for p in [src_db, audio, wav] + ([light] if light else []) + ([label_map_path] if label_map_path else []):
        if p is not None and not p.exists():
            raise FileNotFoundError(p)
    if src_db == out_db:
        raise ValueError("db-output must differ from db-input; source evidence is never overwritten")

    shutil.copy2(src_db, out_db)
    source_sha = sha256_file(audio)
    stream, duration = ffprobe_audio(audio)
    vad_flags, vad_hop = load_vad_flags(wav, args.sr, mode=args.vad_mode)
    frames = extract_frames(
        wav,
        duration,
        vad_flags,
        vad_hop,
        args.run_id,
        sr=args.sr,
        hop=args.hop,
        nfft=args.nfft,
        frame_res_ms=args.frame_resolution_ms,
        chunk_sec=args.chunk_sec,
        noise_floor_override=args.noise_floor_dbfs,
    )
    summaries = build_second_summaries(frames, wav, duration, args.run_id, sr=args.sr)
    speech_segments = build_speech_segments(vad_flags, vad_hop, duration, args.run_id)
    events = build_events(frames, args.run_id)

    con = sqlite3.connect(out_db)
    try:
        frame_cols = [
            "run_id",
            "start_ms",
            "end_ms",
            "frame_resolution_ms",
            "rms_dbfs",
            "peak_dbfs",
            "zero_crossing_rate",
            "f0_hz",
            "f0_confidence",
            "intensity_db",
            "hnr_db",
            "f1_hz",
            "f2_hz",
            "f3_hz",
            "spectral_centroid_hz",
            "spectral_bandwidth_hz",
            "spectral_rolloff_hz",
            "spectral_flatness",
            "spectral_flux",
            "speech_probability",
            "voiced_probability",
            "noise_floor_dbfs",
            "snr_db",
            "clipping_fraction",
        ] + [f"mfcc_{i:02d}" for i in range(1, 14)] + ["extra_features_json"]
        replace_run_rows(con, "audio_frames", frames[frame_cols], args.run_id)
        replace_run_rows(con, "audio_summary_1s", summaries, args.run_id)
        replace_run_rows(con, "speech_segments", speech_segments, args.run_id)
        replace_run_rows(con, "audio_events", events, args.run_id)

        label_map = load_label_map(label_map_path)
        cmp, comparison = build_method_comparison(
            con,
            light,
            args.run_id,
            label_map,
            args.light_id_col,
            args.light_label_col,
            args.light_score_col,
            args.light_status_col,
        )
        fingerprints = write_speaker_fingerprints(
            con, frames, cmp, args.run_id, attribution_threshold=args.attribution_threshold
        )
        update_processor_metadata(
            con,
            args.run_id,
            duration,
            args.frame_resolution_ms,
            args.nfft,
            args.hop,
        )
        con.commit()
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        con.close()

    result = {
        "source_sha256": source_sha,
        "source_codec": stream.get("codec_name"),
        "duration_s": duration,
        "frames": int(len(frames)),
        "summaries_1s": int(len(summaries)),
        "speech_segments": int(len(speech_segments)),
        "events": int(len(events)),
        "noise_floor_dbfs": float(frames.noise_floor_dbfs.iloc[0]),
        "speaker_fingerprints": int(fingerprints),
        "comparison": comparison,
        "sqlite_integrity": integrity,
        "output": str(out_db),
        "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if args.summary_json:
        Path(args.summary_json).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Case-neutral BASIL acoustic enrichment processor")
    p.add_argument("--db-input", required=True, help="Existing Interaction Evidence SQLite database")
    p.add_argument("--db-output", required=True, help="New enriched SQLite database; source DB is never overwritten")
    p.add_argument("--audio", required=True, help="Original source audio used for hash/duration/provenance")
    p.add_argument("--analysis-wav", required=True, help="16 kHz mono 16-bit PCM WAV used for acoustic analysis")
    p.add_argument("--run-id", type=int, default=1)
    p.add_argument("--light-segments", help="Optional independent BASIL Lightweight TSV")
    p.add_argument("--label-map", help="Optional JSON alias->canonical speaker label map")
    p.add_argument("--light-id-col", default="segment_id")
    p.add_argument("--light-label-col", default="speaker_basil")
    p.add_argument("--light-score-col", default="speaker_raw_confidence")
    p.add_argument("--light-status-col", default="attribution_status")
    p.add_argument("--attribution-threshold", type=float, default=0.95)
    p.add_argument("--sr", type=int, default=DEFAULT_SR)
    p.add_argument("--hop", type=int, default=DEFAULT_HOP)
    p.add_argument("--nfft", type=int, default=DEFAULT_NFFT)
    p.add_argument("--frame-resolution-ms", type=int, default=DEFAULT_FRAME_RES_MS)
    p.add_argument("--chunk-sec", type=int, default=DEFAULT_CHUNK_SEC)
    p.add_argument("--vad-mode", type=int, choices=[0, 1, 2, 3], default=2)
    p.add_argument("--noise-floor-dbfs", type=float, help="Optional fixed noise floor for reproducibility/subset validation")
    p.add_argument("--summary-json")
    return p


def main() -> int:
    args = parser().parse_args()
    result = run(args)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
