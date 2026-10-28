import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from particula import analysis as an  # noqa: E402

RUN = Path(__file__).resolve().parents[1] / "data" / "example_run_2026-10-28"


def test_key_correlation_matches_notebook():
    r = an.load_run(RUN)
    mine = an.key_correlations(an.pitch_class_counts(r["notes"]))
    nb = r["keys"].set_index("candidate_key")["correlation"]
    got = mine.set_index("candidate_key")["correlation"]
    assert abs(got["C major"] - nb["C major"]) < 1e-6
    assert mine.iloc[0]["candidate_key"] == "C major"


def test_pitch_class_counts_match_csv():
    r = an.load_run(RUN)
    expected = pd.read_csv(RUN / "pitch_distribution.csv")["note_count"].to_numpy()
    assert (an.pitch_class_counts(r["notes"]) == expected).all()


def test_chord_template_exact_triad():
    prof = np.zeros(12)
    prof[[9, 0, 4]] = 1          # A C E
    assert an.chord_candidates(prof)[0][0] == "Am"


def test_beat_estimate_near_61_bpm():
    notes = an.load_run(RUN)["notes"]
    assert 60 < an.estimate_beat(notes)["bpm"] < 64


def test_flags_catch_pre_attack_note_and_sliver():
    notes = an.load_run(RUN)["notes"]
    f = an.flag_events(notes)
    assert f.loc[0, "flag_before_first_attack"]
    assert f["flag_very_short"].sum() == 1


def test_end_grid_excess_is_not_chance():
    ex = an.end_grid_excess(an.load_run(RUN)["notes"])
    assert ex["observed"] > 5 * ex["expected"]


# ---- v1.2 additions
from particula import ingest, context, report  # noqa: E402
from particula.midi_io import parse_midi        # noqa: E402


def test_midi_parser_matches_notebook_csv():
    d = parse_midi((RUN / "piano_transcription.mid").read_bytes())
    c = an.load_run(RUN)["notes"]
    d = d.sort_values(["start_seconds", "pitch_number"]).reset_index(drop=True)
    c = c.sort_values(["start_seconds", "pitch_number"]).reset_index(drop=True)
    assert len(d) == len(c) == 54
    assert (d["pitch_number"] == c["pitch_number"]).all()
    assert np.abs(d["start_seconds"] - c["start_seconds"]).max() < 1e-3
    assert (d["velocity"] == c["velocity"]).all()


def test_attack_grid_puts_chord_changes_on_bar_lines():
    notes = an.load_run(RUN)["notes"]
    a = an.attack_grid(notes)
    assert a["regular"] and len(a["grid"]) == 9
    bars = an.bar_table(notes, a["grid"])
    assert list(bars["best_chord"]) == ["Am", "Am", "F", "F", "C", "C", "G", "G"]
    assert "Bm" in bars.loc[7, "tied_with"]          # bar 8 is a B+D dyad, ambiguous


def test_tempo_accelerates_across_passage():
    a = an.attack_grid(an.load_run(RUN)["notes"])
    assert a["last_interval_mean"] < a["first_interval_mean"]


def test_ingest_requires_notes_and_accepts_midi_alone():
    try:
        ingest.run_from_files({"a.png": b""})
        raise AssertionError("should have raised")
    except ValueError:
        pass
    run = ingest.run_from_files({"x.mid": (RUN / "piano_transcription.mid").read_bytes()})
    assert len(run["notes"]) == 54 and run["derived"]["from_midi"]


def test_report_contains_progression():
    ctx = context.build_context(ingest.load_folder(RUN))
    assert "| 8 | 28.62 | G |" in report.build_report(ctx)
