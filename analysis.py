"""Symbolic analysis of a transcribed piano run.

Everything here is deterministic: the same note table always gives the same
output. Estimates (key, chords, tempo) are labelled as estimates; none of them
replaces listening to the recording or checking the score.
"""
from __future__ import annotations

import json
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

PC_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Krumhansl-Kessler (1982) probe-tone profiles, index 0 = tonic.
KK_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KK_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

CHORD_TEMPLATES = {
    "": (0, 4, 7),
    "m": (0, 3, 7),
    "dim": (0, 3, 6),
    "7": (0, 4, 7, 10),
    "maj7": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10),
}


# ----------------------------------------------------------------- loading
def load_run(folder: str | Path) -> dict:
    """Read the files written by the Colab notebook (V1 layout)."""
    folder = Path(folder)
    return {
        "notes": pd.read_csv(folder / "note_events.csv"),
        "summary": json.loads((folder / "analysis_summary.json").read_text()),
        "meta": json.loads((folder / "run_metadata.json").read_text()),
        "keys": pd.read_csv(folder / "key_candidates.csv"),
        "folder": folder,
    }


# --------------------------------------------------------------- pitch data
def pitch_class_counts(notes: pd.DataFrame) -> np.ndarray:
    return np.bincount(notes["pitch_class"].astype(int), minlength=12).astype(float)


def pitch_class_durations(notes: pd.DataFrame) -> np.ndarray:
    out = np.zeros(12)
    for pc, d in zip(notes["pitch_class"], notes["duration_seconds"]):
        out[int(pc)] += d
    return out


def key_correlations(pc_hist: np.ndarray) -> pd.DataFrame:
    """Pearson correlation of a pitch-class histogram with all 24 key profiles."""
    rows = []
    for tonic in range(12):
        for mode, prof in (("major", KK_MAJOR), ("minor", KK_MINOR)):
            r = np.corrcoef(pc_hist, np.roll(prof, tonic))[0, 1]
            rows.append({"candidate_key": f"{PC_NAMES[tonic]} {mode}", "correlation": r})
    return pd.DataFrame(rows).sort_values("correlation", ascending=False).reset_index(drop=True)


# ------------------------------------------------------------------ timing
def onset_clusters(notes: pd.DataFrame, tol: float = 0.08) -> pd.DataFrame:
    """Group note starts within `tol` seconds (one attack = one cluster)."""
    starts = np.sort(notes["start_seconds"].to_numpy())
    groups, cur = [], [starts[0]]
    for s in starts[1:]:
        if s - cur[-1] <= tol:
            cur.append(s)
        else:
            groups.append(cur)
            cur = [s]
    groups.append(cur)
    return pd.DataFrame({"onset": [float(np.median(g)) for g in groups],
                         "n_notes": [len(g) for g in groups]})


def estimate_beat(notes: pd.DataFrame, min_gap: float = 0.4) -> dict:
    """Beat period from the median inter-onset interval of attack clusters.

    Assumes the melody moves in quarter notes. This is an estimate and is
    reported next to, not instead of, the notebook's beat-tracker tempo.
    """
    clusters = onset_clusters(notes)
    ioi = np.diff(clusters["onset"].to_numpy())
    ioi = ioi[ioi >= min_gap]
    period = float(np.median(ioi))
    return {"beat_seconds": period, "bpm": 60.0 / period,
            "ioi_mad": float(np.median(np.abs(ioi - period))), "n_intervals": int(len(ioi))}


def first_attack(notes: pd.DataFrame, min_notes: int = 2) -> float:
    c = onset_clusters(notes)
    return float(c.loc[c["n_notes"] >= min_notes, "onset"].iloc[0])


