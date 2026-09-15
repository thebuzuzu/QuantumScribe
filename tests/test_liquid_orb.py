from localwhisper.config import AppConfig, load_config, save_config
from localwhisper.hud_effects import (
    ORB_THEMES,
    LiquidOrbRenderer,
    render_liquid_orb,
    render_prismatic_bubble,
)
from localwhisper.settings_ui import HUD_THEMES
from localwhisper.ui import Popup


def test_only_supported_hud_themes_are_catalogued():
    theme_ids = {theme_id for theme_id, _name, _description in HUD_THEMES}

    assert theme_ids == {"atom_centered", "liquid_orb", "prismatic_bubble"}
    assert ORB_THEMES == {"liquid_orb", "prismatic_bubble"}
    assert AppConfig().hud_theme == "atom_centered"


def test_legacy_hud_theme_is_normalized_to_centered_atom():
    assert AppConfig(hud_theme="dots").hud_theme == "atom_centered"


def test_liquid_orb_theme_persists_and_reloads(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    config = AppConfig(hud_theme="liquid_orb")
    save_config(config)

    assert load_config().hud_theme == "liquid_orb"


def test_liquid_orb_frame_is_deterministic_and_responds_to_inputs():
    frame = render_liquid_orb(
        size=48,
        time_value=1.25,
        color="#0A84FF",
        amplitude=0.35,
        state="recording",
    )
    same_frame = render_liquid_orb(
        size=48,
        time_value=1.25,
        color="#0A84FF",
        amplitude=0.35,
        state="recording",
    )
    changed_frame = render_liquid_orb(
        size=48,
        time_value=1.75,
        color="#0A84FF",
        amplitude=0.8,
        state="recording",
    )

    assert frame.mode == "RGBA"
    assert frame.size == (48, 48)
    assert frame.tobytes() == same_frame.tobytes()
    assert frame.tobytes() != changed_frame.tobytes()
    assert frame.getchannel("A").getextrema()[1] > 0


def test_prismatic_bubble_is_deterministic_and_visually_distinct():
    frame = render_prismatic_bubble(
        size=48,
        time_value=1.25,
        color="#0A84FF",
        amplitude=0.35,
        state="recording",
    )
    same_frame = render_prismatic_bubble(
        size=48,
        time_value=1.25,
        color="#0A84FF",
        amplitude=0.35,
        state="recording",
    )
    liquid_frame = render_liquid_orb(
        size=48,
        time_value=1.25,
        color="#0A84FF",
        amplitude=0.35,
        state="recording",
    )

    assert frame.mode == "RGBA"
    assert frame.size == (48, 48)
    assert frame.tobytes() == same_frame.tobytes()
    assert frame.tobytes() != liquid_frame.tobytes()
    assert frame.getchannel("A").getextrema()[1] > 0


def test_renderer_can_select_prismatic_bubble():
    renderer = LiquidOrbRenderer(size=48, effect="prismatic_bubble")

    frame = renderer.render(
        time_value=0.5,
        color="#BF5AF2",
        amplitude=0.2,
        state="transcribing",
        scale=1.0,
        opacity=1.0,
    )

    assert renderer.effect == "prismatic_bubble"
    assert frame.size == (48, 48)


def test_liquid_orb_renderer_rejects_unsupported_size():
    try:
        LiquidOrbRenderer(size=12)
    except ValueError as exc:
        assert "mínimo" in str(exc)
    else:
        raise AssertionError("renderer deveria rejeitar tamanhos abaixo do mínimo")


def test_liquid_orb_renderer_failure_is_captured_without_tkinter(monkeypatch):
    class BrokenRenderer:
        def render(self, **_kwargs):
            raise RuntimeError("frame failure")

    popup = object.__new__(Popup)
    popup._visual_generation = 7
    popup._active_theme = "liquid_orb"
    popup._liquid_orb_renderer = BrokenRenderer()
    popup._liquid_orb_last_error = ""
    fallback_calls: list[int] = []
    monkeypatch.setattr(
        popup,
        "_fallback_liquid_orb",
        lambda generation: fallback_calls.append(generation),
    )

    assert Popup._render_liquid_orb_frame(
        popup,
        7,
        time_value=0.0,
        amplitude=0.0,
        state="recording",
        scale=1.0,
        opacity=1.0,
    ) is False
    assert fallback_calls == [7]
    assert "frame failure" in popup._liquid_orb_last_error


def test_liquid_orb_fallback_switches_only_the_current_session_to_safe_theme():
    popup = object.__new__(Popup)
    popup._visual_generation = 7
    popup._active_theme = "liquid_orb"
    popup._liquid_orb_renderer = object()
    popup._liquid_orb_failed = False
    popup.hud_state = "recording"
    calls: list[tuple[str, object]] = []
    popup._apply_layout = lambda theme: calls.append(("layout", theme))
    popup._reset_indicators = lambda: calls.append(("reset", None))
    popup._position = lambda: calls.append(("position", None))
    popup._animate_atom = lambda generation: calls.append(("animate", generation))

    Popup._fallback_liquid_orb(popup, 7)

    assert popup._active_theme == "atom_centered"
    assert popup._liquid_orb_failed is True
    assert popup._liquid_orb_renderer is None
    assert calls == [
        ("layout", "atom_centered"),
        ("reset", None),
        ("position", None),
        ("animate", 7),
    ]


def test_liquid_orb_renderer_creation_failure_is_safe(monkeypatch):
    def broken_renderer(**_kwargs):
        raise RuntimeError("renderer unavailable")

    import localwhisper.ui as ui_module

    monkeypatch.setattr(ui_module, "LiquidOrbRenderer", broken_renderer)
    popup = object.__new__(Popup)
    popup._liquid_orb_renderer = None
    popup._liquid_orb_last_error = ""

    assert Popup._ensure_liquid_orb_renderer(popup) is False
    assert "renderer unavailable" in popup._liquid_orb_last_error


def test_show_recording_falls_back_when_renderer_cannot_start(monkeypatch):
    import tkinter as tk
    from unittest.mock import Mock

    import localwhisper.ui as ui_module

    window = Mock()

    def attributes(name, *_args):
        if name == "-transparentcolor":
            raise tk.TclError("unsupported")

    window.attributes.side_effect = attributes
    monkeypatch.setattr(ui_module.tk, "Toplevel", lambda _root: window)
    monkeypatch.setattr(ui_module.tk, "Canvas", lambda *_args, **_kwargs: Mock())
    monkeypatch.setattr(Popup, "_apply_noactivate", lambda _self: None)
    monkeypatch.setattr(
        Popup,
        "_render_pill",
        lambda self, *_args: setattr(self, "_pill_photo", None),
    )
    monkeypatch.setattr(Popup, "_position", lambda _self: None)
    monkeypatch.setattr(
        ui_module,
        "LiquidOrbRenderer",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("renderer unavailable")),
    )

    popup = Popup(Mock(), on_cancel=lambda: None)
    popup.show_recording(theme="liquid_orb")

    assert popup._active_theme == "atom_centered"
    assert popup._liquid_orb_failed is True
    window.deiconify.assert_called_once()


def test_stale_liquid_orb_frame_does_not_invoke_fallback(monkeypatch):
    popup = object.__new__(Popup)
    popup._visual_generation = 8
    popup._active_theme = "liquid_orb"
    popup._liquid_orb_renderer = None
    fallback_calls: list[int] = []
    monkeypatch.setattr(
        popup,
        "_fallback_liquid_orb",
        lambda generation: fallback_calls.append(generation),
    )

    assert Popup._render_liquid_orb_frame(
        popup,
        7,
        time_value=0.0,
        amplitude=0.0,
        state="recording",
        scale=1.0,
        opacity=1.0,
    ) is False
    assert fallback_calls == []
