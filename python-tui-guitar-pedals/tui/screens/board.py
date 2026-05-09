from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer
from textual.binding import Binding
from textual.containers import HorizontalScroll

from audio.chain import PedalChain
from pedals import AVAILABLE_PEDALS
from presets import pedal_from_dict
from tui.screens.add_pedal import AddPedalModal
from tui.screens.audio_settings import AudioSettings, AudioSettingsModal
from tui.screens.presets import PresetsModal
from tui.widgets.pedal_widget import PedalWidget
from tui.widgets.waveform import WaveformDisplay


class BoardScreen(Screen):
    DEFAULT_CSS = """
    BoardScreen > HorizontalScroll {
        height: 1fr;
        align: left middle;
    }
    """

    BINDINGS = [
        Binding("a",          "add_pedal",    "Add"),
        Binding("x",          "remove_pedal", "Remove"),
        Binding("ctrl+left",  "move_left",    "Move Left"),
        Binding("ctrl+right", "move_right",   "Move Right"),
        Binding("left",       "prev_pedal",   "Prev",     show=False),
        Binding("right",      "next_pedal",   "Next",     show=False),
        Binding("s",          "audio_settings","Settings"),
        Binding("p",          "presets",      "Presets"),
        Binding("q",          "quit",         "Quit"),
    ]

    def __init__(self, chain: PedalChain, settings: AudioSettings):
        super().__init__()
        self.chain = chain
        self.settings = settings
        self._selected = 0

    def compose(self) -> ComposeResult:
        with HorizontalScroll(id="pedal-container"):
            for i, pedal in enumerate(self.chain.pedals):
                yield PedalWidget(pedal, selected=(i == self._selected))
        yield WaveformDisplay(self.chain)
        yield Footer()

    # ── selection helpers ───────────────────────────────────────────────

    def _pedal_widgets(self) -> list[PedalWidget]:
        return list(self.query(PedalWidget))

    def _set_selected(self, index: int) -> None:
        widgets = self._pedal_widgets()
        if not widgets:
            return
        self._selected = max(0, min(index, len(widgets) - 1))
        for i, w in enumerate(widgets):
            w.selected = (i == self._selected)

    # ── actions ─────────────────────────────────────────────────────────

    def action_prev_pedal(self) -> None:
        self._set_selected(self._selected - 1)

    def action_next_pedal(self) -> None:
        self._set_selected(self._selected + 1)

    @work
    async def action_add_pedal(self) -> None:
        result = await self.app.push_screen_wait(AddPedalModal())
        if result is None:
            return
        pedal = AVAILABLE_PEDALS[result](self.settings.sample_rate)
        self.chain.pedals.append(pedal)
        container = self.query_one("#pedal-container", HorizontalScroll)
        new_widget = PedalWidget(pedal)
        await container.mount(new_widget)
        self._set_selected(len(self.chain.pedals) - 1)

    async def action_remove_pedal(self) -> None:
        widgets = self._pedal_widgets()
        if not widgets:
            return
        idx = self._selected
        self.chain.pedals.pop(idx)
        await widgets[idx].remove()
        self._set_selected(min(idx, len(self.chain.pedals) - 1))

    async def action_move_left(self) -> None:
        idx = self._selected
        if idx <= 0 or idx >= len(self.chain.pedals):
            return
        pedals = self.chain.pedals
        pedals[idx], pedals[idx - 1] = pedals[idx - 1], pedals[idx]
        container = self.query_one("#pedal-container", HorizontalScroll)
        widgets = self._pedal_widgets()
        await widgets[idx].remove()
        await container.mount(PedalWidget(pedals[idx - 1]), before=widgets[idx - 1])
        self._set_selected(idx - 1)

    async def action_move_right(self) -> None:
        idx = self._selected
        pedals = self.chain.pedals
        if idx < 0 or idx >= len(pedals) - 1:
            return
        pedals[idx], pedals[idx + 1] = pedals[idx + 1], pedals[idx]
        container = self.query_one("#pedal-container", HorizontalScroll)
        widgets = self._pedal_widgets()
        await widgets[idx].remove()
        after_widget = widgets[idx + 1] if idx + 1 < len(widgets) else None
        if after_widget:
            await container.mount(PedalWidget(pedals[idx + 1]), after=after_widget)
        else:
            await container.mount(PedalWidget(pedals[idx + 1]))
        self._set_selected(idx + 1)

    @work
    async def action_presets(self) -> None:
        result = await self.app.push_screen_wait(PresetsModal(self.chain))
        if result is None:
            return
        self.chain.pedals.clear()
        container = self.query_one("#pedal-container", HorizontalScroll)
        await container.remove_children()
        for data in result:
            pedal = pedal_from_dict(data, self.settings.sample_rate)
            self.chain.pedals.append(pedal)
            await container.mount(PedalWidget(pedal))
        self._set_selected(0)

    @work
    async def action_audio_settings(self) -> None:
        result = await self.app.push_screen_wait(AudioSettingsModal(self.settings))
        if result is None:
            return
        self.settings = result
        self.app.restart_audio(result)

    def action_quit(self) -> None:
        self.app.exit()
