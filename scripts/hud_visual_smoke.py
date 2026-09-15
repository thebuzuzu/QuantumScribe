"""Executa um smoke nativo do ciclo de vida visual do HUD.

O runner usa somente Tkinter/Pillow já presentes no Core, não acessa áudio,
Whisper ou rede e encerra sozinho após percorrer todos os temas.
"""

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from localwhisper.ui import Popup  # noqa: E402

THEMES = (
    "dots",
    "atom",
    "atom_compact",
    "atom_centered",
    "atom_minimal",
    "liquid_orb",
)


def run_smoke(duration_ms: int) -> None:
    """Percorre os temas e as transições essenciais, falhando em callback Tk."""
    root = tk.Tk()
    root.withdraw()
    errors: list[tuple[type[BaseException], BaseException, object]] = []

    def report_callback_exception(exc_type, exc_value, exc_traceback) -> None:
        errors.append((exc_type, exc_value, exc_traceback))
        root.destroy()

    root.report_callback_exception = report_callback_exception
    popup = Popup(root, on_cancel=lambda: None, get_amplitude=lambda: 0.18)
    interval = max(120, duration_ms)

    def show_theme(index: int) -> None:
        if errors:
            return
        if index >= len(THEMES):
            popup.hide()
            root.after(0, root.destroy)
            return

        theme = THEMES[index]
        popup.show_recording(theme=theme, color="#0A84FF")
        root.after(interval, lambda: popup.show_processing_with_progress(0.1))
        root.after(interval * 2, popup.complete_progress)
        root.after(interval * 3, lambda: (popup.hide(), show_theme(index + 1)))

    show_theme(0)
    root.mainloop()
    if errors:
        _exc_type, exc_value, _traceback = errors[0]
        raise RuntimeError(f"Falha no callback visual do tema: {exc_value}") from exc_value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--duration-ms",
        type=int,
        default=180,
        help="Duração aproximada de cada etapa do tema (padrão: 180 ms).",
    )
    args = parser.parse_args()
    if args.duration_ms < 1:
        parser.error("--duration-ms deve ser positivo")

    run_smoke(args.duration_ms)
    print(f"HUD visual smoke PASS: {len(THEMES)} temas e transições concluídos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
