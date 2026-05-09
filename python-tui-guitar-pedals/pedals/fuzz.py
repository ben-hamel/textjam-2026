import numpy as np
from pedals.base import Pedal


class FuzzPedal(Pedal):
    name = "FUZZ"
    KNOBS = [
        ("GAIN",   "gain",   0.5, 0.05),
        ("TONE",   "tone",   0.5, 0.05),
        ("VOLUME", "volume", 0.5, 0.05),
    ]

    def __init__(self, sample_rate: int = 44100):
        super().__init__(sample_rate)
        self.gain: float = 0.5
        self.tone: float = 0.5
        self.volume: float = 0.5

    def process(self, buffer: np.ndarray) -> np.ndarray:
        if not self.engaged:
            return buffer

        signal = buffer * (1 + self.gain * 19)
        signal = np.tanh(signal)

        # Simple first-order IIR low-pass for tone (0=dark, 1=bright)
        alpha = self.tone * 0.95 + 0.02
        result = np.empty_like(signal)
        prev = float(signal[0])
        for i in range(len(signal)):
            prev = (1 - alpha) * prev + alpha * float(signal[i])
            result[i] = prev

        return result * self.volume
