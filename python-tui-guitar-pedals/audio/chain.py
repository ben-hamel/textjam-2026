import numpy as np
from pedals.base import Pedal

DISPLAY_SIZE = 2048


class PedalChain:
    def __init__(self):
        self.pedals: list[Pedal] = []
        self._display_buf = np.zeros(DISPLAY_SIZE, dtype="float32")

    @property
    def latest_buffer(self) -> np.ndarray:
        return self._display_buf.copy()

    def set_sample_rate(self, sample_rate: int) -> None:
        for pedal in self.pedals:
            pedal.set_sample_rate(sample_rate)

    def process(self, buffer: np.ndarray) -> np.ndarray:
        for pedal in self.pedals[:]:  # snapshot so UI edits don't race
            buffer = pedal.process(buffer)
        n = len(buffer)
        self._display_buf[:-n] = self._display_buf[n:]
        self._display_buf[-n:] = buffer
        return buffer
