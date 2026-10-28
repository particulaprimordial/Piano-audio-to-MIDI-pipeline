"""Figures for the dashboard.

Geometric encodings used here are ordinary mathematics applied to the note
table: polar coordinates (pitch-class circle), the golden angle (Vogel
phyllotaxis) and frequency-ratio curves (Lissajous). They are visual
encodings of measured data, not claims about the music's meaning.
"""
from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle
from matplotlib.collections import LineCollection

from .analysis import PC_NAMES, CHORD_TEMPLATES

# Palette: warm paper on deep green-black, one hue per pitch class
BG = "#0f1a14"
INK = "#e8e2d0"
MUTED = "#8a9a8c"
GOLD = "#d9b45a"
PHI = (1 + 5 ** 0.5) / 2
GOLDEN_ANGLE = 2 * np.pi * (1 - 1 / PHI)          # ~137.508 degrees
import colorsys
PC_COLORS = [colorsys.hsv_to_rgb(i / 12, 0.55, 0.92) for i in range(12)]


def _style(fig, ax):
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color(MUTED)
    ax.tick_params(colors=MUTED)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)
    ax.title.set_color(INK)


def circle_order(order: str = "chromatic") -> list[int]:
    """Pitch-class placement around the circle: chromatic or circle of fifths."""
    return list(range(12)) if order == "chromatic" else [(7 * i) % 12 for i in range(12)]


def _pos(pc: int, order: list[int]) -> float:
    return np.pi / 2 - 2 * np.pi * order.index(pc) / 12      # C at the top, clockwise


# ------------------------------------------------------------- piano roll
def piano_roll(notes, flagged=None, grid=None, t_max=None):
    fig, ax = plt.subplots(figsize=(11, 4.6))
    _style(fig, ax)
    for i, r in notes.iterrows():
        bad = flagged is not None and bool(flagged.loc[i, "n_flags"])
        ax.add_patch(Rectangle((r.start_seconds, r.pitch_number - 0.4),
                               max(r.duration_seconds, 0.03), 0.8,
                               facecolor=PC_COLORS[int(r.pitch_class)],
                               edgecolor="white" if bad else "none",
                               linewidth=1.4 if bad else 0, alpha=0.85))
    if grid is not None:
        for g in grid:
            ax.axvline(g, color=GOLD, lw=0.6, alpha=0.35)
    ax.set_xlim(0, t_max or notes.end_seconds.max())
    ax.set_ylim(notes.pitch_number.min() - 2, notes.pitch_number.max() + 3)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("MIDI pitch")
    ax.set_title("Transcribed notes (white outline = flagged for manual check; gold lines = bar grid)",
                 fontsize=10)
    ax.grid(alpha=0.12, color=MUTED)
    fig.tight_layout()
    return fig


# ------------------------------------------------ pitch-class mandala
def pitch_class_mandala(pc_weights, bars=None, order="chromatic", show_bars=True):
    """Polar view of the pitch-class distribution with per-bar chord polygons."""
    o = circle_order(order)
    fig, ax = plt.subplots(figsize=(6.4, 6.4), subplot_kw={"aspect": "equal"})
    _style(fig, ax)
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.axis("off")
    for rad in (0.33, 0.66, 1.0):
        ax.add_patch(Circle((0, 0), rad, fill=False, ec=MUTED, lw=0.5, alpha=0.4))
    w = np.asarray(pc_weights, float)
    w = w / w.max() if w.max() else w

    if show_bars and bars is not None:
        n = max(len(bars), 1)
        for i, row in bars.iterrows():
            tpl = _chord_pcs(row["best_chord"])
            if len(tpl) < 3:
                continue
            pts = [(np.cos(_pos(pc, o)), np.sin(_pos(pc, o))) for pc in sorted(tpl, key=o.index)]
            ax.add_patch(Polygon(pts, closed=True, fill=True,
                                 fc=plt.cm.YlGn(0.35 + 0.6 * i / n), alpha=0.16,
                                 ec=GOLD, lw=0.7))
    for pc in range(12):
        a = _pos(pc, o)
        r = 0.08 + 0.92 * w[pc]
        ax.plot([0, np.cos(a) * r], [0, np.sin(a) * r], color=PC_COLORS[pc], lw=6,
                solid_capstyle="round", alpha=0.9)
        ax.text(1.17 * np.cos(a), 1.17 * np.sin(a), PC_NAMES[pc], color=INK,
                ha="center", va="center", fontsize=11)
        ax.plot(np.cos(a), np.sin(a), "o", ms=3, color=MUTED)
    ax.set_title("Pitch-class mandala" + (" (circle of fifths)" if order != "chromatic" else ""),
                 color=INK, fontsize=11)
    return fig


