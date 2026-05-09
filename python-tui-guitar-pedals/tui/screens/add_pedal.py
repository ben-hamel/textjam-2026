from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, ListView, ListItem
from textual.binding import Binding
from textual.containers import Vertical

from pedals import AVAILABLE_PEDALS


class AddPedalModal(ModalScreen[str | None]):
    DEFAULT_CSS = """
    AddPedalModal {
        align: center middle;
    }
    AddPedalModal > Vertical {
        width: 36;
        height: auto;
        border: double $accent;
        background: $surface;
        padding: 1 2;
    }
    AddPedalModal ListView {
        height: auto;
    }
    #modal-title {
        text-align: center;
        margin-bottom: 1;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("── Add Pedal ──", id="modal-title")
            yield ListView(
                *[
                    ListItem(Label(name.capitalize()), id=name)
                    for name in AVAILABLE_PEDALS
                ]
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss(event.item.id)

    def action_cancel(self) -> None:
        self.dismiss(None)
