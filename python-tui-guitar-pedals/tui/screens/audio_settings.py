from dataclasses import dataclass

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, ListView, ListItem, TabbedContent, TabPane, Footer
from textual.binding import Binding
from textual.containers import Vertical

from audio.devices import AudioDevice, list_input_devices, list_output_devices

SAMPLE_RATES = [44100, 48000, 88200, 96000]
BLOCK_SIZES = [64, 128, 256, 512, 1024]

TAB_ORDER = ["tab-input", "tab-output", "tab-sr", "tab-bs"]
LIST_FOR_TAB = {
    "tab-input":  "list-input",
    "tab-output": "list-output",
    "tab-sr":     "list-sr",
    "tab-bs":     "list-bs",
}


@dataclass
class AudioSettings:
    input_device: AudioDevice
    output_device: AudioDevice
    sample_rate: int
    block_size: int


class AudioSettingsModal(ModalScreen[AudioSettings | None]):
    DEFAULT_CSS = """
    AudioSettingsModal {
        align: center middle;
    }
    AudioSettingsModal > Vertical {
        width: 52;
        height: 24;
        border: double $accent;
        background: $surface;
        padding: 1 2;
    }
    #modal-title {
        text-align: center;
        margin-bottom: 1;
    }
    #hint {
        text-align: center;
        margin-bottom: 1;
        color: $text-muted;
    }
    TabbedContent {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("left",   "prev_tab", "Prev Tab"),
        Binding("right",  "next_tab", "Next Tab"),
        Binding("c",      "confirm",  "Confirm"),
        Binding("escape", "cancel",   "Cancel"),
    ]

    def __init__(self, current: AudioSettings):
        super().__init__()
        self.inputs = list_input_devices()
        self.outputs = list_output_devices()
        self._pending = AudioSettings(
            current.input_device,
            current.output_device,
            current.sample_rate,
            current.block_size,
        )
        self._labels: dict[str, str] = {
            **{f"in-{d.index}":  d.name            for d in self.inputs},
            **{f"out-{d.index}": d.name            for d in self.outputs},
            **{f"sr-{sr}":       f"{sr} Hz"        for sr in SAMPLE_RATES},
            **{f"bs-{bs}":       self._bs_label(bs) for bs in BLOCK_SIZES},
        }

    def compose(self) -> ComposeResult:
        cur = self._pending
        with Vertical():
            yield Label("── Audio Settings ──", id="modal-title")
            yield Label("← → switch tab   ↑↓ navigate   Enter select", id="hint")
            with TabbedContent(id="tabs"):
                with TabPane("Input", id="tab-input"):
                    yield ListView(
                        *[ListItem(Label(self._prefix(d.index == cur.input_device.index) + d.name), id=f"in-{d.index}") for d in self.inputs],
                        id="list-input",
                    )
                with TabPane("Output", id="tab-output"):
                    yield ListView(
                        *[ListItem(Label(self._prefix(d.index == cur.output_device.index) + d.name), id=f"out-{d.index}") for d in self.outputs],
                        id="list-output",
                    )
                with TabPane("Sample Rate", id="tab-sr"):
                    yield ListView(
                        *[ListItem(Label(self._prefix(sr == cur.sample_rate) + f"{sr} Hz"), id=f"sr-{sr}") for sr in SAMPLE_RATES],
                        id="list-sr",
                    )
                with TabPane("Buffer Size", id="tab-bs"):
                    yield ListView(
                        *[ListItem(Label(self._prefix(bs == cur.block_size) + self._bs_label(bs)), id=f"bs-{bs}") for bs in BLOCK_SIZES],
                        id="list-bs",
                    )
        yield Footer()

    def on_mount(self) -> None:
        in_idx  = next((i for i, d  in enumerate(self.inputs)   if d.index == self._pending.input_device.index),  0)
        out_idx = next((i for i, d  in enumerate(self.outputs)  if d.index == self._pending.output_device.index), 0)
        sr_idx  = next((i for i, sr in enumerate(SAMPLE_RATES)  if sr == self._pending.sample_rate), 0)
        bs_idx  = next((i for i, bs in enumerate(BLOCK_SIZES)   if bs == self._pending.block_size),  0)

        self.query_one("#list-input",  ListView).index = in_idx
        self.query_one("#list-output", ListView).index = out_idx
        self.query_one("#list-sr",     ListView).index = sr_idx
        self.query_one("#list-bs",     ListView).index = bs_idx

        self._focus_active_list()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        self._focus_active_list()

    def _focus_active_list(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        list_id = LIST_FOR_TAB.get(tabs.active, "list-input")
        self.query_one(f"#{list_id}", ListView).focus()

    def action_prev_tab(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        idx = TAB_ORDER.index(tabs.active)
        tabs.active = TAB_ORDER[(idx - 1) % len(TAB_ORDER)]

    def action_next_tab(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        idx = TAB_ORDER.index(tabs.active)
        tabs.active = TAB_ORDER[(idx + 1) % len(TAB_ORDER)]

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("in-"):
            idx = int(item_id.removeprefix("in-"))
            self._pending.input_device = next(d for d in self.inputs if d.index == idx)
            self._refresh_checks("list-input", item_id)
        elif item_id.startswith("out-"):
            idx = int(item_id.removeprefix("out-"))
            self._pending.output_device = next(d for d in self.outputs if d.index == idx)
            self._refresh_checks("list-output", item_id)
        elif item_id.startswith("sr-"):
            self._pending.sample_rate = int(item_id.removeprefix("sr-"))
            self._refresh_checks("list-sr", item_id)
        elif item_id.startswith("bs-"):
            self._pending.block_size = int(item_id.removeprefix("bs-"))
            self._refresh_checks("list-bs", item_id)

    def _refresh_checks(self, list_id: str, selected_id: str) -> None:
        for item in self.query_one(f"#{list_id}", ListView).query(ListItem):
            label = item.query_one(Label)
            base = self._labels.get(item.id, "")
            label.update(self._prefix(item.id == selected_id) + base)

    @staticmethod
    def _prefix(selected: bool) -> str:
        return "✓ " if selected else "  "

    def action_confirm(self) -> None:
        self.dismiss(self._pending)

    def action_cancel(self) -> None:
        self.dismiss(None)

    @staticmethod
    def _bs_label(bs: int) -> str:
        if bs <= 128:
            return f"{bs}  (lower latency)"
        if bs >= 512:
            return f"{bs}  (higher latency)"
        return f"{bs}"
