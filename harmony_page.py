import streamlit as st

from particula import analysis as an
from particula.ui import get_ctx

ctx = get_ctx()
bars = ctx["bars"]

st.title("Harmony")
st.subheader("Chord candidates per bar")
show = bars.drop(columns="profile")
st.dataframe(
    show, use_container_width=True, hide_index=True,
    column_config={
        "score": st.column_config.ProgressColumn("template match", min_value=0.0, max_value=1.0, format="%.2f"),
        "runner_up_score": st.column_config.ProgressColumn("runner-up match", min_value=0.0, max_value=1.0, format="%.2f"),
        "tied_with": st.column_config.TextColumn("tied within 0.03"),
    })
st.caption("Each bar's pitch-class profile (sounding time inside the bar) is compared with major, minor, "
           "diminished and seventh-chord templates by cosine similarity. Chords listed under 'tied' cannot be "
           "told apart from the notes present, typically because the bar has only two or three pitch classes.")
st.code(" | ".join(bars["best_chord"]), language=None)

if (bars["tied_with"] != "").any():
    st.warning("Bars with tied candidates: " + ", ".join(str(x) for x in bars.loc[bars["tied_with"] != "", "bar"])
               + ". Decide these by ear or from the score.")

st.subheader("Chord transition graph")
st.graphviz_chart(an.chord_graph_dot(bars), use_container_width=True)
st.caption("Nodes: best-scoring chord per bar with the number of bars it holds. Edges: changes between "
           "consecutive bars, labelled with their count.")
