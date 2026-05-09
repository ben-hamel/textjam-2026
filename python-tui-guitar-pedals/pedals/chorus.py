import numpy as np
from pedals.base import Pedal


class ChorusPedal(Pedal):
    name = "CHORUS"
    KNOBS = [
        ("RATE",  "rate",  0.3, 0.05),
        ("DEPTH", "depth", 0.5, 0.05),
        ("MIX",   "mix",   0.5, 0.05),
    ]

    def __init__(self, sample_rate: int = 44100):
        super().__init__(sample_rate)
        self.rate: float = 0.3
        self.depth: float = 0.5
        self.mix: float = 0.5
        self._lfo_phase = 0.0
        self._init_buffer()

    def _init_buffer(self) -> None:
        max_delay = int(self.sample_rate * 0.05)  # 50ms
        self._buf = np.zeros(max_delay + 1, dtype=np.float32)
        self._pos = 0

    def set_sample_rate(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate
        self._init_buffer()

    def process(self, buffer: np.ndarray) -> np.ndarray:
        if not self.engaged:
            return buffer

        lfo_rate = 0.1 + self.rate * 4.9  # 0.1–5 Hz
        lfo_step = lfo_rate * 2 * np.pi / self.sample_rate
        base_delay = int(0.02 * self.sample_rate)   # 20ms centre
        mod_depth = int(self.depth * 0.015 * self.sample_rate)

        output = np.empty_like(buffer)
        buf_len = len(self._buf)

        for i in range(len(buffer)):
            delay = base_delay + int(np.sin(self._lfo_phase) * mod_depth)
            delay = max(1, min(delay, buf_len - 1))
            read = (self._pos - delay) % buf_len
            delayed = self._buf[read]
            self._buf[self._pos] = buffer[i]
            output[i] = buffer[i] * (1 - self.mix) + delayed * self.mix
            self._pos = (self._pos + 1) % buf_len
            self._lfo_phase += lfo_step
            if self._lfo_phase > 2 * np.pi:
                self._lfo_phase -= 2 * np.pi

        return output
