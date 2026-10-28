"""Deterministic run report (Markdown). Every number comes from the note table."""
from __future__ import annotations

from . import analysis as an


def build_report(ctx: dict) -> str:
    s, b, a, eg = ctx["stats"], ctx["beat"], ctx["attack"], ctx["end_grid"]
    bars, keys, fl = ctx["bars"], ctx["keys"], ctx["flagged"]
    top = keys.head(3)
    lines = [f"# Run report: {ctx['run']['label']}", "",
             "Estimates from an automatic transcription; check against the recording.", "",
             "## Summary", "",
             "| Quantity | Value |", "|---|---|",
             f"| Note events | {s['notes']} |",
             f"| Range | {s['pitch_min']}–{s['pitch_max']} ({s['span_semitones']} semitones) |",
             f"| MIDI length | {s['midi_end_seconds']:.1f} s |",
             f"| Attacks | {a['n_attacks']} |",
             f"| Median attack interval | {b['beat_seconds']:.3f} s ({b['bpm']:.1f} BPM) |",
             f"| Interval, first 8 vs last 8 attacks | {60/a['first_interval_mean']:.1f} → {60/a['last_interval_mean']:.1f} BPM |",
             f"| Mean / median note duration | {s['duration_mean']:.2f} s / {s['duration_median']:.2f} s |",
             f"| Bar grid | {ctx['mode']}, {ctx['beats_per_bar']} beats per bar |", "",
             "## Key candidates (pitch-class correlation)", ""]
    for _, r in top.iterrows():
        lines.append(f"- {r['candidate_key']}: {r['correlation']:.3f}")
    lines += ["", "## Chord candidates per bar", "", "| Bar | Start (s) | Best | Score | Tied within 0.03 |", "|---|---|---|---|---|"]
    for _, r in bars.iterrows():
        lines.append(f"| {r['bar']} | {r['start']} | {r['best_chord']} | {r['score']:.2f} | {r['tied_with']} |")
    lines += ["", "## Quality flags", "",
              f"- Events flagged: {int((fl['n_flags'] > 0).sum())} of {len(fl)}",
              f"- Note ends on a 0.5 s grid: {eg['observed']} observed, {eg['expected']:.1f} expected by chance "
              f"(p = {eg['p_value']:.1e})"]
    return "\n".join(lines) + "\n"
