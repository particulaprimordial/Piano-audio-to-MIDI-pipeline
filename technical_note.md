# Note-Level Analysis of an Automatically Transcribed Piano Sketch

Technical note v0.3 (working draft). Author: Particula. Status: single-recording case study; no reference transcription yet.

## Abstract

A 32-second phone recording of a solo piano sketch was converted to MIDI with a pretrained piano
transcription model and analysed from the resulting note table. The transcription contains 54 note
events spanning C2–E5 and uses only the seven diatonic pitch classes. Pitch-class statistics favour
C major (r = 0.949 against the Krumhansl–Kessler profile). A bar-by-bar template match, with bar lines
placed on the performed attacks, gives the sequence Am–Am–F–F–C–C–G–G, with the last bar ambiguous
between G, Bm and two diminished triads. The chord pattern fits vi–IV–I–V in C major or i–VI–III–VII in
A minor, so the tonal centre is not settled by the data. The pulse rises from about 60 to 63 BPM over the
passage. Eleven of 54 note end times fall within 2 ms of a multiple of 0.5 s, against 0.4 expected by
chance, and one quiet note begins 1.5 s before the first audible attack. These point to transcription
artefacts. No accuracy figure can be given until a hand-corrected reference exists.

## 1. Introduction

Automatic music transcription (AMT) estimates note events (pitch, onset, offset) from audio
(Benetos et al., 2019). For a composer working from phone sketches, the output is a draft to be corrected
in notation software. This note documents one run of such a workflow and states what can and cannot be
concluded from it.

## 2. Methods

**Recording.** Phone recording, AAC, decoded to mono 44.1 kHz 24-bit PCM with FFmpeg.

**Noise reduction.** Stationary spectral gating (`noisereduce`), `prop_decrease = 0.6`. The effect on
transcription was not tested in this run.

**Transcription.** Pretrained piano model of Kong et al. (2021), via `piano-transcription-inference`.
Device and library versions were not logged. Output: one MIDI track.

**Note table.** The notebook parses the MIDI with `pretty_midi` (54 rows). The dashboard also contains an
independent dependency-free MIDI reader; on this file it returns the same 54 notes with identical pitches,
velocities and start times (maximum difference 0 ms at the CSV's 0.1 ms precision).

**Key estimate.** Pearson correlation between the pitch-class count vector and the 24 rotated
Krumhansl–Kessler profiles (Krumhansl, 1990). The implementation reproduces the notebook's value for
C major (0.9486).

**Attacks and bars.** Note starts within 80 ms are merged into attacks (29 attacks from the first chord
onward). The melody moves in quarter notes, so each attack is taken as one beat and bar lines are placed on
every fourth attack. Attack spacing was checked for regularity (no gap above 1.5× or below 0.5× the median).
A fixed-tempo alternative (least-squares fit of attack times to a regular grid) is available for comparison.

**Chord labels.** For each bar, a pitch-class profile weighted by sounding time is compared by cosine
similarity with binary templates (major, minor, diminished, dominant 7th, major 7th, minor 7th). Candidates
within 0.03 of the best score are reported as tied.

**Quality flags.** Events are flagged if shorter than 50 ms, quieter than velocity 30, starting more than
0.5 s before the first attack, or ending within 2 ms of a multiple of 0.5 s. For the last flag the number of
hits is compared with the binomial expectation for uniformly distributed end times.

## 3. Results

| Quantity | Value |
|---|---|
| Note events | 54 |
| Range | C2–E5 (40 semitones) |
| Pitch classes used | C D E F G A B (counts 13, 6, 6, 7, 10, 6, 6) |
| Median attack interval | 0.974 s (61.6 BPM); notebook beat tracker: 63.3 BPM |
| Interval over first 8 / last 8 attacks | 60.4 / 62.8 BPM |
| Mean / median note duration | 2.54 s / 2.07 s |
| Top key candidate | C major, r = 0.949; next G major 0.693, A minor 0.670 |
| Bar-wise chord labels | Am, Am, F, F, C, C, G, G (scores 0.75–0.91) |

**Harmony.** Bar lines on attacks 1, 5, 9, … fall at 1.57, 5.52, 9.52, 13.35, 17.20, 20.98, 24.80 and
28.62 s, which are the times of the chord changes. Bars 1–2 are dominated by A and E under a B–C melody,
bars 3–4 by F, bars 5–6 by C, bar 7 by G and B. Bar 8 contains little more than B and D sounding together
(a held B4 and D4/D5 with D3 below). Every triad containing both notes scores within 0.006 of G: G, G#dim,
Bm and Bdim are tied, so the label G for that bar is a default, not a result.

**Tempo.** Attack intervals shorten from about 1.0 s to 0.95 s over the passage (60.4 to 62.8 BPM). The
fixed-tempo fit has a root-mean-square residual of 71 ms, and a grid built from the median interval
(61.6 BPM) places the last chord change about 0.2 s late. This explains most of the gap between the median
(61.6) and the notebook tracker (63.3).

**Artefact indicators.**

- Event 1 (E3, velocity 13) starts at 0.09 s and ends at 5.5 s, but the waveform is silent until about 1.6 s.
- Event 27 (F2) lasts 7.8 ms.
- 11 of 54 note ends lie on a 0.5 s grid (expected 0.43, p ≈ 6 × 10⁻¹³).
- The metadata field `duration_seconds` (32.5 s) is the end of the MIDI, not the audio length; the audio
  ends near 31.7 s.

## 4. Discussion

The correlation with C major is explained by the pitch set: every note is diatonic to C major and to A
minor, and C is the most frequent. The chord sequence is more informative. It begins on A minor and ends
on G, so calling the passage "C major" is a choice of tonal centre that needs a listening decision, not a
result of this analysis. The rising pulse is a property of the performance and matters for notation: a
metronomic 4/4 score will need tempo markings or a flexible grid. Duration statistics are inflated if the
model extends notes through sustain pedal, so the 2.5 s mean should not be read as key-hold time.

## 5. Limitations

- One recording, one model, one noise-reduction setting; no reference transcription, so no precision,
  recall or F1 can be reported.
- The model version, device and library versions were not logged.
- Attack-snapped bars assume one attack per beat; passages with syncopation or missing beats need the
  fixed-tempo grid or manual bar lines.
- Chord templates ignore voicing, inversion and non-chord tones beyond duration weighting.
- The cause of the 0.5 s end-time pattern is unknown. A segment-boundary effect is one candidate, not a finding.

## 6. Next steps

1. Correct bars 1–4 in MuseScore to create a reference MIDI.
2. Transcribe the original and denoised audio separately; score each against the reference with
   note-level precision, recall and F1 (onset tolerance 50 ms, pitch exact) using `mir_eval`.
3. Log library versions and the model name in `run_metadata.json`.
4. Repeat on more than one recording before generalising.

## References

Benetos, E., Dixon, S., Duan, Z., & Ewert, S. (2019). Automatic music transcription: An overview.
*IEEE Signal Processing Magazine, 36*(1), 20–30.

Kong, Q., Li, B., Song, X., Wan, Y., & Wang, Y. (2021). High-resolution piano transcription with pedals
by regressing onset and offset times. *IEEE/ACM Transactions on Audio, Speech, and Language Processing,
29*, 3707–3717.

Krumhansl, C. L. (1990). *Cognitive Foundations of Musical Pitch*. Oxford University Press.

Raffel, C., et al. (2014). mir_eval: A transparent implementation of common MIR metrics. *Proc. ISMIR*.
