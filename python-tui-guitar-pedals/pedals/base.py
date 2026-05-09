from abc import ABC, abstractmethod
import numpy as np


class Pedal(ABC):
    name: str = "PEDAL"
    # Each entry: (label, attr_name, default, step)
    KNOBS: list[tuple[str, str, float, float]] = []

    def __init__(self, sample_rate: int = 44100):
        self.engaged: bool = True
        self.sample_rate: int = sample_rate

    def set_sample_rate(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate

    @abstractmethod
    def process(self, buffer: np.ndarray) -> np.ndarray: ...
