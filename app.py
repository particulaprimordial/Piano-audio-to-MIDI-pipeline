"""Particula Primordial Music Analysis Lab: Streamlit entry point.

Run:  streamlit run app.py
Drop the notebook's output files into the sidebar (note_events.csv or a .mid file is
required; everything else is optional). With nothing dropped, the example run in data/ is shown.
"""
from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
import particula                                   # noqa: E402
from particula import analysis as an, context, ingest   # noqa: E402

st.set_page_config(page_title="Particula Primordial Lab", page_icon="🌿", layout="wide")

DATA = ROOT / "data"


@st.cache_data(show_spinner=False)
def cached_upload(items: tuple):
    return ingest.run_from_files(dict(items))


@st.cache_data(show_spinner=False)
def cached_folder(path: str):
    return ingest.load_folder(path)


# --------------------------------------------------------------- sidebar
st.sidebar.title("Particula Primordial")
st.sidebar.caption(f"Music analysis lab v{particula.__version__}")

uploads = st.sidebar.file_uploader(
    "Drop run files here", accept_multiple_files=True, type=ingest.ACCEPTED,
    help="Required: note_events.csv or a .mid file. Optional: key_candidates.csv, analysis_summary.json, "
         "run_metadata.json, PNG figures, audio.")

run, source = None, None
if uploads:
    try:
        run = cached_upload(tuple(sorted((u.name, u.getvalue()) for u in uploads)))
        source = "uploaded files"
    except ValueError as exc:
        st.sidebar.error(str(exc))

if run is None:
    folders = sorted(p.name for p in DATA.iterdir() if p.is_dir()) if DATA.exists() else []
    if not folders:
        st.error("No run found. Drop note_events.csv or a .mid file in the sidebar.")
        st.stop()
    pick = st.sidebar.selectbox("Example run", folders, index=len(folders) - 1)
    run = cached_folder(str(DATA / pick))
    source = f"data/{pick}"

st.sidebar.caption(f"Showing: {source}")
if run["derived"]["from_midi"]:
    st.sidebar.info("Note table read from the MIDI file. Metadata and notebook figures are not available.")

fit = an.fit_grid(run["notes"])
mode_label = st.sidebar.radio("Bar grid", ["Snap to attacks", "Constant tempo"],
                              help="Snap places bar lines on the performed attacks (follows tempo changes). "
                                   "Constant tempo uses a fixed BPM.")
bpb = st.sidebar.selectbox("Beats per bar", [3, 4, 5, 6], index=1)
bpm = t0 = None
if mode_label == "Constant tempo":
    bpm = st.sidebar.slider("Tempo (BPM)", 40.0, 140.0, round(fit["bpm"], 1), 0.1)
    t0 = st.sidebar.slider("Bar 1 starts at (s)", 0.0, 8.0, round(fit["t0"], 3), 0.005)
order = st.sidebar.radio("Circle layout", ["chromatic", "fifths"], horizontal=True)

st.session_state["ctx"] = context.build_context(
    run, "attacks" if mode_label == "Snap to attacks" else "constant", bpm, t0, bpb, order)

# ------------------------------------------------------------ navigation
pages = [
    st.Page("views/overview_page.py", title="Overview", icon="🌿", default=True),
    st.Page("views/harmony_page.py", title="Harmony", icon="🎼"),
    st.Page("views/geometry_page.py", title="Geometry", icon="🌀"),
    st.Page("views/validation_page.py", title="Validation", icon="🔬"),
    st.Page("views/media_page.py", title="Audio & images", icon="🔊"),
    st.Page("views/data_page.py", title="Data & export", icon="📊"),
    st.Page("views/method_page.py", title="Method & developer", icon="🧰"),
]
st.navigation(pages).run()