def fit_grid(notes: pd.DataFrame, iters: int = 4) -> dict:
    """Least-squares fit of attack times to a regular beat grid.

    A fixed tempo from the median interval drifts over a long passage; fitting
    onset = t0 + k * beat to all on-beat attacks removes most of that drift.
    Attacks further than a quarter beat from the grid are ignored in the fit.
    """
    clusters = onset_clusters(notes)
    on = clusters["onset"].to_numpy()
    t0 = first_attack(notes)
    beat = estimate_beat(notes)["beat_seconds"]
    sel = on[on >= t0 - 0.2]
    ok = np.ones(len(sel), bool)
    for _ in range(iters):
        k = np.round((sel - t0) / beat)
        ok = np.abs(sel - (t0 + k * beat)) < 0.25 * beat
        if ok.sum() < 3:
            break
        A = np.vstack([k[ok], np.ones(ok.sum())]).T
        beat, t0 = np.linalg.lstsq(A, sel[ok], rcond=None)[0]
    k = np.round((sel[ok] - t0) / beat)
    rms = float(np.sqrt(np.mean((sel[ok] - (t0 + k * beat)) ** 2)))
    return {"beat_seconds": float(beat), "bpm": float(60.0 / beat), "t0": float(t0),
            "rms_seconds": rms, "n_attacks": int(ok.sum())}


def attack_grid(notes: pd.DataFrame, beats_per_bar: int = 4) -> dict:
    """Bar boundaries snapped to the performed attacks (every `beats_per_bar`-th attack).

    Assumes one attack per beat from the first chord on. If the attack spacing is
    irregular (gaps or doubled attacks), `regular` is False and the caller should
    use a constant-tempo grid instead.
    """
    c = onset_clusters(notes)
    t0 = first_attack(notes)
    on = c.loc[c["onset"] >= t0 - 0.05, "onset"].to_numpy()
    ioi = np.diff(on)
    med = float(np.median(ioi))
    regular = bool(ioi.max() < 1.5 * med and ioi.min() > 0.5 * med)
    end = float(notes["end_seconds"].max())
    bars = list(on[::beats_per_bar])
    grid = np.array(bars + [end]) if bars[-1] < end else np.array(bars)
    # slope of the attack interval over time, seconds per second
    slope = float(np.polyfit(on[1:], ioi, 1)[0]) if len(ioi) > 2 else 0.0
    return {"grid": grid, "regular": regular, "n_attacks": int(len(on)),
            "first_interval_mean": float(ioi[:8].mean()), "last_interval_mean": float(ioi[-8:].mean()),
            "interval_slope": slope}


def attack_intervals(notes: pd.DataFrame) -> pd.DataFrame:
    c = onset_clusters(notes)
    return pd.DataFrame({"time": c["onset"].iloc[1:].to_numpy(),
                         "interval_s": np.diff(c["onset"].to_numpy())})


def chord_graph_dot(bars: pd.DataFrame) -> str:
    """Graphviz DOT for the bar-to-bar chord sequence (nodes: chords, edges: changes)."""
    seq = [c for c in bars["best_chord"] if c]
    held = {}
    for c in seq:
        held[c] = held.get(c, 0) + 1
    edges = {}
    for a, b in zip(seq, seq[1:]):
        if a != b:
            edges[(a, b)] = edges.get((a, b), 0) + 1
    lines = ["digraph G {", "rankdir=LR;", 'bgcolor="transparent";',
             'node [shape=circle, style=filled, fillcolor="#17261d", color="#d9b45a", '
             'fontcolor="#e8e2d0", fontname="serif"];',
             'edge [color="#8a9a8c", fontcolor="#8a9a8c", fontname="serif"];']
    for c, n in held.items():
        lines.append(f'"{c}" [label="{c}\n{n} bar{"s" if n > 1 else ""}"];')
    for (a, b), n in edges.items():
        lines.append(f'"{a}" -> "{b}" [label="{n}", penwidth={1 + n}];')
    lines.append("}")
    return "\n".join(lines)


def bar_grid(t0: float, beat: float, end: float, beats_per_bar: int = 4) -> np.ndarray:
    bar = beat * beats_per_bar
    n = int(np.ceil((end - t0) / bar))
    return t0 + bar * np.arange(n + 1)


