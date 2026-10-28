import streamlit as st

from particula.report import build_report
from particula.ui import get_ctx

ctx = get_ctx()
notes = ctx["notes"]

st.title("Data & export")
lo, hi = int(notes.pitch_number.min()), int(notes.pitch_number.max())
rng = st.slider("Pitch range (MIDI number)", lo, hi, (lo, hi))
view = notes[(notes.pitch_number >= rng[0]) & (notes.pitch_number <= rng[1])]
st.dataframe(view, use_container_width=True, hide_index=True,
             column_config={"velocity": st.column_config.ProgressColumn("velocity", min_value=0, max_value=127)})

c = st.columns(3)
c[0].download_button("note_events.csv", notes.to_csv(index=False), "note_events.csv", "text/csv")
c[1].download_button("bar_chords.csv", ctx["bars"].drop(columns="profile").to_csv(index=False),
                     "bar_chords.csv", "text/csv")
c[2].download_button("run_report.md", build_report(ctx), "run_report.md", "text/markdown")
with st.expander("Run report preview"):
    st.markdown(build_report(ctx))
