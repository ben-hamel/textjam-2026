# zig-tui-guitar-pedals

A terminal fuzz pedal simulator written in Zig.

## Build

```
zig build
```

## Run

**With microphone input:**
```
zig build run
```

**With a looping WAV file:**
```
zig build run -- --file /path/to/loop.wav
```

## Controls

| Key | Action |
|-----|--------|
| `←` `→` | Select knob (GAIN / TONE / VOLUME) |
| `↑` `↓` | Adjust selected knob |
| `space` | Toggle bypass |
| `q` | Quit |
