"""Minimal Standard MIDI File reader (no external dependencies).

Reads note on/off events and the tempo map and returns a note table with the
same columns the Colab notebook writes to note_events.csv. Controller events
(sustain pedal etc.) are ignored; any pedal extension must already be in the
note lengths, as it is for the piano transcription model's output.
"""
from __future__ import annotations

import struct

import pandas as pd

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _vlq(data: bytes, i: int):
    v = 0
    while True:
        b = data[i]
        i += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, i


def parse_midi(data: bytes) -> pd.DataFrame:
    if data[:4] != b"MThd":
        raise ValueError("Not a Standard MIDI File (missing MThd header).")
    _fmt, ntrk, division = struct.unpack(">HHH", data[8:14])
    if division & 0x8000:
        raise ValueError("SMPTE time division is not supported.")
    i = 8 + struct.unpack(">I", data[4:8])[0]
    tempos = [(0, 500000)]
    raw = []                                  # (track, name, pitch, vel, on_tick, off_tick)
    for t in range(ntrk):
        if data[i:i + 4] != b"MTrk":
            raise ValueError("Corrupt MIDI file (missing MTrk).")
        length = struct.unpack(">I", data[i + 4:i + 8])[0]
        j, end = i + 8, i + 8 + length
        i = end
        tick, status, name = 0, 0, "Unknown"
        open_notes: dict = {}
        while j < end:
            dt, j = _vlq(data, j)
            tick += dt
            b = data[j]
            if b == 0xFF:
                mtype = data[j + 1]
                ln, k = _vlq(data, j + 2)
                body = data[k:k + ln]
                if mtype == 0x51 and ln == 3:
                    tempos.append((tick, int.from_bytes(body, "big")))
                elif mtype == 0x03:
                    name = body.decode("latin-1") or "Unknown"
                j = k + ln
                continue
            if b in (0xF0, 0xF7):
                ln, k = _vlq(data, j + 1)
                j = k + ln
                continue
            if b & 0x80:
                status = b
                j += 1
            kind, ch = status & 0xF0, status & 0x0F
            if kind in (0xC0, 0xD0):
                j += 1
                continue
            d1, d2 = data[j], data[j + 1]
            j += 2
            if kind == 0x90 and d2 > 0:
                open_notes.setdefault((ch, d1), []).append((tick, d2))
            elif kind == 0x80 or (kind == 0x90 and d2 == 0):
                stack = open_notes.get((ch, d1))
                if stack:
                    on_tick, vel = stack.pop(0)
                    raw.append((t, name, d1, vel, on_tick, tick))
    tempos.sort()

    def to_sec(tk: int) -> float:
        sec, last_t, last_us = 0.0, 0, 500000
        for tt, us in tempos:
            if tt >= tk:
                break
            sec += (tt - last_t) * last_us / 1e6 / division
            last_t, last_us = tt, us
        return sec + (tk - last_t) * last_us / 1e6 / division

    rows = []
    for t, name, p, v, a, b in raw:
        s, e = to_sec(a), to_sec(b)
        rows.append({"instrument_index": t, "instrument_name": name, "pitch_number": p,
                     "pitch_name": f"{NAMES[p % 12]}{p // 12 - 1}", "pitch_class": p % 12,
                     "start_seconds": round(s, 4), "end_seconds": round(e, 4),
                     "duration_seconds": round(e - s, 4), "velocity": v})
    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("The MIDI file contains no notes.")
    df = df.sort_values("start_seconds", kind="stable").reset_index(drop=True)
    df.insert(0, "note_event_id", range(1, len(df) + 1))
    return df
