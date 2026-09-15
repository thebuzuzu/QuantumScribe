from unittest.mock import Mock

from localwhisper.ui import Popup


class _Window:
    def __init__(self) -> None:
        self.alpha = None
        self.withdrawn = False

    def attributes(self, name: str, value=None):
        if name == "-alpha" and value is not None:
            self.alpha = value
        return self.alpha

    def deiconify(self) -> None:
        self.withdrawn = False

    def withdraw(self) -> None:
        self.withdrawn = True


def _popup_for_lifecycle() -> Popup:
    popup = object.__new__(Popup)
    popup._visual_generation = 0
    popup._active_theme = "dots"
    popup._atom_color = "#BF5AF2"
    popup._liquid_orb_renderer = object()
    popup._liquid_orb_failed = False
    popup._liquid_orb_last_error = ""
    popup._liquid_orb_explosion_progress = 0.0
    popup._cancel_hold_started_at = None
    popup._cancel_hold_duration = 0.5
    popup.window = _Window()
    popup.animating = False
    popup.smooth_amp = 0.0
    popup.hud_state = "idle"
    popup._only_atom_scale = 1.0
    popup._is_condensing = False
    popup._is_exploding = False
    popup._progress_animating = False
    popup._cancel_hold_id = 42
    return popup


def _stub_popup_lifecycle(monkeypatch, calls: list[tuple[str, object]]) -> None:
    monkeypatch.setattr(Popup, "_hide_progress", lambda _self: calls.append(("hide_progress", None)))
    monkeypatch.setattr(Popup, "_apply_layout", lambda _self, theme: calls.append(("layout", theme)))
    monkeypatch.setattr(Popup, "_set_content", lambda _self, *_args, **_kwargs: calls.append(("content", None)))
    monkeypatch.setattr(Popup, "_reset_indicators", lambda _self: calls.append(("reset", None)))
    monkeypatch.setattr(Popup, "_position", lambda _self: calls.append(("position", None)))
    monkeypatch.setattr(Popup, "_animate", lambda _self, generation: calls.append(("animate", generation)))
    monkeypatch.setattr(Popup, "clear_cancel_hold", lambda _self: calls.append(("clear_cancel", None)))


def test_liquid_orb_theme_switch_invalidates_the_previous_visual_generation(monkeypatch):
    popup = _popup_for_lifecycle()
    calls: list[tuple[str, object]] = []
    _stub_popup_lifecycle(monkeypatch, calls)

    Popup.show_recording(popup, theme="liquid_orb", color="#0A84FF")
    first_generation = popup.visual_generation

    Popup.show_recording(popup, theme="dots", color="#FF9F0A")

    assert popup._active_theme == "dots"
    assert popup.visual_generation == first_generation + 1
    assert popup._atom_color == "#FF9F0A"
    assert [call for call in calls if call[0] == "layout"] == [
        ("layout", "liquid_orb"),
        ("layout", "dots"),
    ]


def test_liquid_orb_lifecycle_keeps_states_and_rejects_stale_hide(monkeypatch):
    popup = _popup_for_lifecycle()
    popup._active_theme = "liquid_orb"
    calls: list[tuple[str, object]] = []
    _stub_popup_lifecycle(monkeypatch, calls)

    Popup.show_processing_with_progress(popup, audio_duration=1.0)
    assert popup.hud_state == "transcribing"
    transcribing_generation = popup.visual_generation

    Popup.show_message(popup, "Falha", "Tente novamente", error=True)
    assert popup.hud_state == "error"
    error_generation = popup.visual_generation
    assert error_generation == transcribing_generation + 1

    Popup.hide(popup, generation=transcribing_generation)
    assert popup.hud_state == "error"
    assert popup.visual_generation == error_generation

    Popup.complete_progress(popup)
    assert popup.hud_state == "exploding"
    assert popup.animating is True

    Popup.hide(popup, generation=error_generation)
    assert popup.hud_state == "idle"
    assert popup.animating is False
    assert popup.visual_generation == error_generation + 1
    assert ("clear_cancel", None) in calls


def test_cancel_hold_only_draws_feedback_while_recording(monkeypatch):
    popup = _popup_for_lifecycle()
    popup._active_layout = {"atom_a": 10, "atom_b": 8, "atom_cx": 20, "atom_cy": 20}
    popup.canvas = Mock()
    popup.hud_state = "recording"
    monkeypatch.setattr("localwhisper.ui.time.monotonic", lambda: 5.0)

    Popup.start_cancel_hold(popup, duration_seconds=0.5)
    assert popup._cancel_hold_started_at == 5.0
    popup.canvas.itemconfigure.assert_called_with(
        popup._cancel_hold_id,
        extent=-0.0,
        state="normal",
    )

    popup.hud_state = "transcribing"
    popup._cancel_hold_started_at = None
    popup.canvas.reset_mock()
    Popup.start_cancel_hold(popup)
    popup.canvas.coords.assert_not_called()
    popup.canvas.itemconfigure.assert_not_called()
