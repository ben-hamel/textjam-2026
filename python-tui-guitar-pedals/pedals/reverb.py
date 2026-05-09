import numpy as np
from pedals.base import Pedal

# Simplified Freeverb: 4 lowpass comb filters + 2 allpass filters
_COMB_DELAYS   = [1557, 1617, 1491, 1422]
_ALLPASS_DELAYS = [225, 556]


class ReverbPedal(Pedal):
    name = "REVERB"
    KNOBS = [
        ("ROOM",  "room",  0.5, 0.05),
        ("DAMP",  "damp",  0.5, 0.05),
        ("MIX",   "mix",   0.3, 0.05),
    ]

    def __init__(self, sample_rate: int = 44100):
        super().__init__(sample_rate)
        self.room: float = 0.5
        self.damp: float = 0.5
        self.mix: float = 0.3
        self._comb_bufs  = [np.zeros(d, dtype=np.float32) for d in _COMB_DELAYS]
        self._comb_pos   = [0] * len(_COMB_DELAYS)
        self._comb_filt  = [0.0] * len(_COMB_DELAYS)
        self._ap_bufs    = [np.zeros(d, dtype=np.float32) for d in _ALLPASS_DELAYS]
        self._ap_pos     = [0] * len(_ALLPASS_DELAYS)

    def process(self, buffer: np.ndarray) -> np.ndarray:
        if not self.engaged:
            return buffer

        feedback = self.room * 0.28 + 0.7   # 0.70–0.98
        damp     = self.damp * 0.4

        output = np.zeros_like(buffer)

        for i in range(len(buffer)):
            inp = buffer[i] * 0.015

            # Parallel comb filters
            comb_sum = 0.0
            for c in range(len(_COMB_DELAYS)):
                p = self._comb_pos[c]
                y = self._comb_bufs[c][p]
                self._comb_filt[c] = y * (1 - damp) + self._comb_filt[c] * damp
                self._comb_bufs[c][p] = inp + self._comb_filt[c] * feedback
                self._comb_pos[c] = (p + 1) % _COMB_DELAYS[c]
                comb_sum += y

            # Series allpass filters
            sig = comb_sum
            for a in range(len(_ALLPASS_DELAYS)):
                p = self._ap_pos[a]
                buf_out = self._ap_bufs[a][p]
                self._ap_bufs[a][p] = sig + buf_out * 0.5
                sig = buf_out - sig
                self._ap_pos[a] = (p + 1) % _ALLPASS_DELAYS[a]

            output[i] = buffer[i] * (1 - self.mix) + sig * self.mix

        return output
