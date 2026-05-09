from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text


class Knob(Widget):
    DEFAULT_CSS = """
    Knob {
        width: 10;
        height: 5;
        border: round $panel-lighten-2;
        padding: 0 1;
        margin: 0 1;
    }
    Knob:focus {
        border: round $accent;
    }
    """

    BINDINGS = [
        ("up", "increment", ""),
        ("down", "decrement", ""),
    ]

    value: reactive[float] = reactive(0.5)

    class Changed(Message):
        def __init__(self, knob: "Knob", value: float) -> None:
            super().__init__()
            self.knob = knob
            self.value = value

    def __init__(self, label: str, initial: float = 0.5, step: float = 0.05, **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self.value = initial
        self.step = step
        self.can_focus = True

    def render(self) -> Text:
        filled = round(self.value * 6)
        bar = "█" * filled + "░" * (6 - filled)
        label_line = self._label[:6].center(6)
        value_line = f"{self.value:.2f}".center(6)
        return Text(f"{label_line}\n{bar}\n{value_line}")

    def action_increment(self) -> None:
        self.value = min(1.0, round(self.value + self.step, 2))
        self.post_message(self.Changed(self, self.value))

    def action_decrement(self) -> None:
        self.value = max(0.0, round(self.value - self.step, 2))
        self.post_message(self.Changed(self, self.value))
