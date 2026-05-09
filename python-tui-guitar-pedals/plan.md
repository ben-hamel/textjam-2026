# Terminal Guitar Pedal — Claude Code Prompt

## Project Overview

Build a terminal-based guitar pedal app in Python on macOS. The goal is a real-time audio effects pedal with a text UI, built as a jam submission for a text-based game/tool jam.

## Tech Stack

- **Python**
- **`sounddevice`** — real-time audio I/O
- **`numpy`** — DSP math
- **`textual`** — TUI

---

## Phase 1 — Passthrough (Start Here)

1. **Device picker** — on startup, list all available audio devices and let the user select their input and output (audio interface connected via USB on macOS)
2. **Audio passthrough** — once devices are selected, open a `sounddevice` stream that passes audio from input to output with no processing, just to confirm the pipeline works
3. **Basic TUI shell** — a simple Textual layout that shows the selected devices and a placeholder for the pedal UI, with a way to quit cleanly (`q` or `ctrl+c`)

---

## Phase 2 — Fuzz Pedal (After Passthrough Works)

4. **Fuzz pedal** — a single pedal with three knobs: Gain, Tone, Volume
   - Implement fuzz as soft or hard clipping on the numpy audio buffer
   - Knobs should be selectable with arrow keys and adjustable with up/down
   - Changes should affect the audio in real time
5. **Engaged toggle** — a bypass switch to turn the effect on/off
6. **Waveform display** — a small real-time view of the processed signal using braille or block characters

---

## General Notes

- Keep latency low — use a blocksize of **512 samples at 44100hz**
- Audio callback should be non-blocking and simple
- The app should feel like a guitar pedal, not a DAW — focused and tactile
- macOS Core Audio, no ASIO needed

> **Start with Phase 1 only.** Get passthrough working and confirmed before touching effects or the full UI.