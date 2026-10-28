import platform
from pathlib import Path

import matplotlib
import numpy
import pandas
import streamlit as st

import particula
from particula.ui import get_ctx

ROOT = Path(__file__).resolve().parent.parent
ctx = get_ctx()

st.title("Method & developer")
note = ROOT / "paper" / "technical_note.md"
if note.exists():
    st.markdown(note.read_text(encoding="utf-8"))

st.divider()
st.subheader("Environment")
st.json({"particula": particula.__version__, "python": platform.python_version(),
         "streamlit": st.__version__, "numpy": numpy.__version__, "pandas": pandas.__version__,
         "matplotlib": matplotlib.__version__})
st.subheader("Run metadata")
st.json(ctx["meta"] or {"note": "no run_metadata.json dropped"}, expanded=False)
fixes = ROOT / "docs" / "pipeline_fixes.md"
if fixes.exists():
    with st.expander("Notebook fixes"):
        st.markdown(fixes.read_text(encoding="utf-8"))
