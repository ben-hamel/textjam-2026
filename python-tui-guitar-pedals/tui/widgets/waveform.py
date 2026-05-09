import numpy as np
from rich.text import Text
from textual.widget import Widget
from audio.chain import PedalChain

_LEFT_DOTS  = [0x01, 0x02, 0x04, 0x40]
_RIGHT_DOTS = [0x08, 0x10, 0x20, 0x80]


def _find_trigger(buffer: np.ndarray) -> int:
    """Find first rising zero-crossing in the first half so display stays locked."""
    half = len(buffer) // 2
    for i in range(1, half):
        if buffer[i - 1] <= 0.0 < buffer[i]:
            return i
    return 0


def _render_braille(buffer: np.ndarray, width: int, height: int) -> str:
    pixel_cols = width * 2
    pixel_rows = height * 4
    n = len(buffer)

    # Sample one value per pixel column
    indices = np.linspace(0, n - 1, pixel_cols, dtype=int)
    samples = buffer[indices]

    # Map -1..1 → pixel row (1.0 = top row 0, -1.0 = bottom row pixel_rows-1)
    dot_rows = np.clip(((1 - samples) / 2 * pixel_rows).astype(int), 0, pixel_rows - 1)

    # Connect consecutive dots: fill between adjacent column positions so there are no gaps
    top_rows = np.minimum(dot_rows[:-1], dot_rows[1:])
    bot_rows = np.maximum(dot_rows[:-1], dot_rows[1:])
    top_rows = np.append(top_rows, dot_rows[-1])
    bot_rows = np.append(bot_rows, dot_rows[-1])

    lines = []
    for char_row in range(height):
        line = ""
        for char_col in range(width):
            lc = char_col * 2
            rc = char_col * 2 + 1
            code = 0x2800
            for dot_row in range(4):
                pr = char_row * 4 + dot_row
                if top_rows[lc] <= pr <= bot_rows[lc]:
                    code |= _LEFT_DOTS[dot_row]
                if rc < pixel_cols and top_rows[rc] <= pr <= bot_rows[rc]:
                    code |= _RIGHT_DOTS[dot_row]
            line += chr(code)
        lines.append(line)

    return "\n".join(lines)


class WaveformDisplay(Widget):
    DEFAULT_CSS = """
    WaveformDisplay {
        height: 6;
        border: round $panel-lighten-2;
        margin: 0;
    }
    """

    def __init__(self, chain: PedalChain, **kwargs):
        super().__init__(**kwargs)
        self.chain = chain

    def on_mount(self) -> None:
        self.set_interval(1 / 30, self.refresh)

    def render(self) -> Text:
        w = self.size.width - 2
        h = self.size.height - 2
        if w < 2 or h < 1:
            return Text("")

        buf = self.chain.latest_buffer

        # Auto-scale so quiet signals still show
        peak = np.max(np.abs(buf))
        if peak > 0.01:
            buf = buf / peak

        # Trigger on rising zero-crossing for a stable display
        trigger = _find_trigger(buf)
        needed = w * 2
        window = buf[trigger:trigger + needed]
        if len(window) < needed:
            return Text("")

        return Text(_render_braille(window, w, h))
