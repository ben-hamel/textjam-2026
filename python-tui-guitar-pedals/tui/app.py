from textual.app import App

from audio.chain import PedalChain
from audio.devices import AudioDevice
from audio.engine import AudioEngine
from pedals.fuzz import FuzzPedal
from tui.screens.audio_settings import AudioSettings
from tui.screens.device_select import DeviceSelectScreen
from tui.screens.board import BoardScreen


class PedalBoardApp(App):
    def __init__(self):
        super().__init__()
        self.chain = PedalChain()
        self.chain.pedals.append(FuzzPedal())
        self.engine = AudioEngine(self.chain)

    def on_mount(self):
        self.push_screen(DeviceSelectScreen())

    def on_devices_selected(self, input_device: AudioDevice, output_device: AudioDevice, sample_rate: int, block_size: int):
        settings = AudioSettings(input_device, output_device, sample_rate, block_size)
        self.engine.start(input_device.index, output_device.index, sample_rate, block_size)
        self.push_screen(BoardScreen(self.chain, settings))

    def restart_audio(self, settings: AudioSettings):
        self.engine.stop()
        self.chain.set_sample_rate(settings.sample_rate)
        self.engine.start(
            settings.input_device.index,
            settings.output_device.index,
            settings.sample_rate,
            settings.block_size,
        )

    def on_unmount(self):
        self.engine.stop()
