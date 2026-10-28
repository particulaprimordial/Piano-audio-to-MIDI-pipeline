# Notebook fixes found while reading the first run (2026-10-28)

1. **`transcription_method` is null.** Cell 6 (corrected version) never assigns `TRANSCRIPTION_METHOD`.
   Add after `transcriber.transcribe(...)`:
   ```python
   import piano_transcription_inference as pti
   TRANSCRIPTION_METHOD = "piano-transcription-inference"
   MODEL_VERSION = getattr(pti, "__version__", "unknown")
   ```
   and write both into `run_metadata.json`.

2. **`duration_seconds` is overwritten.** Cell 9 builds `{**metadata, **summary}`; `summary` also has a
   `duration_seconds` key (end of the last MIDI note, 32.5 s) that replaces the audio length from Cell 4.
   Rename the summary key to `midi_end_seconds`, keep `audio_duration_seconds` from the decoded WAV.

3. **Log library versions.** Record `torch`, `librosa`, `noisereduce`, `pretty_midi`, and the
   `piano-transcription-inference` version in `run_metadata.json`; the end-time pattern noted in
   `paper/technical_note.md` cannot be traced to a cause without them.

4. **Run the transcription twice** (original working WAV vs. denoised WAV) and save both MIDI files
   (`piano_transcription_original.mid`, `piano_transcription_denoised.mid`). This is the only way to
   answer whether strength 0.6 helps.

5. **Keep private audio out of the repo.** `original.aac` and `piano_clean.wav` are not copied into `data/`.
   Add `*.aac`, `*.m4a`, `*.wav` to `.gitignore`.
