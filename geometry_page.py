import streamlit as st

from particula import analysis as an, geometry as geo
from particula.ui import get_ctx, show

ctx = get_ctx()
notes, bars = ctx["notes"], ctx["bars"]

st.title("Geometry")
st.markdown("Three encodings of the same note table. Colour is pitch class throughout.")
a, b = st.columns(2)
with a:
    weight = st.radio("Weight by", ["duration", "count"], horizontal=True)
    w = an.pitch_class_durations(notes) if weight == "duration" else an.pitch_class_counts(notes)
    show(geo.pitch_class_mandala(w, bars, ctx["order"]))
    st.caption("Spokes: pitch-class weight. Polygons: the best-scoring chord of each bar, lighter for later bars.")
with b:
    show(geo.phyllotaxis(notes))
    st.caption("Notes in chronological order on a Vogel spiral (angle n × 137.5°, radius √n). Size is duration. "
               "The spiral is a space-filling layout; it carries no musical structure.")

st.subheader("Interval curves for one bar")
bar_pick = st.selectbox("Bar", bars["bar"].tolist())
row = bars[bars["bar"] == bar_pick].iloc[0]
in_bar = notes[(notes.start_seconds < row["end"]) & (notes.end_seconds > row["start"])]
midi = in_bar.groupby("pitch_class")["pitch_number"].min().tolist()
if len(midi) >= 2:
    show(geo.lissajous_rosette(midi))
    st.caption("x = sin(f₁t), y = sin(f₂t) for each pair of pitch classes sounding in the bar (equal temperament, "
               "A4 = 440 Hz). Ratios near 3:2 or 5:4 give nearly closed curves; the drift comes from tempering.")
else:
    st.write("Fewer than two pitch classes in this bar.")