# ------------------------------------------------------------------- chords
def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def bar_pitch_class_profile(notes: pd.DataFrame, t0: float, t1: float) -> np.ndarray:
    prof = np.zeros(12)
    for pc, s, e in zip(notes["pitch_class"], notes["start_seconds"], notes["end_seconds"]):
        prof[int(pc)] += _overlap(s, e, t0, t1)
    return prof


def chord_candidates(profile: np.ndarray, top: int = 3) -> list[tuple[str, float]]:
    """Rank chord labels by cosine similarity to binary chord templates."""
    if profile.sum() == 0:
        return []
    scored = []
    for root in range(12):
        for suffix, ivs in CHORD_TEMPLATES.items():
            tpl = np.zeros(12)
            for iv in ivs:
                tpl[(root + iv) % 12] = 1
            sim = float(profile @ tpl / (np.linalg.norm(profile) * np.linalg.norm(tpl)))
            scored.append((f"{PC_NAMES[root]}{suffix}", sim))
    scored.sort(key=lambda x: -x[1])
    return scored[:top]


def bar_table(notes: pd.DataFrame, grid: np.ndarray) -> pd.DataFrame:
    rows = []
    for i in range(len(grid) - 1):
        t0, t1 = grid[i], grid[i + 1]
        prof = bar_pitch_class_profile(notes, t0, t1)
        cands = chord_candidates(prof, top=24)
        tied = [c for c, sc in cands[1:] if cands and sc >= cands[0][1] - 0.03]
        cands = cands[:3]
        rows.append({
            "bar": i + 1, "start": round(float(t0), 2), "end": round(float(t1), 2),
            "best_chord": cands[0][0] if cands else "",
            "score": round(cands[0][1], 3) if cands else 0.0,
            "runner_up": cands[1][0] if len(cands) > 1 else "",
            "runner_up_score": round(cands[1][1], 3) if len(cands) > 1 else 0.0,
            "tied_with": ", ".join(tied),
            "profile": prof / prof.sum() if prof.sum() else prof,
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------- QC flags
def flag_events(notes: pd.DataFrame, min_duration: float = 0.05, low_velocity: int = 30,
                early_gap: float = 0.5, grid: float = 0.5, grid_tol: float = 0.002) -> pd.DataFrame:
    """Mark events that deserve a manual check. Flags are suspicions, not verdicts."""
    d = notes.copy()
    t_first = first_attack(d)
    d["flag_very_short"] = d["duration_seconds"] < min_duration
    d["flag_low_velocity"] = d["velocity"] < low_velocity
    d["flag_before_first_attack"] = d["start_seconds"] < t_first - early_gap
    r = np.abs(d["end_seconds"] / grid - np.round(d["end_seconds"] / grid)) * grid
    d["flag_end_on_half_second"] = r < grid_tol
    cols = [c for c in d.columns if c.startswith("flag_")]
    d["n_flags"] = d[cols].sum(axis=1)
    return d


def end_grid_excess(notes: pd.DataFrame, grid: float = 0.5, tol: float = 0.002) -> dict:
    """Observed vs chance count of note ends landing on a 0.5 s grid (binomial tail)."""
    r = np.abs(notes["end_seconds"] / grid - np.round(notes["end_seconds"] / grid)) * grid
    observed = int((r < tol).sum())
    p = 2 * tol / grid
    n = len(notes)
    p_val = sum(comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(observed, n + 1))
    return {"n": n, "observed": observed, "expected": n * p, "p_value": float(p_val)}


def summary_stats(notes: pd.DataFrame) -> dict:
    d = notes["duration_seconds"]
    lo, hi = notes["pitch_number"].idxmin(), notes["pitch_number"].idxmax()
    return {
        "notes": int(len(notes)),
        "pitch_min": notes.loc[lo, "pitch_name"], "pitch_max": notes.loc[hi, "pitch_name"],
        "span_semitones": int(notes["pitch_number"].max() - notes["pitch_number"].min()),
        "midi_end_seconds": float(notes["end_seconds"].max()),
        "duration_mean": float(d.mean()), "duration_median": float(d.median()),
        "velocity_mean": float(notes["velocity"].mean()),
    }
