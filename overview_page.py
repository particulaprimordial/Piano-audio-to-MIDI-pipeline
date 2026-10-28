import pandas as pd
import streamlit as st

from particula import analysis as an, geometry as geo
from particula.ui import get_ctx, show

ctx = get_ctx()
notes, s, b, stt = ctx["notes"], ctx["summary"], ctx["beat"], ctx["stats"]

st.title("Overview")
st.caption(f"Source: {ctx['run']['label']}")
st.info("Everything here is estimated from an automatic transcription. Treat it as a hypothesis "
        "to check against the recording.")
for w in ctx["warnings"]:
    st.warning(w)

c = st.columns(5)
c[0].metric("Note events", stt["notes"])
c[1].metric("Range", f"{stt['pitch_min']}–{stt['pitch_max']}")
c[2].metric("Median attack tempo", f"{b['bpm']:.1f} BPM")
nb = s.get("estimated_tempo_bpm")
c[3].metric("Notebook tempo", f"{nb:.1f} BPM" if nb else "n/a")
c[4].metric("Flagged events", int((ctx["flagged"]["n_flags"] > 0).sum()))

show(geo.piano_roll(notes, ctx["flagged"], ctx["grid"]))

left, right = st.columns(2)
with left:
    show(geo.key_bars(ctx["keys"]))
    st.caption("Correlation of pitch-class counts with Krumhansl–Kessler key profiles. A major scale and its "
               "relative minor share their notes, so this ranks note frequency, not harmony.")
with right:
    counts = an.pitch_class_counts(notes).astype(int)
    st.bar_chart(pd.DataFrame({"events": counts}, index=an.PC_NAMES))
    st.caption("Note events per pitch class.")

st.subheader("Pulse over time")
iv = ctx["intervals"].copy()
iv = iv[iv["interval_s"] >= 0.4]
iv["BPM"] = 60.0 / iv["interval_s"]
st.line_chart(iv.set_index("time")["BPM"])
a = ctx["attack"]
st.caption(f"Tempo implied by the interval between attacks: {60/a['first_interval_mean']:.1f} BPM over the first "
           f"8 attacks, {60/a['last_interval_mean']:.1f} BPM over the last 8. A fixed-tempo bar grid drifts "
           "against this; the default grid snaps bars to the attacks.")
