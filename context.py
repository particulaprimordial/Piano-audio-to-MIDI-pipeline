"""Build the analysis context shared by every dashboard page."""
from __future__ import annotations

import numpy as np

from . import analysis as an


def build_context(run: dict, mode: str = "attacks", bpm: float | None = None,
                  t0: float | None = None, beats_per_bar: int = 4, order: str = "chromatic") -> dict:
    notes = run["notes"]
    beat = an.estimate_beat(notes)
    fit = an.fit_grid(notes)
    att = an.attack_grid(notes, beats_per_bar)
    warnings = []
    used = mode
    if mode == "attacks" and not att["regular"]:
        warnings.append("Attack spacing is irregular, so bars are not snapped to attacks; "
                        "a constant-tempo grid is used instead.")
        used = "constant"
    if used == "attacks":
        grid = att["grid"]
    else:
        b = 60.0 / (bpm or fit["bpm"])
        grid = an.bar_grid(t0 if t0 is not None else fit["t0"], b,
                           float(notes["end_seconds"].max()), beats_per_bar)
    bars = an.bar_table(notes, grid)
    flagged = an.flag_events(notes)
    return {"run": run, "notes": notes, "summary": run["summary"], "meta": run["meta"],
            "keys": run["keys"], "beat": beat, "fit": fit, "attack": att, "grid": grid,
            "bars": bars, "flagged": flagged, "mode": used, "order": order,
            "beats_per_bar": beats_per_bar, "stats": an.summary_stats(notes),
            "end_grid": an.end_grid_excess(notes), "warnings": warnings,
            "intervals": an.attack_intervals(notes)}
