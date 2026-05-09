from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, ListView, ListItem, Footer
from textual.binding import Binding

from audio.devices import AudioDevice, list_input_devices, list_output_devices

SAMPLE_RATES = [44100, 48000, 88200, 96000]
BLOCK_SIZES = [64, 128, 256, 512, 1024]


class DeviceSelectScreen(Screen):
    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.inputs = list_input_devices()
        self.outputs = list_output_devices()
        self.selected_input: AudioDevice | None = None
        self.selected_output: AudioDevice | None = None
        self.selected_sample_rate: int | None = None
        self._step = "input"

    def compose(self) -> ComposeResult:
        yield Label("Select input device:", id="prompt")
        yield ListView(
            *[ListItem(Label(d.name), id=f"in-{d.index}") for d in self.inputs],
            id="device-list",
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""

        if item_id.startswith("in-"):
            device_index = int(item_id.removeprefix("in-"))
            self.selected_input = next(d for d in self.inputs if d.index == device_index)
            self._step = "output"
            self._show_output_picker()

        elif item_id.startswith("out-"):
            device_index = int(item_id.removeprefix("out-"))
            self.selected_output = next(d for d in self.outputs if d.index == device_index)
            self._step = "sample_rate"
            self._show_sample_rate_picker()

        elif item_id.startswith("sr-"):
            self.selected_sample_rate = int(item_id.removeprefix("sr-"))
            self._step = "block_size"
            self._show_block_size_picker()

        elif item_id.startswith("bs-"):
            block_size = int(item_id.removeprefix("bs-"))
            self.app.on_devices_selected(
                self.selected_input,
                self.selected_output,
                self.selected_sample_rate,
                block_size,
            )

    def _show_output_picker(self):
        self.query_one("#prompt", Label).update("Select output device:")
        lv = self.query_one("#device-list", ListView)
        lv.clear()
        for d in self.outputs:
            lv.append(ListItem(Label(d.name), id=f"out-{d.index}"))

    def _show_sample_rate_picker(self):
        self.query_one("#prompt", Label).update("Select sample rate (Hz):")
        lv = self.query_one("#device-list", ListView)
        lv.clear()
        for sr in SAMPLE_RATES:
            marker = " (default)" if sr == 44100 else ""
            lv.append(ListItem(Label(f"{sr}{marker}"), id=f"sr-{sr}"))

    def _show_block_size_picker(self):
        self.query_one("#prompt", Label).update("Select buffer size (samples):")
        lv = self.query_one("#device-list", ListView)
        lv.clear()
        for bs in BLOCK_SIZES:
            if bs <= 128:
                note = " (lower latency)"
            elif bs >= 512:
                note = " (higher latency)"
            else:
                note = " (default)"
            lv.append(ListItem(Label(f"{bs}{note}"), id=f"bs-{bs}"))

    def action_quit(self):
        self.app.exit()
