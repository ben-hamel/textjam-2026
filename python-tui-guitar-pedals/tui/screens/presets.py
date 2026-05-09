from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListItem, ListView

from audio.chain import PedalChain
from presets import delete_preset, load_presets, save_preset


class PresetsModal(ModalScreen[list[dict] | None]):
    DEFAULT_CSS = """
    PresetsModal {
        align: center middle;
    }
    PresetsModal > Vertical {
        width: 50;
        height: auto;
        max-height: 24;
        border: double $accent;
        background: $surface;
        padding: 1 2;
    }
    PresetsModal ListView {
        height: auto;
        max-height: 12;
    }
    #modal-title {
        text-align: center;
        margin-bottom: 1;
    }
    #hint {
        margin-top: 1;
        color: $text-muted;
    }
    #name-row {
        margin-top: 1;
        height: auto;
    }
    #name-row Label {
        padding: 1 1 0 0;
        width: auto;
    }
    #name-input {
        width: 1fr;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("d", "delete_preset", "Delete"),
    ]

    def __init__(self, chain: PedalChain):
        super().__init__()
        self.chain = chain
        self._presets: list[dict] = load_presets()
        self._saving = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("── Presets ──", id="modal-title")
            yield ListView(id="preset-list")
            with Horizontal(id="name-row"):
                yield Label("Name:")
                yield Input(placeholder="preset name…", id="name-input")
            yield Label("", id="hint")

    def on_mount(self) -> None:
        self._rebuild_list()
        self._refresh_view()

    def _rebuild_list(self) -> None:
        lv = self.query_one("#preset-list", ListView)
        lv.clear()
        lv.append(ListItem(Label("[ + Save current board ]")))
        for p in self._presets:
            lv.append(ListItem(Label(p["name"])))

    def _refresh_view(self) -> None:
        self.query_one("#preset-list").display = not self._saving
        self.query_one("#name-row").display = self._saving
        hint = self.query_one("#hint", Label)
        title = self.query_one("#modal-title", Label)
        if self._saving:
            title.update("── Save Preset ──")
            hint.update("enter: save  esc: back")
            self.query_one("#name-input", Input).focus()
        else:
            title.update("── Presets ──")
            hint.update("enter: load/save  d: delete  esc: close")
            self.query_one("#preset-list", ListView).focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx == 0:
            self._saving = True
            self._refresh_view()
        else:
            preset_idx = idx - 1
            if 0 <= preset_idx < len(self._presets):
                self.dismiss(self._presets[preset_idx]["pedals"])

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        if not name:
            return
        save_preset(name, self.chain)
        self._presets = load_presets()
        self._rebuild_list()
        event.input.clear()
        self._saving = False
        self._refresh_view()

    def action_delete_preset(self) -> None:
        if self._saving:
            return
        lv = self.query_one("#preset-list", ListView)
        idx = lv.index
        if idx is None or idx == 0:  # 0 is the save item, can't delete it
            return
        delete_preset(self._presets[idx - 1]["name"])
        self._presets = load_presets()
        self._rebuild_list()
        self._refresh_view()

    def action_cancel(self) -> None:
        if self._saving:
            self._saving = False
            self.query_one("#name-input", Input).clear()
            self._refresh_view()
        else:
            self.dismiss(None)
