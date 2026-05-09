# Rust TUI Guitar Pedals

A terminal UI guitar effects pedal app. Audio runs live — launch it and start playing.

## Usage

```bash
# Live input (mic / guitar interface)
cargo run

# Feed a WAV file instead of live input (loops continuously)
cargo run -- --file path/to/guitar.wav
```

`--file` accepts mono or stereo WAV files (16/24/32-bit int or float). Stereo is mixed to mono automatically.

## Controls

| Key | Action |
|---|---|
| `←` / `→` | Select previous / next knob |
| `↑` / `↓` | Adjust selected knob ±0.05 |
| `space` | Toggle bypass |
| `q` | Quit |

## Pedal

**Fuzz** — three knobs:

- **GAIN** — drive amount (tanh saturation)
- **TONE** — IIR low-pass cutoff
- **VOLUME** — output level

## Requirements

- Rust 1.85+
- Audio hardware (input + output) for live mode, or a WAV file for `--file` mode
