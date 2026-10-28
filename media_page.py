import streamlit as st

run = st.session_state["ctx"]["run"]

st.title("Audio & images")
if run["audio"]:
    st.subheader("Audio")
    for name, data, mime in run["audio"]:
        st.caption(name)
        st.audio(data, format=mime)
    st.caption("Browsers differ in support for raw .aac files; WAV and MP3 are the safe choices.")
else:
    st.caption("No audio dropped. Add a WAV, MP3 or M4A in the sidebar to listen while checking notes.")

if run["images"]:
    st.subheader("Figures")
    for name, data in sorted(run["images"].items()):
        st.image(data, caption=name, use_container_width=True)

if run["midi"]:
    st.subheader("MIDI")
    st.download_button("Download " + run["midi"][0], run["midi"][1], run["midi"][0], "audio/midi")
