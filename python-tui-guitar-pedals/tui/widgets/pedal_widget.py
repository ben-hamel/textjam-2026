from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button
from textual.containers import Horizontal
from textual.reactive import reactive

from pedals.base import Pedal
from tui.widgets.knob import Knob


class PedalWidget(Widget):
    DEFAULT_CSS = """
    PedalWidget {
        border: tall $panel-lighten-2;
        width: 40;
        height: 16;
        padding: 1 1;
        margin: 0 1;
    }
    PedalWidget.selected {
        border: tall $accent;
    }
    PedalWidget > Horizontal {
        height: auto;
        align: center middle;
    }
    .pedal-name {
        text-align: center;
        width: 100%;
        padding: 1 0;
        text-style: bold;
    }
    .bypass-btn {
        width: 1fr;
        margin: 1 2 0 2;
    }
    """

    selected: reactive[bool] = reactive(False)

    def __init__(self, pedal: Pedal, selected: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.pedal = pedal
        self.selected = selected

    def compose(self) -> ComposeResult:
        yield Horizontal(
            *[
                Knob(label, initial=getattr(self.pedal, attr), step=step, id=f"knob-{attr}")
                for label, attr, _default, step in self.pedal.KNOBS
            ]
        )
        yield Label(f"─── {self.pedal.name} ───", classes="pedal-name")
        yield Button("⬤  ENGAGED", classes="bypass-btn", variant="success")

    def watch_selected(self, selected: bool) -> None:
        self.set_class(selected, "selected")

    def on_knob_changed(self, event: Knob.Changed) -> None:
        if event.knob.id and event.knob.id.startswith("knob-"):
            attr = event.knob.id[5:]
            setattr(self.pedal, attr, event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.pedal.engaged = not self.pedal.engaged
        btn = self.query_one(Button)
        if self.pedal.engaged:
            btn.label = "⬤  ENGAGED"
            btn.variant = "success"
        else:
            btn.label = "○  BYPASS"
            btn.variant = "default"
