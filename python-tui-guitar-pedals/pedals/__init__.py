from pedals.fuzz import FuzzPedal
from pedals.delay import DelayPedal
from pedals.chorus import ChorusPedal
from pedals.reverb import ReverbPedal

AVAILABLE_PEDALS: dict[str, type] = {
    "fuzz":   FuzzPedal,
    "delay":  DelayPedal,
    "chorus": ChorusPedal,
    "reverb": ReverbPedal,
}
