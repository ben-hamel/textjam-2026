import json
from pathlib import Path

from audio.chain import PedalChain
from pedals import AVAILABLE_PEDALS
from pedals.base import Pedal

PRESETS_PATH = Path.home() / ".config" / "textjam-pedals" / "presets.json"


def pedal_to_dict(pedal: Pedal) -> dict:
    type_name = next(k for k, v in AVAILABLE_PEDALS.items() if v is type(pedal))
    knobs = {attr: getattr(pedal, attr) for _, attr, _, _ in pedal.KNOBS}
    return {"type": type_name, "engaged": pedal.engaged, "knobs": knobs}


def pedal_from_dict(data: dict, sample_rate: int = 44100) -> Pedal:
    pedal = AVAILABLE_PEDALS[data["type"]](sample_rate)
    pedal.engaged = data["engaged"]
    for attr, value in data["knobs"].items():
        setattr(pedal, attr, value)
    return pedal


def load_presets() -> list[dict]:
    if not PRESETS_PATH.exists():
        return []
    try:
        return json.loads(PRESETS_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def save_presets(presets: list[dict]) -> None:
    PRESETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRESETS_PATH.write_text(json.dumps(presets, indent=2))


def save_preset(name: str, chain: PedalChain) -> None:
    presets = load_presets()
    entry = {"name": name, "pedals": [pedal_to_dict(p) for p in chain.pedals]}
    for i, p in enumerate(presets):
        if p["name"] == name:
            presets[i] = entry
            break
    else:
        presets.append(entry)
    save_presets(presets)


def delete_preset(name: str) -> None:
    presets = [p for p in load_presets() if p["name"] != name]
    save_presets(presets)
