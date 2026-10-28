import streamlit as st

from particula.ui import get_ctx

ctx = get_ctx()
fl, ex, stt, s, a = ctx["flagged"], ctx["end_grid"], ctx["stats"], ctx["summary"], ctx["attack"]

st.title("Validation")
st.markdown(
    f"- **Note ends on a 0.5 s grid:** {ex['observed']} of {ex['n']} notes end within 2 ms of a multiple of 0.5 s; "
    f"about {ex['expected']:.1f} are expected by chance (binomial tail p = {ex['p_value']:.1e}). Real releases "
    "do not align to a grid, so these end times more likely come from the model or its segmenting.")
st.markdown(
    f"- **Tempo variation:** attack intervals imply {60/a['first_interval_mean']:.1f} BPM at the start and "
    f"{60/a['last_interval_mean']:.1f} BPM at the end. This is in the performance, not a transcription error.")
st.markdown(f"- **MIDI length:** notes run to {stt['midi_end_seconds']:.1f} s. Compare with the audio length; the "
            "notebook's `duration_seconds` field holds the MIDI length (see Method & developer).")
if "transcription_method" in s:
    st.markdown(f"- **Transcription method logged:** `{s.get('transcription_method')}`. "
                "A null value means the notebook did not record which model produced the file.")

cols = [c for c in fl.columns if c.startswith("flag_")]
bad = fl[fl["n_flags"] > 0]
st.subheader(f"Flagged events ({len(bad)})")
st.dataframe(bad[["note_event_id", "pitch_name", "start_seconds", "end_seconds", "velocity"] + cols],
             use_container_width=True, hide_index=True)
st.caption("Flags mark events to check in MuseScore: shorter than 50 ms, velocity below 30, starting more than "
           "0.5 s before the first attack, or ending on the 0.5 s grid. A flag is a suspicion, not a verdict.")