def _chord_pcs(label: str) -> list[int]:
    if not label:
        return []
    root = label[:2] if len(label) > 1 and label[1] == "#" else label[:1]
    suffix = label[len(root):]
    if root not in PC_NAMES or suffix not in CHORD_TEMPLATES:
        return []
    r = PC_NAMES.index(root)
    return [(r + iv) % 12 for iv in CHORD_TEMPLATES[suffix]]


# ------------------------------------------------------ phyllotaxis
def phyllotaxis(notes, size_by="duration_seconds"):
    """Each note event placed on a Vogel spiral (angle n * 137.5 deg, radius c*sqrt(n)).

    Order is chronological, colour is pitch class, size is note duration. The
    spiral carries no musical meaning; it is a space-filling layout in which
    every event stays visible.
    """
    d = notes.sort_values("start_seconds").reset_index(drop=True)
    n = np.arange(1, len(d) + 1)
    r = np.sqrt(n)
    th = n * GOLDEN_ANGLE
    s = d[size_by].to_numpy()
    s = 40 + 520 * (s - s.min()) / (np.ptp(s) or 1)
    fig, ax = plt.subplots(figsize=(6.4, 6.4), subplot_kw={"aspect": "equal"})
    _style(fig, ax)
    ax.axis("off")
    ax.scatter(r * np.cos(th), r * np.sin(th), s=s,
               c=[PC_COLORS[int(p)] for p in d.pitch_class], alpha=0.85,
               edgecolors=INK, linewidths=0.4)
    ax.set_title("Phyllotaxis of note events (chronological, golden angle)",
                 color=INK, fontsize=11)
    return fig


# -------------------------------------------------------- Lissajous
def midi_to_hz(m, a4=440.0):
    return a4 * 2 ** ((np.asarray(m, float) - 69) / 12)


def lissajous_rosette(midi_notes, a4=440.0, points=6000):
    """Lissajous curve x=sin(f1 t), y=sin(f2 t) for every pair of chord tones.

    Equal-tempered ratios are slightly irrational, so most curves never close
    exactly; the drift is visible and is the real physical content.
    """
    midi_notes = sorted(set(int(m) for m in midi_notes))
    pairs = [(a, b) for i, a in enumerate(midi_notes) for b in midi_notes[i + 1:]]
    k = max(1, len(pairs))
    cols = int(np.ceil(np.sqrt(k)))
    rows = int(np.ceil(k / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(2.2 * cols + 0.5, 2.2 * rows + 0.5))
    fig.patch.set_facecolor(BG)
    axes = np.atleast_1d(axes).ravel()
    t = np.linspace(0, 2 * np.pi, points)
    for ax, (a, b) in zip(axes, pairs):
        fa, fb = midi_to_hz([a, b], a4)
        # normalise to the interval ratio so the figure is independent of register
        ratio = fb / fa
        ax.set_facecolor(BG)
        ax.plot(np.sin(t * 40), np.sin(t * 40 * ratio), color=GOLD, lw=0.5, alpha=0.8)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(MUTED)
        ax.set_title(f"{_nm(a)}–{_nm(b)}  {ratio:.3f}", color=INK, fontsize=8)
    for ax in axes[len(pairs):]:
        ax.axis("off")
    fig.tight_layout()
    return fig


def _nm(m):
    return f"{PC_NAMES[m % 12]}{m // 12 - 1}"


# ------------------------------------------------------- key bars
def key_bars(keys, top=8):
    k = keys.head(top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    _style(fig, ax)
    ax.barh(k.candidate_key, k.correlation, color=GOLD, alpha=0.85)
    ax.set_xlabel("correlation with key profile")
    ax.set_title("Key candidates (heuristic)", fontsize=10)
    ax.grid(axis="x", alpha=0.12, color=MUTED)
    fig.tight_layout()
    return fig
