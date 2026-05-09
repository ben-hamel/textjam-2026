# Rust TUI Guitar Pedals — MVP Plan

## Goal

A single-screen TUI guitar pedal app. Launch it, audio starts immediately with a fuzz pedal loaded. Adjust knobs, toggle bypass, quit. No setup screens, no presets, no modals.

## What it does

- Opens default audio input/output at 44100 Hz, 256 sample block size
- Loads a fuzz pedal with GAIN, TONE, VOLUME knobs
- Displays the pedal and its knobs in the terminal
- Left/right navigates between knobs
- Up/down adjusts the selected knob (step 0.05, clamped 0.0–1.0)
- Space toggles bypass on/off
- q quits and stops audio

## File structure

```
rust-tui-guitar-pedals/
├── Cargo.toml
└── src/
    ├── main.rs        — entry point, wires audio + TUI together
    ├── pedal.rs       — FuzzPedal struct + DSP
    ├── audio.rs       — AudioEngine (cpal input→ringbuf→process→output)
    └── app.rs         — TUI app state, draw loop, key handling
```

## Dependencies

| Crate | Purpose |
|---|---|
| `ratatui` | TUI rendering |
| `crossterm` | Terminal backend + key events |
| `cpal` | Cross-platform real-time audio I/O |
| `ringbuf` | Lock-free ring buffer connecting input/output streams |
| `anyhow` | Error handling |

## Audio design

cpal runs input and output as separate streams on background threads. A lock-free ring buffer connects them:

```
mic → [input callback] → ringbuf → [output callback] → process() → speakers
```

`process()` locks `Arc<Mutex<FuzzPedal>>` with `try_lock()` (never blocks the audio thread) and applies the DSP in-place on a `&mut [f32]` buffer. Input may be stereo — average channels to mono. Output may be stereo — copy mono to all channels.

## DSP (FuzzPedal)

Direct port from Python:
1. Apply gain: `s = tanh(s * (1 + gain * 19))`
2. IIR low-pass tone filter: `prev = (1 - alpha) * prev + alpha * s`
3. Scale by volume

## TUI design

Single screen, no alternate modes:

```
┌──────────────────────────────────────────┐
│                                          │
│   GAIN        TONE       VOLUME          │
│   ████░░      ████░░     ████░░          │
│   0.50        0.50       0.50            │
│                                          │
│              ─── FUZZ ───               │
│              ◉  ENGAGED                 │
│                                          │
└──────────────────────────────────────────┘
  ← → knob   ↑ ↓ adjust   space bypass   q quit
```

Selected knob is highlighted in yellow. Bypass shows green "◉ ENGAGED" or dim "○ BYPASS".

## Key bindings

| Key | Action |
|---|---|
| `←` / `→` | Previous / next knob |
| `↑` | Increment selected knob by 0.05 |
| `↓` | Decrement selected knob by 0.05 |
| `space` | Toggle bypass |
| `q` | Quit |

## Build steps

1. Write `Cargo.toml`
2. Write `src/pedal.rs` — FuzzPedal struct + Pedal trait
3. Write `src/audio.rs` — AudioEngine using cpal + ringbuf
4. Write `src/app.rs` — App state + ratatui draw + crossterm event loop
5. Write `src/main.rs` — wire it all together
6. `cargo build` and fix errors
7. `cargo run` and test with audio hardware
