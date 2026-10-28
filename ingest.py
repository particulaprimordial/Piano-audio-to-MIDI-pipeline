"""Turn dropped files (or a run folder) into one run dictionary.

Accepted: note_events.csv or a .mid file (required, one of them); optionally
key_candidates.csv, analysis_summary.json, run_metadata.json, PNG/JPG figures
and audio (.wav .mp3 .m4a .aac .ogg). Anything missing is derived or skipped.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import analysis as an
from .midi_io import NAMES, parse_midi

AUDIO_MIME = {".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4",
              ".aac": "audio/aac", ".ogg": "audio/ogg"}
IMAGE_EXT = (".png", ".jpg", ".jpeg")
ACCEPTED = ["csv", "json", "mid", "midi", "png", "jpg", "jpeg", "wav", "mp3", "m4a", "aac", "ogg"]


def _complete_notes(df: pd.DataFrame) -> pd.DataFrame:
    need = {"pitch_number", "start_seconds", "end_seconds"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError("note table is missing columns: " + ", ".join(sorted(missing)))
    df = df.copy()
    df["pitch_number"] = df["pitch_number"].astype(int)
    if "pitch_class" not in df:
        df["pitch_class"] = df["pitch_number"] % 12
    if "pitch_name" not in df:
        df["pitch_name"] = [f"{NAMES[p % 12]}{p // 12 - 1}" for p in df["pitch_number"]]
    if "duration_seconds" not in df:
        df["duration_seconds"] = (df["end_seconds"] - df["start_seconds"]).round(4)
    if "velocity" not in df:
        df["velocity"] = 64
    df = df.sort_values("start_seconds", kind="stable").reset_index(drop=True)
    if "note_event_id" not in df:
        df.insert(0, "note_event_id", range(1, len(df) + 1))
    if df.empty:
        raise ValueError("the note table is empty")
    return df


def run_from_files(files: dict[str, bytes]) -> dict:
    lower = {k.lower(): k for k in files}
    notes, source = None, None
    for key, orig in lower.items():
        if key.endswith("note_events.csv"):
            notes, source = pd.read_csv(io.BytesIO(files[orig])), orig
            break
    if notes is None:
        for key, orig in lower.items():
            if key.endswith((".mid", ".midi")):
                notes, source = parse_midi(files[orig]), orig
                break
    if notes is None:
        raise ValueError("Drop note_events.csv or a .mid file (at least one is required).")
    notes = _complete_notes(notes)

    def _json(suffix):
        for key, orig in lower.items():
            if key.endswith(suffix):
                try:
                    return json.loads(files[orig].decode("utf-8"))
                except Exception:
                    return {}
        return {}

    keys = None
    for key, orig in lower.items():
        if key.endswith("key_candidates.csv"):
            keys = pd.read_csv(io.BytesIO(files[orig]))
    if keys is None:
        keys = an.key_correlations(an.pitch_class_counts(notes))

    images = {k: v for k, v in files.items() if k.lower().endswith(IMAGE_EXT)}
    audio = [(k, v, AUDIO_MIME[Path(k).suffix.lower()]) for k, v in files.items()
             if Path(k).suffix.lower() in AUDIO_MIME]
    midi = next(((k, v) for k, v in files.items() if k.lower().endswith((".mid", ".midi"))), None)
    meta = _json("run_metadata.json")
    return {"notes": notes, "summary": _json("analysis_summary.json"), "meta": meta,
            "keys": keys, "images": images, "audio": audio, "midi": midi,
            "label": meta.get("original_filename") or Path(source).name,
            "derived": {"keys": not any(k.endswith("key_candidates.csv") for k in lower),
                        "from_midi": source.lower().endswith((".mid", ".midi"))}}


def load_folder(folder: str | Path) -> dict:
    folder = Path(folder)
    files = {p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()}
    return run_from_files(files)
