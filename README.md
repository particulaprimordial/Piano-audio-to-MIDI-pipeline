# Particula Primordial Music Analysis Lab

Dashboard and analysis code for automatically transcribed piano sketches.
Drop the Colab notebook's output files into the sidebar and read the results.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Drag and drop into the sidebar: `note_events.csv` **or** a `.mid` file (one is required). Optional:
`key_candidates.csv`, `analysis_summary.json`, `run_metadata.json`, PNG figures, and audio
(WAV, MP3, M4A, AAC, OGG). Missing pieces are derived or skipped. With nothing dropped, the example run
in `data/` is shown. Dropped files are used in memory only.

## Pages

| Page | Contents |
|---|---|
| Overview | Piano roll with flags and bar lines, key candidates, pitch-class counts, pulse over time |
| Harmony | Chord candidates per bar with ties, transition graph |
| Geometry | Pitch-class mandala, golden-angle spiral, interval Lissajous curves |
| Validation | Transcription artefact checks, flagged events |
| Audio & images | Playback of dropped audio, notebook figures, MIDI download |
| Data & export | Filterable note table, CSV and Markdown report downloads |
| Method & developer | Technical note, environment versions, run metadata, notebook fixes |

## Streamlit categories used

| Category | Used for | Streamlit feature |
|---|---|---|
| Widgets | Drag-and-drop, grid controls | `file_uploader`, `slider`, `radio`, `selectbox`, `download_button` |
| Charts | Pitch classes, pulse over time | `bar_chart`, `line_chart`, `pyplot` |
| Dataframes | Note table, chord table | `dataframe`, `column_config` |
| Graphs | Chord transitions | `graphviz_chart` |
| Images & video | Notebook figures | `image` |
| Audio | Listening while checking notes | `audio` |
| Text | Technical note, captions | `markdown`, `caption` |
| Page navigation | Seven pages | `navigation`, `Page` |
| Developer tools | Versions, metadata | `json`, `code` |
| Code editors | Notebook fix snippets | `code`, `expander` |

Not included: LLMs (the analysis is deterministic by design; an assistant can be added later on top of the
note table), Authentication, Connections, Maps, Molecules & genes, Integrations (nothing in this project needs
them yet). Third-party components from the gallery were not added because they could not be tested offline.

## Layout

```
app.py                      entry point, uploader, navigation
views/                      one script per page
src/particula/analysis.py   key, attacks, bar grids, chord templates, flags
src/particula/midi_io.py    dependency-free MIDI reader
src/particula/ingest.py     dropped files -> run dictionary
src/particula/geometry.py   figures
src/particula/report.py     Markdown run report
data/<run>/                 example run (no audio)
paper/technical_note.md     methods, results, limitations
docs/pipeline_fixes.md      corrections for the Colab notebook
tests/                      unit tests against the example run
```

## Status

Transcription accuracy has not been measured. See `paper/technical_note.md`, section 5.
