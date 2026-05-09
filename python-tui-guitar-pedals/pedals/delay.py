import numpy as np
from pedals.base import Pedal

MAX_DELAY_SECONDS = 2


class DelayPedal(Pedal):
    name = "DELAY"
    KNOBS = [
        ("TIME",     "time",     0.3, 0.05),
        ("FEEDBACK", "feedback", 0.4, 0.05),
        ("MIX",      "mix",      0.4, 0.05),
    ]

    def __init__(self, sample_rate: int = 44100):
        super().__init__(sample_rate)
        self.time: float = 0.3
        self.feedback: float = 0.4
        self.mix: float = 0.4
        self._init_buffer()

    def _init_buffer(self) -> None:
        self._buf = np.zeros(self.sample_rate * MAX_DELAY_SECONDS, dtype=np.float32)
        self._pos = 0

    def set_sample_rate(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate
        self._init_buffer()

    def process(self, buffer: np.ndarray) -> np.ndarray:
        if not self.engaged:
            return buffer

        max_samples = len(self._buf)
        delay_samples = max(1, int((0.05 + self.time * 0.95) * self.sample_rate))
        output = np.empty_like(buffer)

        for i in range(len(buffer)):
            read = (self._pos - delay_samples) % max_samples
            delayed = self._buf[read]
            self._buf[self._pos] = buffer[i] + delayed * self.feedback
            output[i] = buffer[i] * (1 - self.mix) + delayed * self.mix
            self._pos = (self._pos + 1) % max_samples

        return output
