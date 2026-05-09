import sounddevice as sd
import numpy as np
from audio.chain import PedalChain


class AudioEngine:
    def __init__(self, chain: PedalChain):
        self.stream: sd.Stream | None = None
        self.chain = chain

    def start(self, input_device: int, output_device: int, sample_rate: int = 44100, block_size: int = 256):
        def callback(indata: np.ndarray, outdata: np.ndarray, frames, time, status):
            mono = indata[:, 0]
            processed = self.chain.process(mono)
            outdata[:, 0] = processed

        self.stream = sd.Stream(
            samplerate=sample_rate,
            blocksize=block_size,
            device=(input_device, output_device),
            channels=1,
            dtype="float32",
            latency="low",
            callback=callback,
        )
        self.stream.start()

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
