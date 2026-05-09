import sounddevice as sd
from dataclasses import dataclass


@dataclass
class AudioDevice:
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int


def list_input_devices() -> list[AudioDevice]:
    devices = sd.query_devices()
    return [
        AudioDevice(i, d["name"], d["max_input_channels"], d["max_output_channels"])
        for i, d in enumerate(devices)
        if d["max_input_channels"] > 0
    ]


def list_output_devices() -> list[AudioDevice]:
    devices = sd.query_devices()
    return [
        AudioDevice(i, d["name"], d["max_input_channels"], d["max_output_channels"])
        for i, d in enumerate(devices)
        if d["max_output_channels"] > 0
    ]
