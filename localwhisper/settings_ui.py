"""Interface Gráfica do Painel de Configurações do Quantum Scribe (v3 — Redesign Apple).

Redesign completo no estilo dos Ajustes do macOS/iOS:

1. Navegação hierárquica: barra lateral com categorias; cada categoria abre uma
   página; linhas com chevron (›) abrem subpáginas internas com botão "‹ Voltar" —
   opções dentro de opções, sem telas sobrepostas.
2. Aplicação instantânea: cada controle grava e aplica a configuração no momento
   em que é alterado. Toggles realmente ligam/desligam o recurso correspondente.
3. Temas dinâmicos: modo Escuro/Claro + cor de destaque selecionável (padrão
   violeta Quantum), aplicados a todos os componentes via localwhisper.theme.
4. Downloads com progresso percentual real e monotônico (barra que preenche
   gradualmente), via localwhisper.download_progress.
5. Comunicação premium: toasts discretos confirmam cada ação importante.
"""

from __future__ import annotations

import copy
import glob
import importlib.util
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable

from PIL import Image, ImageDraw, ImageTk

from .config import AppConfig, is_model_downloaded
from .diary import diary_dir, search_entries
from .download_progress import (
    download_snapshot_with_progress,
    download_whisper_with_progress,
    format_bytes,
)
from .hotkey import _parse_hotkey
from .rewriter import _PINNED_REVISIONS
from .startup import supports_startup
from .theme import ACCENT_PRESETS, DEFAULT_ACCENT, Theme, build_theme, font_family

_HOTKEY_FIELDS = {
    "hotkey": "Ditado Normal",
    "hotkey_translate": "Ditado + Traduzir",
    "hotkey_auto_send": "Ditado + Enviar",
    "hotkey_quantum_brain": "Ditado + Quantum Brain",
}
_HOTKEY_ALIASES = {
    "control": "ctrl",
    "windows": "win",
    "super": "win",
    "cmd": "win",
}


def hotkey_conflict(config: AppConfig, field: str, value: str) -> str | None:
    """Retorna o rótulo de um atalho equivalente já em uso, se houver."""
    candidate = frozenset(
        _HOTKEY_ALIASES.get(part.strip().lower(), part.strip().lower())
        for part in value.split("+")
    )
    for other_field, label in _HOTKEY_FIELDS.items():
        if other_field == field:
            continue
        other_value = str(getattr(config, other_field, "") or "").strip()
        if not other_value:
            continue
        other = frozenset(
            _HOTKEY_ALIASES.get(part.strip().lower(), part.strip().lower())
            for part in other_value.split("+")
        )
        if candidate == other:
            return label
    return None


def get_project_root() -> Path:
    """Retorna a pasta do aplicativo para exibição e abertura na tela Sobre."""
    return Path(__file__).resolve().parents[1]


def load_or_generate_icon() -> Image.Image:
    """Carrega o ícone oficial em assets/icon.png ou desenha programaticamente se não existir."""
    assets_dir = Path(__file__).parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    icon_path = assets_dir / "icon.png"

    if icon_path.exists():
        try:
            return Image.open(icon_path)
        except Exception:
            pass

    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 248, 248), fill=(10, 11, 14, 255), outline=None)
    draw.ellipse((8, 8, 248, 248), fill=None, outline=(255, 96, 0, 255), width=6)
    orb_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    orb_draw = ImageDraw.Draw(orb_img)
    orb_draw.ellipse((40, 113, 216, 143), fill=None, outline=(255, 120, 40, 120), width=3)
    img.alpha_composite(orb_img)
    img.alpha_composite(orb_img.rotate(60, resample=Image.Resampling.BICUBIC))
    img.alpha_composite(orb_img.rotate(-60, resample=Image.Resampling.BICUBIC))
    draw.rounded_rectangle((108, 70, 148, 140), radius=15, fill=(255, 96, 0, 255))
    draw.rounded_rectangle((114, 76, 142, 100), radius=6, fill=(55, 60, 72, 255))
    draw.arc((96, 95, 160, 155), start=0, end=180, fill=(255, 96, 0, 255), width=4)
    draw.line((128, 155, 128, 185), fill=(255, 96, 0, 255), width=5)
    draw.line((100, 185, 156, 185), fill=(255, 96, 0, 255), width=5)
    draw.ellipse((190, 95, 202, 107), fill=(255, 238, 128, 255), outline=None)
    draw.ellipse((54, 95, 66, 107), fill=(255, 238, 128, 255), outline=None)
    draw.ellipse((122, 210, 134, 222), fill=(255, 238, 128, 255), outline=None)

    try:
        img.save(icon_path, "PNG")
    except Exception:
        pass

    return img


# ---------------------------------------------------------------------------
# Catálogos de opções
# ---------------------------------------------------------------------------

MODELS_MAP: dict[str, dict[str, str]] = {
    "tiny": {
        "id": "tiny",
        "name": "Super Leve (Tiny)",
        "desc": "Transcreve muito rápido, mas pode errar pontuação e termos complexos.",
        "size": "~75 MB",
    },
    "base": {
        "id": "base",
        "name": "Leve (Base)",
        "desc": "Bom equilíbrio entre velocidade e precisão básica.",
        "size": "~145 MB",
    },
    "small": {
        "id": "small",
        "name": "Equilibrado (Small)",
        "desc": "Ótima precisão e velocidade para o uso diário.",
        "size": "~460 MB",
    },
    "medium": {
        "id": "medium",
        "name": "Alto Desempenho (Medium)",
        "desc": "Excelente precisão, ideal para termos técnicos. Recomendado.",
        "size": "~1,5 GB",
    },
    "large-v3": {
        "id": "large-v3",
        "name": "Máxima Precisão (Large-v3)",
        "desc": "Precisão absoluta; consome mais memória de GPU/RAM.",
        "size": "~3,0 GB",
    },
}

LANGUAGES: list[tuple[str, str]] = [
    ("auto", "Detecção Automática"),
    ("pt", "Português (Brasil)"),
    ("en", "Inglês"),
    ("es", "Espanhol"),
    ("fr", "Francês"),
    ("de", "Alemão"),
    ("it", "Italiano"),
]

DEVICES: list[tuple[str, str, str]] = [
    ("auto", "Automático", "Detecta a GPU NVIDIA e usa CPU quando não houver suporte."),
    ("cuda", "GPU (CUDA)", "Máximo desempenho em placas NVIDIA compatíveis."),
    ("cpu", "CPU", "Funciona em qualquer computador; um pouco mais lento."),
]

COMPUTE_TYPES: list[tuple[str, str, str]] = [
    ("auto", "Automática", "Seleciona a precisão mais segura para o seu hardware."),
    ("int8", "Int8 (leve)", "Menor consumo de memória com ótima velocidade."),
    ("float16", "Float16 (precisa)", "Maior precisão em GPUs compatíveis."),
]

HUD_THEMES: list[tuple[str, str, str]] = [
    ("atom_centered", "Átomo Centralizado", "Somente o átomo, centralizado no indicador."),
    ("liquid_orb", "Liquid Orb", "Orbe líquido com brilho de vidro e movimento orgânico."),
    ("prismatic_bubble", "Prismatic Bubble", "Bubble prismático de duas lobas e aro cromático."),
]

ENHANCE_PROFILES: list[tuple[str, str, str]] = [
    ("fast", "Rápido", "Apenas normalização de volume. Quase nenhum custo de CPU."),
    ("balanced", "Equilibrado", "Filtro de graves + normalização. Recomendado."),
    ("quality", "Máxima Qualidade", "Redução de ruído espectral completa. Mais lento."),
]

SILENCE_OPTIONS: list[tuple[int, str]] = [
    (250, "250 ms — corta rápido, frases curtas"),
    (350, "350 ms — equilíbrio (padrão)"),
    (500, "500 ms — tolera pausas maiores"),
    (700, "700 ms — ideal para fala lenta"),
]

TONES: list[tuple[str, str, str]] = [
    ("natural", "Natural", "Corrige ortografia e pontuação mantendo 100% das suas palavras."),
    ("formal", "Formal", "Reescreve com linguagem profissional, ideal para e-mails."),
    ("developer", "Desenvolvedor", "Preserva jargões técnicos e termos em inglês."),
]

DEFAULT_WHISPER_PROMPTS = {
    "natural": "",
    "formal": "Linguagem formal, regras cultas.",
    "developer": "Desenvolvedor de software, termos em inglês, camelCase, Python, React.",
}
DEFAULT_LLM_PROMPTS = {
    "natural": "Corrija ortografia, acentuação e pontuação básicas. Mantenha 100% das palavras originais, a estrutura e a coloquialidade do ditado.",
    "formal": "Reescreva com linguagem formal, profissional e vocabulário empresarial. Corrija a gramática e remova gírias.",
    "developer": "Mantenha os jargões de programação em inglês e corrija a estrutura do texto para ficar claro e técnico.",
}


# ---------------------------------------------------------------------------
# Componentes premium reutilizáveis
# ---------------------------------------------------------------------------

class AppleSwitch(tk.Canvas):
    """Interruptor Liga/Desliga estilo Apple, desenhado com as cores do tema."""

    W, H = 46, 28

    def __init__(self, parent: tk.Widget, theme: Theme, variable: tk.BooleanVar,
                 command: Callable[[bool], None] | None = None, bg: str | None = None) -> None:
        super().__init__(parent, width=self.W, height=self.H, bd=0, highlightthickness=0,
                         bg=bg or theme.card_bg, cursor="hand2")
        self.theme = theme
        self.variable = variable
        self.command = command
        self.bind("<Button-1>", lambda _e: self.toggle())
        self._trace_id = self.variable.trace_add("write", lambda *_: self._draw())
        self.bind("<Destroy>", self._on_destroy)
        self._draw()

    def _on_destroy(self, event) -> None:
        if event.widget is self:
            try:
                self.variable.trace_remove("write", self._trace_id)
            except Exception:
                pass

    def toggle(self) -> None:
        self.variable.set(not self.variable.get())
        if self.command:
            self.command(self.variable.get())

    def _draw(self) -> None:
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        self.delete("all")
        on = bool(self.variable.get())
        t = self.theme
        track = t.accent if on else t.track
        self.create_oval(2, 2, self.H - 2, self.H - 2, fill=track, outline="")
        self.create_oval(self.W - self.H + 2, 2, self.W - 2, self.H - 2, fill=track, outline="")
        self.create_rectangle(self.H // 2, 2, self.W - self.H // 2, self.H - 2, fill=track, outline="")
        knob_r = self.H - 6
        if on:
            x0 = self.W - knob_r - 3
        else:
            x0 = 3
        self.create_oval(x0, 3, x0 + knob_r, 3 + knob_r, fill="#FFFFFF", outline="")


class ColorSwatch(tk.Canvas):
    """Círculo de cor selecionável com marca de seleção, estilo seletor do macOS."""

    def __init__(self, parent: tk.Widget, theme: Theme, color: str, size: int = 30,
                 selected: bool = False, command: Callable[[], None] | None = None,
                 bg: str | None = None) -> None:
        super().__init__(parent, width=size + 8, height=size + 8, bd=0, highlightthickness=0,
                         bg=bg or theme.card_bg, cursor="hand2")
        self.theme = theme
        self.color = color
        self.size = size
        self.selected = selected
        self.command = command
        self.bind("<Button-1>", lambda _e: self._clicked())
        self._draw()

    def _clicked(self) -> None:
        if self.command:
            self.command()

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        pad = 4
        d = self.size
        if self.selected:
            self.create_oval(1, 1, d + 7, d + 7, outline=self.theme.accent, width=2)
        self.create_oval(pad, pad, pad + d, pad + d, fill=self.color, outline=self.theme.border)
        if self.selected:
            cx, cy = pad + d / 2, pad + d / 2
            self.create_text(cx, cy, text="✓", fill="#FFFFFF", font=("Segoe UI Bold", 11))


class SegmentedControl(tk.Frame):
    """Controle segmentado estilo iOS/macOS (ex.: Escuro | Claro)."""

    def __init__(self, parent: tk.Widget, theme: Theme, options: list[tuple[str, str]],
                 current: str, command: Callable[[str], None], font_name: str,
                 bg: str | None = None) -> None:
        super().__init__(parent, bg=bg or theme.input_bg,
                         highlightthickness=1, highlightbackground=theme.border)
        self.theme = theme
        self.command = command
        self.current = current
        self._buttons: dict[str, tk.Label] = {}
        for key, label in options:
            lbl = tk.Label(
                self, text=label, font=(font_name, 10), padx=18, pady=5,
                bg=self.theme.input_bg, fg=self.theme.muted, cursor="hand2",
            )
            lbl.pack(side="left", padx=2, pady=2)
            lbl.bind("<Button-1>", lambda _e, k=key: self.select(k))
            self._buttons[key] = lbl
        self._refresh()

    def select(self, key: str) -> None:
        if key == self.current:
            return
        self.current = key
        self._refresh()
        self.command(key)

    def _refresh(self) -> None:
        for key, lbl in self._buttons.items():
            if key == self.current:
                lbl.configure(bg=self.theme.card_bg, fg=self.theme.text,
                              font= lbl.cget("font"))
            else:
                lbl.configure(bg=self.theme.input_bg, fg=self.theme.muted)


class Toast(tk.Label):
    """Notificação discreta exibida na base da janela, estilo banner do macOS."""

    def __init__(self, parent: tk.Widget, theme: Theme, message: str, kind: str = "success") -> None:
        colors = {"success": theme.success, "error": theme.danger, "info": theme.accent}
        dot = {"success": "✓", "error": "✕", "info": "●"}.get(kind, "●")
        super().__init__(
            parent, text=f" {dot}  {message} ",
            font=("Segoe UI Semibold", 10),
            fg=theme.text, bg=theme.card_bg,
            padx=16, pady=9,
            highlightthickness=1, highlightbackground=colors.get(kind, theme.accent),
        )


# ---------------------------------------------------------------------------
# Janela principal de Configurações
# ---------------------------------------------------------------------------

class SettingsWindow(tk.Toplevel):
    """Janela de configurações premium estilo Apple, com aplicação instantânea."""

    SIDEBAR_SECTIONS: list[tuple[str, str, str]] = [
        ("appearance", "◐", "Aparência"),
        ("dictation", "🎙", "Ditado"),
        ("audio", "🎧", "Microfone e Áudio"),
        ("ai", "✦", "Inteligência Artificial"),
        ("shortcuts", "⌨", "Atalhos"),
        ("brain", "🧠", "Quantum Brain"),
        ("storage", "💾", "Armazenamento"),
        ("system", "⚙", "Sistema"),
        ("about", "ℹ", "Sobre"),
    ]

    SECTION_TITLES: dict[str, tuple[str, str]] = {
        "appearance": ("Aparência", "Personalize o tema, as cores e o indicador flutuante."),
        "dictation": ("Ditado", "Modelo de transcrição, idioma e estilo do texto."),
        "ai": ("Inteligência Artificial", "Reescrita inteligente, tons e aprendizado."),
        "audio": ("Microfone e Áudio", "Entrada de som, aprimoramento e streaming."),
        "shortcuts": ("Atalhos", "Teclas de atalho globais do aplicativo."),
        "brain": ("Quantum Brain", "Seu segundo cérebro: notas, sínteses e projetos."),
        "storage": ("Armazenamento", "Histórico local de transcrições."),
        "system": ("Sistema", "Inicialização e comportamento do aplicativo."),
        "about": ("Sobre", "Versão, sistema e créditos."),
    }

    def __init__(self, parent: tk.Tk, current_config: AppConfig,
                 on_save: Callable[[AppConfig], None],
                 on_install_update: Callable[[Path, str], None] | None = None) -> None:
        super().__init__(parent)
        self.on_save_callback = on_save
        self.on_install_update_callback = on_install_update
        self._cfg: AppConfig = copy.deepcopy(current_config)

        # Estado de tema e tipografia
        self.theme: Theme = build_theme(
            getattr(self._cfg, "theme_mode", "dark"),
            getattr(self._cfg, "accent_color", DEFAULT_ACCENT),
        )
        self.font_name = font_family(self)

        # Estado operacional
        self._test_stream = None
        self._test_stream_active = False
        self._smooth_level = 0.0
        self._test_amplitude = 0.0
        self._listed_files: list[str] = []
        self._dl_active = False          # Download de modelo Whisper em andamento
        self._llm_dl_active = False      # Download do Mini-LLM em andamento
        self._pages: dict[str, tk.Frame] = {}
        self._page_builders: dict[str, Callable[[tk.Widget], tk.Frame]] = {}
        self._page_parents: dict[str, str] = {}
        self._current_page = ""
        self._toast_after_id: str | None = None
        self._update_active = False
        self._update_status_text = "Consulte o GitHub para procurar uma versão mais recente."
        self._update_status_label: tk.Label | None = None
        self._update_button: tk.Label | None = None

        # Variáveis Tkinter espelhando a configuração (widgets reativos)
        cfg = self._cfg
        self.paste_var = tk.BooleanVar(value=cfg.auto_paste)
        self.sounds_var = tk.BooleanVar(value=cfg.play_sounds)
        self.sound_volume_var = tk.DoubleVar(value=cfg.sound_volume)
        self.literal_mode_var = tk.BooleanVar(value=cfg.literal_mode)
        self.punctuation_assist_var = tk.BooleanVar(value=cfg.punctuation_assist)
        self.learning_var = tk.BooleanVar(value=cfg.continuous_learning)
        self.rewriter_var = tk.BooleanVar(value=cfg.use_llm_rewriter)
        self.streaming_var = tk.BooleanVar(value=cfg.streaming_mode)
        self.audio_enhance_var = tk.BooleanVar(value=cfg.audio_enhance)
        self.remove_stutters_var = tk.BooleanVar(value=cfg.remove_stutters)
        self.remove_fillers_var = tk.BooleanVar(value=cfg.remove_fillers)
        self.quantum_brain_enabled_var = tk.BooleanVar(value=cfg.quantum_brain_enabled)
        self.quantum_brain_also_paste_var = tk.BooleanVar(value=cfg.quantum_brain_also_paste)
        self.start_with_windows_var = tk.BooleanVar(value=getattr(cfg, "start_with_windows", False))

        try:
            self._icon_img = load_or_generate_icon()
            self._icon_photo = ImageTk.PhotoImage(self._icon_img)
            self.iconphoto(False, self._icon_photo)
        except Exception:
            self._icon_img = None

        self.title("Quantum Scribe — Ajustes")
        self.minsize(900, 600)

        width, height = 980, 660
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")

        self.withdraw()
        self._build_window()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.update_idletasks()
        self.deiconify()
        self.focus_set()

    # ------------------------------------------------------------------
    # Construção e reconstrução da janela (necessário ao trocar o tema)
    # ------------------------------------------------------------------

    def _build_window(self) -> None:
        t = self.theme
        self.configure(bg=t.bg)

        for child in self.winfo_children():
            child.destroy()
        self._pages.clear()
        self._page_builders.clear()
        self._page_parents.clear()

        self._setup_styles()

        self._body = tk.Frame(self, bg=t.bg)
        self._body.pack(fill="both", expand=True)

        self._sidebar = tk.Frame(self._body, bg=t.sidebar_bg, width=224)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)
        tk.Frame(self._body, bg=t.border, width=1).pack(side="left", fill="y")

        self._content = tk.Frame(self._body, bg=t.bg)
        self._content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._register_pages()

        if not self._current_page:
            self._current_page = "appearance"
        self._show(self._current_page, update_sidebar=True)

    def _setup_styles(self) -> None:
        t = self.theme
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=t.input_bg,
            troughcolor=t.bg,
            bordercolor=t.bg,
            lightcolor=t.bg,
            darkcolor=t.bg,
            arrowsize=0,
        )
        style.map("Vertical.TScrollbar", background=[("active", t.accent)])

        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=t.track,
            background=t.accent,
            bordercolor=t.track,
            lightcolor=t.accent,
            darkcolor=t.accent,
            thickness=8,
        )

        style.configure(
            "Treeview",
            background=t.input_bg,
            foreground=t.text,
            fieldbackground=t.input_bg,
            bordercolor=t.border,
            borderwidth=0,
            font=(self.font_name, 9),
        )
        style.configure(
            "Treeview.Heading",
            background=t.card_bg,
            foreground=t.muted,
            relief="flat",
            font=(self.font_name, 9, "bold"),
        )
        style.map("Treeview", background=[("selected", t.accent)],
                  foreground=[("selected", t.on_accent)])

    # ------------------------------------------------------------------
    # Navegação (categorias → páginas → subpáginas)
    # ------------------------------------------------------------------

    def _register_page(self, page_id: str, builder: Callable[[tk.Widget], tk.Frame],
                       parent: str | None = None) -> None:
        self._page_builders[page_id] = builder
        if parent:
            self._page_parents[page_id] = parent

    def _show(self, page_id: str, update_sidebar: bool = False) -> None:
        if self._current_page == page_id and page_id in self._pages:
            return

        if self._current_page == "sub_mic":
            self._stop_test_stream()

        for page in self._pages.values():
            page.pack_forget()

        self._current_page = page_id

        if page_id not in self._pages:
            builder = self._page_builders.get(page_id)
            if builder is None:
                return
            self._pages[page_id] = builder(self._content)

        self._pages[page_id].pack(fill="both", expand=True)

        if update_sidebar:
            root_section = self._root_section_of(page_id)
            self._highlight_sidebar(root_section)

    def _root_section_of(self, page_id: str) -> str:
        while page_id in self._page_parents:
            page_id = self._page_parents[page_id]
        return page_id

    def _go_back(self) -> None:
        parent = self._page_parents.get(self._current_page)
        if parent:
            self._show(parent, update_sidebar=True)

    def _highlight_sidebar(self, section_id: str) -> None:
        t = self.theme
        for sid, widgets in self._sidebar_btns.items():
            active = sid == section_id
            bg = t.sidebar_active if active else t.sidebar_bg
            widgets["frame"].configure(bg=bg)
            widgets["icon"].configure(bg=bg, fg=t.accent if active else t.muted)
            widgets["text"].configure(
                bg=bg,
                fg=t.text if active else t.muted,
                font=(self.font_name, 10, "bold" if active else "normal"),
            )

    # ------------------------------------------------------------------
    # Barra lateral
    # ------------------------------------------------------------------

    def _build_sidebar(self) -> None:
        t = self.theme

        header = tk.Frame(self._sidebar, bg=t.sidebar_bg)
        header.pack(fill="x", padx=18, pady=(22, 14))

        if self._icon_img is not None:
            try:
                self._sidebar_icon = ImageTk.PhotoImage(
                    self._icon_img.resize((30, 30), Image.Resampling.LANCZOS))
                tk.Label(header, image=self._sidebar_icon, bg=t.sidebar_bg).pack(side="left")
            except Exception:
                pass

        tk.Label(
            header, text="Ajustes", font=(self.font_name, 15, "bold"),
            fg=t.text, bg=t.sidebar_bg,
        ).pack(side="left", padx=(10, 0))

        self._sidebar_btns: dict[str, dict[str, tk.Widget]] = {}
        for sid, icon, text in self.SIDEBAR_SECTIONS:
            self._sidebar_button(sid, icon, text)

    def _sidebar_button(self, sid: str, icon: str, text: str) -> None:
        t = self.theme
        frame = tk.Frame(self._sidebar, bg=t.sidebar_bg, cursor="hand2")
        frame.pack(fill="x", padx=10, pady=1)

        icon_lbl = tk.Label(frame, text=icon, font=("Segoe UI Symbol", 12),
                            fg=t.muted, bg=t.sidebar_bg, width=3, anchor="center")
        icon_lbl.pack(side="left", padx=(8, 4), pady=8)

        text_lbl = tk.Label(frame, text=text, font=(self.font_name, 10),
                            fg=t.muted, bg=t.sidebar_bg, anchor="w")
        text_lbl.pack(side="left", fill="x", expand=True, pady=8)

        self._sidebar_btns[sid] = {"frame": frame, "icon": icon_lbl, "text": text_lbl}

        for w in (frame, icon_lbl, text_lbl):
            w.bind("<Button-1>", lambda _e, s=sid: self._show(s, update_sidebar=True))
            w.bind("<Enter>", lambda _e, s=sid: self._sidebar_hover(s, True))
            w.bind("<Leave>", lambda _e, s=sid: self._sidebar_hover(s, False))

    def _sidebar_hover(self, sid: str, entering: bool) -> None:
        if self._root_section_of(self._current_page) == sid:
            return
        t = self.theme
        widgets = self._sidebar_btns[sid]
        bg = t.hover_bg if entering else t.sidebar_bg
        widgets["frame"].configure(bg=bg)
        widgets["icon"].configure(bg=bg)
        widgets["text"].configure(bg=bg)

    # ------------------------------------------------------------------
    # Infraestrutura de páginas e linhas
    # ------------------------------------------------------------------

    def _page_shell(self, title: str, subtitle: str,
                    back_to: str | None = None) -> tuple[tk.Frame, tk.Frame]:
        """Cria o contêiner de página com cabeçalho e área rolável."""
        t = self.theme
        page = tk.Frame(self._content, bg=t.bg)

        header = tk.Frame(page, bg=t.bg)
        header.pack(fill="x", padx=28, pady=(22, 6))

        if back_to:
            back = tk.Label(
                header, text=f"‹ {self.SECTION_TITLES.get(back_to, ('Voltar', ''))[0]}",
                font=(self.font_name, 11, "bold"), fg=t.accent, bg=t.bg, cursor="hand2",
            )
            back.pack(anchor="w", pady=(0, 6))
            back.bind("<Button-1>", lambda _e: self._go_back())
            back.bind("<Enter>", lambda _e: back.configure(fg=t.accent_hover))
            back.bind("<Leave>", lambda _e: back.configure(fg=t.accent))

        tk.Label(header, text=title, font=(self.font_name, 20, "bold"),
                 fg=t.text, bg=t.bg).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, font=(self.font_name, 10),
                     fg=t.muted, bg=t.bg).pack(anchor="w", pady=(2, 0))

        scroll = ScrollArea(page, theme_bg=t.bg)
        scroll.pack(fill="both", expand=True, padx=28, pady=(10, 20))
        return page, scroll.inner

    def _card(self, parent: tk.Widget, title: str | None = None) -> tk.Frame:
        t = self.theme
        if title:
            tk.Label(
                parent, text=title.upper(), font=(self.font_name, 8, "bold"),
                fg=t.muted, bg=t.bg, anchor="w",
            ).pack(fill="x", pady=(14, 6), padx=4)
        card = tk.Frame(parent, bg=t.card_bg,
                        highlightthickness=1, highlightbackground=t.border)
        card.pack(fill="x", pady=(0, 6))
        return card

    def _separator(self, card: tk.Frame) -> None:
        if card.winfo_children():
            tk.Frame(card, bg=self.theme.border, height=1).pack(fill="x", padx=16)

    def _row_base(self, card: tk.Frame, label: str, desc: str | None = None) -> tk.Frame:
        self._separator(card)
        t = self.theme
        row = tk.Frame(card, bg=t.card_bg)
        row.pack(fill="x", padx=16, pady=11)
        row.columnconfigure(0, weight=1)

        text_box = tk.Frame(row, bg=t.card_bg)
        text_box.grid(row=0, column=0, sticky="w")
        tk.Label(text_box, text=label, font=(self.font_name, 10, "bold"),
                 fg=t.text, bg=t.card_bg, anchor="w").pack(fill="x")
        if desc:
            tk.Label(text_box, text=desc, font=(self.font_name, 8),
                     fg=t.muted, bg=t.card_bg, anchor="w", justify="left",
                     wraplength=430).pack(fill="x", pady=(1, 0))
        return row

    def _row_toggle(self, card: tk.Frame, label: str, desc: str,
                    variable: tk.BooleanVar, field: str,
                    on_change: Callable[[bool], None] | None = None,
                    toast: str | None = None) -> tk.Frame:
        row = self._row_base(card, label, desc)

        def changed(value: bool) -> None:
            saved = self._set(field, value, toast=toast)
            if saved and on_change:
                on_change(value)

        switch = AppleSwitch(row, self.theme, variable, command=changed, bg=self.theme.card_bg)
        switch.grid(row=0, column=1, sticky="e")
        return row

    def _row_nav(self, card: tk.Frame, label: str, desc: str | None,
                 value: str | Callable[[], str], target: str) -> tk.Frame:
        row = self._row_base(card, label, desc)
        t = self.theme

        right = tk.Frame(row, bg=t.card_bg, cursor="hand2")
        right.grid(row=0, column=1, sticky="e")

        value_lbl = tk.Label(right, text=value if isinstance(value, str) else value(),
                             font=(self.font_name, 10), fg=t.muted, bg=t.card_bg)
        value_lbl.pack(side="left", padx=(0, 6))
        if callable(value):
            row._value_refresher = lambda: value_lbl.configure(text=value())  # type: ignore[attr-defined]

        chevron = tk.Label(right, text="›", font=(self.font_name, 14),
                           fg=t.muted, bg=t.card_bg)
        chevron.pack(side="left")

        def go(_event=None) -> None:
            self._show(target, update_sidebar=True)

        for w in (row, right, value_lbl, chevron):
            w.bind("<Button-1>", go)
            w.configure(cursor="hand2")
        row.bind("<Enter>", lambda _e: self._row_hover(row, True))
        row.bind("<Leave>", lambda _e: self._row_hover(row, False))
        return row

    def _row_hover(self, row: tk.Frame, entering: bool) -> None:
        # Hover sutil: mantém o card, apenas o cursor já indica clicabilidade.
        pass

    def _row_action(self, card: tk.Frame, label: str, desc: str | None,
                    button_text: str, command: Callable[[], None],
                    kind: str = "primary") -> tk.Frame:
        row = self._row_base(card, label, desc)
        t = self.theme
        styles = {
            "primary": (t.accent, t.on_accent, t.accent_hover),
            "secondary": (t.input_bg, t.text, t.hover_bg),
            "danger": (t.input_bg, t.danger, t.hover_bg),
        }
        bg, fg, hover = styles.get(kind, styles["primary"])
        btn = tk.Label(row, text=button_text, font=(self.font_name, 9, "bold"),
                       bg=bg, fg=fg, padx=14, pady=6, cursor="hand2")
        btn.grid(row=0, column=1, sticky="e")
        btn.bind("<Button-1>", lambda _e: command())
        btn.bind("<Enter>", lambda _e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda _e: btn.configure(bg=bg))
        return row

    def _button(self, parent: tk.Widget, text: str, command: Callable[[], None],
                kind: str = "primary") -> tk.Label:
        t = self.theme
        styles = {
            "primary": (t.accent, t.on_accent, t.accent_hover),
            "secondary": (t.input_bg, t.text, t.hover_bg),
            "danger": (t.input_bg, t.danger, t.hover_bg),
        }
        bg, fg, hover = styles.get(kind, styles["primary"])
        btn = tk.Label(parent, text=text, font=(self.font_name, 9, "bold"),
                       bg=bg, fg=fg, padx=14, pady=7, cursor="hand2")
        btn.bind("<Button-1>", lambda _e: command())
        btn.bind("<Enter>", lambda _e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda _e: btn.configure(bg=bg))
        return btn

    def _styled_entry(self, parent: tk.Widget, value: str, width: int = 24) -> tk.Entry:
        t = self.theme
        entry = tk.Entry(
            parent, bg=t.input_bg, fg=t.text, font=(self.font_name, 10),
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=t.border, highlightcolor=t.accent,
            insertbackground=t.text, width=width,
        )
        entry.insert(0, value)
        return entry

    def _styled_text(self, parent: tk.Widget, height: int = 4) -> tk.Text:
        t = self.theme
        return tk.Text(
            parent, height=height, bg=t.input_bg, fg=t.text, font=(self.font_name, 10),
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=t.border, highlightcolor=t.accent,
            insertbackground=t.text, wrap="word",
        )

    # ------------------------------------------------------------------
    # Aplicação instantânea e comunicação
    # ------------------------------------------------------------------

    def _set(self, field: str, value, toast: str | None = None,
             toast_kind: str = "success") -> bool:
        """Grava o campo na configuração e aplica imediatamente no app."""
        previous_cfg = copy.deepcopy(self._cfg)
        setattr(self._cfg, field, value)
        # AppConfig também é atualizado fora do construtor pela UI. Reaplique
        # invariantes aqui para que um controle incompatível nunca pareça ativo.
        self._cfg.normalize()
        for config_field, variable_name in (
            ("remove_stutters", "remove_stutters_var"),
            ("remove_fillers", "remove_fillers_var"),
            ("continuous_learning", "learning_var"),
            ("use_llm_rewriter", "rewriter_var"),
            ("start_with_windows", "start_with_windows_var"),
        ):
            variable = getattr(self, variable_name, None)
            if variable is not None:
                variable.set(getattr(self._cfg, config_field))
        try:
            self.on_save_callback(self._cfg)
        except Exception as error:
            self._cfg = previous_cfg
            for config_field, variable_name in (
                ("remove_stutters", "remove_stutters_var"),
                ("remove_fillers", "remove_fillers_var"),
                ("continuous_learning", "learning_var"),
                ("use_llm_rewriter", "rewriter_var"),
                ("start_with_windows", "start_with_windows_var"),
            ):
                variable = getattr(self, variable_name, None)
                if variable is not None:
                    variable.set(getattr(self._cfg, config_field))
            self._toast(f"Não foi possível salvar: {error}", "error")
            return False
        if toast:
            self._toast(toast, toast_kind)
        return True

    def _toast(self, message: str, kind: str = "success") -> None:
        if self._toast_after_id:
            try:
                self.after_cancel(self._toast_after_id)
            except Exception:
                pass
        toast = Toast(self, self.theme, message, kind)
        toast.place(relx=0.5, rely=1.0, x=0, y=-28, anchor="s")
        toast.lift()
        self._toast_after_id = self.after(2400, toast.destroy)

    def _refresh_theme(self, toast: str | None = None) -> None:
        """Reconstrói a janela inteira com o novo tema (modo/cor alterados)."""
        self.theme = build_theme(
            getattr(self._cfg, "theme_mode", "dark"),
            getattr(self._cfg, "accent_color", DEFAULT_ACCENT),
        )
        current = self._current_page
        self._current_page = current
        self._build_window()
        if toast:
            self._toast(toast)

    # ------------------------------------------------------------------
    # Encerramento seguro
    # ------------------------------------------------------------------

    def destroy(self) -> None:
        self._stop_test_stream()
        super().destroy()


class ScrollArea(tk.Frame):
    """Área rolável suave baseada em Canvas, com rolagem por roda do mouse."""

    def __init__(self, parent: tk.Widget, theme_bg: str | None = None, **kwargs) -> None:
        bg = theme_bg or "#0A0B0D"
        super().__init__(parent, bg=bg, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                       command=self.canvas.yview, style="Vertical.TScrollbar")
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.inner.bind("<Configure>",
                        lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", self._fit_width)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

    def _fit_width(self, event) -> None:
        self.canvas.itemconfig(self._window_id, width=event.width)

    def _bind_wheel(self, _event) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)

    def _unbind_wheel(self, _event) -> None:
        self.canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, event) -> None:
        try:
            if event.widget.winfo_class() in ("Text", "Treeview"):
                return
        except Exception:
            pass
        try:
            self.canvas.yview_scroll(int(-event.delta / 120), "units")
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Páginas: registro e construtores
# ---------------------------------------------------------------------------

def _register_pages(self: SettingsWindow) -> None:
    self._register_page("appearance", self._page_appearance)
    self._register_page("dictation", self._page_dictation)
    self._register_page("audio", self._page_audio)
    self._register_page("ai", self._page_ai)
    self._register_page("shortcuts", self._page_shortcuts)
    self._register_page("brain", self._page_brain)
    self._register_page("storage", self._page_storage)
    self._register_page("system", self._page_system)
    self._register_page("about", self._page_about)
    # Subpáginas de Ditado
    self._register_page("sub_model", self._page_sub_model, parent="dictation")
    self._register_page("sub_language", self._page_sub_language, parent="dictation")
    self._register_page("sub_hardware", self._page_sub_hardware, parent="dictation")
    self._register_page("sub_prompt", self._page_sub_prompt, parent="dictation")
    self._register_page("sub_fillers", self._page_sub_fillers, parent="dictation")
    # Subpáginas de Aparência
    self._register_page("sub_hud_theme", self._page_sub_hud_theme, parent="appearance")
    self._register_page("sub_atom_color", self._page_sub_atom_color, parent="appearance")
    # Subpáginas de IA
    self._register_page("sub_tone", self._page_sub_tone, parent="ai")
    self._register_page("sub_tone_editor", self._page_sub_tone_editor, parent="sub_tone")
    # Subpáginas de Áudio
    self._register_page("sub_mic", self._page_sub_mic, parent="audio")
    self._register_page("sub_profile", self._page_sub_profile, parent="audio")
    self._register_page("sub_silence", self._page_sub_silence, parent="audio")


def _rebuild_page(self: SettingsWindow, page_id: str) -> None:
    """Destrói e reconstrói uma página (para refletir novos estados)."""
    page = self._pages.pop(page_id, None)
    if page is not None:
        page.destroy()
    if self._current_page == page_id:
        self._show(page_id)


SettingsWindow._register_pages = _register_pages
SettingsWindow._rebuild_page = _rebuild_page


# ---------------------------------------------------------------------------
# PÁGINA: APARÊNCIA
# ---------------------------------------------------------------------------

def _page_appearance(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell(*self.SECTION_TITLES["appearance"])

    # --- Tema (modo Escuro / Claro) ---
    card = self._card(body, "Tema")
    row = self._row_base(card, "Modo de Exibição",
                         "Escolha entre a aparência escura ou clara em todo o app.")
    mode = getattr(self._cfg, "theme_mode", "dark")

    def on_mode_change(key: str) -> None:
        self._set("theme_mode", key)
        self._refresh_theme(toast="Tema claro ativado" if key == "light" else "Tema escuro ativado")

    seg = SegmentedControl(row, t, [("dark", "Escuro"), ("light", "Claro")],
                           mode, on_mode_change, self.font_name)
    seg.grid(row=0, column=1, sticky="e")

    # --- Cor de destaque ---
    card = self._card(body, "Cor de Destaque")
    row = self._row_base(card, "Cor do Aplicativo",
                         "A cor de destaque tinge botões, toggles e barras de progresso.")
    swatches = tk.Frame(row, bg=t.card_bg)
    swatches.grid(row=0, column=1, sticky="e")

    current_accent = getattr(self._cfg, "accent_color", DEFAULT_ACCENT).upper()
    self._swatch_widgets: list[ColorSwatch] = []

    def pick(hex_color: str) -> None:
        self._set("accent_color", hex_color)
        self._refresh_theme(toast="Cor de destaque atualizada")

    for name, hex_color in ACCENT_PRESETS:
        sw = ColorSwatch(swatches, t, hex_color,
                         selected=(hex_color.upper() == current_accent),
                         command=lambda c=hex_color: pick(c))
        sw.pack(side="left", padx=3)
        self._swatch_widgets.append(sw)

    # Amostra personalizada (seletor de cores do sistema)
    custom = tk.Canvas(swatches, width=38, height=38, bd=0, highlightthickness=0,
                       bg=t.card_bg, cursor="hand2")
    custom.pack(side="left", padx=3)
    known = {c.upper() for _, c in ACCENT_PRESETS}
    is_custom = current_accent not in known

    def draw_custom(selected: bool = False) -> None:
        custom.delete("all")
        if selected:
            custom.create_oval(1, 1, 37, 37, outline=t.accent, width=2)
        segments = ["#BF5AF2", "#FF2D78", "#0A84FF", "#30D158", "#FFD60A", "#FF6000"]
        for i, seg_color in enumerate(segments):
            custom.create_arc(4, 4, 34, 34, start=i * 60, extent=60,
                              fill=seg_color, outline="")
        if selected:
            custom.create_text(19, 19, text="✓", fill="#FFFFFF", font=("Segoe UI Bold", 10))

    draw_custom(is_custom)

    def pick_custom(_event=None) -> None:
        from tkinter import colorchooser
        result = colorchooser.askcolor(color=current_accent,
                                       title="Escolha a cor de destaque", parent=self)
        if result and result[1]:
            pick(result[1].upper())

    custom.bind("<Button-1>", pick_custom)

    # --- Indicador flutuante (HUD) ---
    card = self._card(body, "Indicador Flutuante (HUD)")

    self._row_nav(card, "Animação do HUD",
                  "Estilo visual exibido enquanto você dita.",
                  lambda: dict((k, n) for k, n, _d in HUD_THEMES).get(self._cfg.hud_theme, "Bolinhas"),
                  "sub_hud_theme")

    self._row_nav(card, "Cor do Átomo",
                  "Cor das órbitas e elétrons nos temas de átomo.",
                  lambda: self._cfg.atom_color.upper(), "sub_atom_color")

    note = tk.Label(
        body,
        text="As alterações de aparência são aplicadas imediatamente, sem reiniciar.",
        font=(self.font_name, 8, "italic"), fg=t.muted, bg=t.bg, anchor="w",
    )
    note.pack(fill="x", padx=4, pady=(10, 0))
    return page


SettingsWindow._page_appearance = _page_appearance


def _page_sub_hud_theme(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    page, body = self._page_shell("Animação do HUD",
                                  "Escolha como o indicador flutuante aparece durante o ditado.",
                                  back_to="appearance")
    card = self._card(body)
    for theme_id, name, desc in HUD_THEMES:
        self._radio_row(card, name, desc,
                        selected=(self._cfg.hud_theme == theme_id),
                        command=lambda tid=theme_id: self._select_hud_theme(tid))
    return page


SettingsWindow._page_sub_hud_theme = _page_sub_hud_theme


def _select_hud_theme(self: SettingsWindow, theme_id: str) -> None:
    self._set("hud_theme", theme_id, toast="Animação do HUD atualizada")
    self._rebuild_page("sub_hud_theme")


SettingsWindow._select_hud_theme = _select_hud_theme


def _page_sub_atom_color(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell("Cor do Átomo",
                                  "Escolha a cor das órbitas e elétrons do indicador.",
                                  back_to="appearance")
    card = self._card(body)
    row = self._row_base(card, "Cores Sugeridas", "Toque em uma cor para aplicar.")
    swatches = tk.Frame(row, bg=t.card_bg)
    swatches.grid(row=0, column=1, sticky="e")

    atom_presets = ["#BF5AF2", "#FF2D78", "#0A84FF", "#30D158", "#FFD60A", "#FF6000"]
    current = self._cfg.atom_color.upper()

    def pick(hex_color: str) -> None:
        self._set("atom_color", hex_color, toast="Cor do átomo atualizada")
        self._rebuild_page("sub_atom_color")

    for hex_color in atom_presets:
        sw = ColorSwatch(swatches, t, hex_color,
                         selected=(hex_color.upper() == current),
                         command=lambda c=hex_color: pick(c))
        sw.pack(side="left", padx=3)

    row2 = self._row_base(card, "Cor Personalizada", "Abra o seletor de cores do sistema.")
    self._button(row2, "Escolher Cor…", lambda: _pick_custom_atom(self), "secondary").grid(
        row=0, column=1, sticky="e")
    return page


def _pick_custom_atom(self: SettingsWindow) -> None:
    from tkinter import colorchooser
    result = colorchooser.askcolor(color=self._cfg.atom_color,
                                   title="Escolha a cor do átomo", parent=self)
    if result and result[1]:
        self._set("atom_color", result[1].upper(), toast="Cor do átomo atualizada")
        self._rebuild_page("sub_atom_color")


SettingsWindow._page_sub_atom_color = _page_sub_atom_color


# ---------------------------------------------------------------------------
# Linha de seleção única (radio) reutilizável nas subpáginas
# ---------------------------------------------------------------------------

def _radio_row(self: SettingsWindow, card: tk.Frame, label: str, desc: str | None,
               selected: bool, command: Callable[[], None],
               trailing: tk.Widget | None = None) -> tk.Frame:
    """Linha clicável com marcador de seleção estilo iOS (círculo + check)."""
    t = self.theme
    row = self._row_base(card, label, desc)

    mark = tk.Canvas(row, width=24, height=24, bd=0, highlightthickness=0, bg=t.card_bg)
    mark.grid(row=0, column=1, sticky="e", padx=(8, 0))

    def draw() -> None:
        mark.delete("all")
        if selected:
            mark.create_oval(2, 2, 22, 22, fill=t.accent, outline="")
            mark.create_text(12, 12, text="✓", fill=t.on_accent, font=("Segoe UI Bold", 10))
        else:
            mark.create_oval(2, 2, 22, 22, outline=t.border, width=2)

    draw()

    if trailing is not None:
        trailing.grid(row=0, column=2, sticky="e", padx=(8, 0))

    clickable = [row, mark]
    for child in row.winfo_children():
        if isinstance(child, tk.Frame):
            clickable.append(child)
            clickable.extend(child.winfo_children())
    for w in clickable:
        try:
            w.bind("<Button-1>", lambda _e: command())
            w.configure(cursor="hand2")
        except Exception:
            pass
    return row


SettingsWindow._radio_row = _radio_row


# ---------------------------------------------------------------------------
# PÁGINA: DITADO
# ---------------------------------------------------------------------------

def _page_dictation(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    page, body = self._page_shell(*self.SECTION_TITLES["dictation"])

    # --- Modelo de IA ---
    card = self._card(body, "Reconhecimento de Voz")

    self._row_nav(card, "Modelo de IA",
                  "Tamanho e precisão do modelo Whisper.",
                  lambda: MODELS_MAP.get(self._cfg.model, MODELS_MAP["medium"])["name"],
                  "sub_model")

    self._row_nav(card, "Idioma",
                  "Idioma falado durante o ditado.",
                  lambda: dict(LANGUAGES).get(self._cfg.language or "auto", "Detecção Automática"),
                  "sub_language")

    self._row_nav(card, "Hardware e Precisão",
                  "Processador e quantização usados na transcrição.",
                  lambda: dict((k, n) for k, n, _d in DEVICES).get(self._cfg.device, "Automático"),
                  "sub_hardware")

    if self.literal_mode_var.get():
        self._row_base(
            card,
            "Prompt Auxiliar",
            "Inativo durante a Transcrição Literal para preservar as palavras reconhecidas.",
        )
    else:
        self._row_nav(card, "Prompt Auxiliar",
                      "Vocabulário e regras ensinados ao modelo.",
                      "Editar", "sub_prompt")

    # --- Estilo do texto ---
    card = self._card(body, "Estilo do Texto")

    self._row_toggle(card, "Transcrição Literal",
                     "Preserva exatamente o que foi falado, sem correções automáticas.",
                     self.literal_mode_var, "literal_mode",
                     on_change=lambda _v: self._rebuild_page("dictation"),
                     toast=None)

    if self.literal_mode_var.get():
        self._row_toggle(card, "Assistência de Pontuação",
                         "Compatível com o modo literal: altera apenas pontuação, nunca palavras.",
                         self.punctuation_assist_var, "punctuation_assist")
        self._row_base(
            card,
            "Sem alterações de palavras",
            "Remoção de repetições e hesitações, aprendizado e reescrita por IA "
            "ficam desativados enquanto a transcrição literal estiver ativa.",
        )
    else:
        self._row_toggle(card, "Pontuação Inteligente",
                         "Insere pontos e interrogações pelas pausas naturais da fala.",
                         self.punctuation_assist_var, "punctuation_assist")

        self._row_toggle(card, "Remover Repetições",
                         "Limpa gagueiras e palavras duplicadas em sequência.",
                         self.remove_stutters_var, "remove_stutters")

        self._row_toggle(card, "Remover Hesitações",
                         "Remove sons como “hmm”, “ãh” e “eh” do texto final.",
                         self.remove_fillers_var, "remove_fillers",
                         on_change=lambda _v: self._rebuild_page("dictation"))

        if self.remove_fillers_var.get():
            self._row_nav(card, "Hesitações Personalizadas",
                          "Palavras extras a remover, separadas por vírgula.",
                          "Editar", "sub_fillers")
        else:
            self._row_base(
                card,
                "Hesitações Personalizadas",
                "Inativas — ative Remover Hesitações para editar a lista.",
            )

    # --- Saída ---
    card = self._card(body, "Saída do Texto")

    self._row_toggle(card, "Colar Automaticamente",
                     "Digita o texto no cursor assim que a transcrição termina. "
                     "Desligado, o texto vai apenas para a área de transferência.",
                     self.paste_var, "auto_paste")

    return page


SettingsWindow._page_dictation = _page_dictation


# ---------------------------------------------------------------------------
# SUBPÁGINA: MODELO DE IA (com download em percentual real)
# ---------------------------------------------------------------------------

def _page_sub_model(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell(
        "Modelo de IA",
        "Toque em um modelo para usá-lo. Modelos não instalados podem ser baixados aqui.",
        back_to="dictation")

    card = self._card(body)
    self._dl_rows: dict[str, dict[str, tk.Widget]] = {}

    for model_id, info in MODELS_MAP.items():
        downloaded = is_model_downloaded(model_id)
        selected = self._cfg.model == model_id

        status = "✓ Instalado" if downloaded else f"{info['size']} — não instalado"
        desc = f"{info['desc']}  ·  {status}"

        row = self._radio_row(
            card, info["name"], desc,
            selected=selected,
            command=lambda mid=model_id: self._select_model(mid),
        )

        widgets: dict[str, tk.Widget] = {"row": row}
        if not downloaded and not self._dl_active:
            btn = self._button(row, "Baixar", lambda mid=model_id: self._start_model_download(mid),
                               "primary")
            btn.grid(row=0, column=2, sticky="e", padx=(10, 0))
            widgets["button"] = btn
        self._dl_rows[model_id] = widgets

    # Área de progresso do download (aparece somente durante o download)
    self._dl_frame = tk.Frame(body, bg=t.card_bg,
                              highlightthickness=1, highlightbackground=t.border)
    self._dl_title = tk.Label(self._dl_frame, text="", font=(self.font_name, 10, "bold"),
                              fg=t.text, bg=t.card_bg, anchor="w")
    self._dl_title.pack(fill="x", padx=16, pady=(12, 2))
    self._dl_detail = tk.Label(self._dl_frame, text="", font=(self.font_name, 8),
                               fg=t.muted, bg=t.card_bg, anchor="w")
    self._dl_detail.pack(fill="x", padx=16)
    bar_row = tk.Frame(self._dl_frame, bg=t.card_bg)
    bar_row.pack(fill="x", padx=16, pady=(8, 12))
    self._dl_pct_var = tk.DoubleVar(value=0.0)
    self._dl_bar = ttk.Progressbar(bar_row, orient="horizontal", mode="determinate",
                                   variable=self._dl_pct_var, maximum=100.0,
                                   style="Accent.Horizontal.TProgressbar")
    self._dl_bar.pack(side="left", fill="x", expand=True)
    self._dl_pct_label = tk.Label(bar_row, text="0%", font=(self.font_name, 10, "bold"),
                                  fg=t.accent, bg=t.card_bg, width=5, anchor="e")
    self._dl_pct_label.pack(side="left", padx=(10, 0))

    if self._dl_active:
        self._dl_frame.pack(fill="x", pady=(10, 6))

    note = tk.Label(
        body,
        text="O download é retomado automaticamente se for interrompido.",
        font=(self.font_name, 8, "italic"), fg=t.muted, bg=t.bg, anchor="w",
    )
    note.pack(fill="x", padx=4, pady=(8, 0))
    return page


SettingsWindow._page_sub_model = _page_sub_model


def _select_model(self: SettingsWindow, model_id: str) -> None:
    if model_id == self._cfg.model:
        return
    name = MODELS_MAP.get(model_id, {}).get("name", model_id)
    if not is_model_downloaded(model_id):
        self._toast(
            f"Baixe o modelo {name} antes de ativá-lo.",
            kind="info",
        )
        return
    self._set("model", model_id, toast=f"Modelo {name} ativado")
    self._rebuild_page("sub_model")


SettingsWindow._select_model = _select_model


def _start_model_download(self: SettingsWindow, model_id: str) -> None:
    if self._dl_active:
        return
    self._dl_active = True

    info = MODELS_MAP.get(model_id, {})
    name = info.get("name", model_id)

    def on_progress(percent: float, downloaded: int, total: int) -> None:
        def update() -> None:
            if not self.winfo_exists():
                return
            try:
                self._dl_pct_var.set(percent)
                self._dl_pct_label.configure(text=f"{percent:.0f}%")
                if total > 0:
                    self._dl_detail.configure(
                        text=f"{format_bytes(downloaded)} de {format_bytes(total)}")
            except Exception:
                pass
        try:
            self.after(0, update)
        except Exception:
            pass

    def worker() -> None:
        from .model_manager import ModelDownloadError, ensure_model_downloaded
        error: Exception | None = None
        try:
            ensure_model_downloaded(
                model_id,
                downloader=lambda m, *, cache_dir, revision: download_whisper_with_progress(
                    m, cache_dir, on_progress, revision=revision),
            )
        except (ModelDownloadError, Exception) as exc:  # noqa: BLE001
            error = exc

        def finish() -> None:
            self._dl_active = False
            if error is None:
                self._toast(f"Modelo {name} instalado com sucesso")
            else:
                self._toast(f"Falha no download: {error}", kind="error")
            if self.winfo_exists():
                self._rebuild_page("sub_model")

        try:
            self.after(0, finish)
        except Exception:
            pass

    # Reconstrói a página para exibir a área de progresso no lugar dos botões
    self._rebuild_page("sub_model")
    self._dl_title.configure(text=f"Baixando {name}…")
    self._dl_detail.configure(text="Conectando ao Hugging Face…")
    threading.Thread(target=worker, daemon=True).start()


SettingsWindow._start_model_download = _start_model_download


# ---------------------------------------------------------------------------
# SUBPÁGINA: IDIOMA
# ---------------------------------------------------------------------------

def _page_sub_language(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    page, body = self._page_shell("Idioma",
                                  "Idioma principal da sua fala durante o ditado.",
                                  back_to="dictation")
    card = self._card(body)
    current = self._cfg.language or "auto"
    for code, name in LANGUAGES:
        self._radio_row(card, name, None,
                        selected=(current == code),
                        command=lambda c=code: self._select_language(c))
    return page


SettingsWindow._page_sub_language = _page_sub_language


def _select_language(self: SettingsWindow, code: str) -> None:
    value = "" if code == "auto" else code
    name = dict(LANGUAGES).get(code, code)
    self._set("language", value, toast=f"Idioma definido: {name}")
    self._rebuild_page("sub_language")


SettingsWindow._select_language = _select_language


# ---------------------------------------------------------------------------
# SUBPÁGINA: HARDWARE E PRECISÃO (opções dentro de opções)
# ---------------------------------------------------------------------------

def _page_sub_hardware(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    page, body = self._page_shell("Hardware e Precisão",
                                  "Onde a transcrição é processada e com qual quantização.",
                                  back_to="dictation")

    card = self._card(body, "Processador")
    for dev_id, name, desc in DEVICES:
        self._radio_row(card, name, desc,
                        selected=(self._cfg.device == dev_id),
                        command=lambda d=dev_id: self._select_device(d))

    card = self._card(body, "Precisão (Quantização)")
    for ct_id, name, desc in COMPUTE_TYPES:
        self._radio_row(card, name, desc,
                        selected=(self._cfg.compute_type == ct_id),
                        command=lambda c=ct_id: self._select_compute(c))

    t = self.theme
    note = tk.Label(
        body,
        text="Ao trocar o processador ou a precisão, o modelo é recarregado automaticamente no próximo ditado.",
        font=(self.font_name, 8, "italic"), fg=t.muted, bg=t.bg, anchor="w", wraplength=620,
        justify="left",
    )
    note.pack(fill="x", padx=4, pady=(8, 0))
    return page


SettingsWindow._page_sub_hardware = _page_sub_hardware


def _select_device(self: SettingsWindow, device: str) -> None:
    name = dict((k, n) for k, n, _d in DEVICES).get(device, device)
    self._set("device", device, toast=f"Processador definido: {name}")
    self._rebuild_page("sub_hardware")


def _select_compute(self: SettingsWindow, compute: str) -> None:
    name = dict((k, n) for k, n, _d in COMPUTE_TYPES).get(compute, compute)
    self._set("compute_type", compute, toast=f"Precisão definida: {name}")
    self._rebuild_page("sub_hardware")


SettingsWindow._select_device = _select_device
SettingsWindow._select_compute = _select_compute


# ---------------------------------------------------------------------------
# SUBPÁGINA: PROMPT AUXILIAR
# ---------------------------------------------------------------------------

def _page_sub_prompt(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell("Prompt Auxiliar",
                                  "Ensine vocabulário, marcas e termos que o modelo deve reconhecer.",
                                  back_to="dictation")

    card = self._card(body)
    box = tk.Frame(card, bg=t.card_bg)
    box.pack(fill="both", expand=True, padx=16, pady=14)

    prompt_text = self._styled_text(box, height=10)
    prompt_text.pack(fill="both", expand=True)
    prompt_text.insert("1.0", self._cfg.initial_prompt or "")
    prompt_text.focus_set()

    def apply_prompt(_event=None) -> None:
        value = prompt_text.get("1.0", "end-1c").strip()
        if value != (self._cfg.initial_prompt or ""):
            self._set("initial_prompt", value, toast="Prompt auxiliar atualizado")

    prompt_text.bind("<FocusOut>", apply_prompt)

    btn_row = tk.Frame(body, bg=t.bg)
    btn_row.pack(fill="x", pady=(10, 0))
    self._button(btn_row, "Aplicar Prompt", apply_prompt, "primary").pack(side="right")

    note = tk.Label(
        body,
        text="Dica: liste marcas, gírias e termos técnicos exatamente como devem aparecer no texto.",
        font=(self.font_name, 8, "italic"), fg=t.muted, bg=t.bg, anchor="w",
    )
    note.pack(fill="x", padx=4, pady=(8, 0))
    return page


SettingsWindow._page_sub_prompt = _page_sub_prompt


# ---------------------------------------------------------------------------
# SUBPÁGINA: HESITAÇÕES PERSONALIZADAS
# ---------------------------------------------------------------------------

def _page_sub_fillers(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell("Hesitações Personalizadas",
                                  "Termos removidos automaticamente do texto final.",
                                  back_to="dictation")

    card = self._card(body)
    row = self._row_base(card, "Termos a Remover",
                         "Separe por vírgulas. Ex.: tipo assim, né, então")
    entry = self._styled_entry(row, self._cfg.custom_fillers or "", width=26)
    entry.grid(row=0, column=1, sticky="e")

    def apply_fillers(_event=None) -> None:
        value = entry.get().strip()
        if value != (self._cfg.custom_fillers or ""):
            self._set("custom_fillers", value, toast="Hesitações personalizadas atualizadas")

    entry.bind("<FocusOut>", apply_fillers)
    entry.bind("<Return>", apply_fillers)

    note = tk.Label(
        body,
        text="Quando preenchida, esta lista substitui as hesitações padrão. "
             "A remoção só acontece com “Remover Hesitações” ativado.",
        font=(self.font_name, 8, "italic"), fg=t.muted, bg=t.bg, anchor="w",
        wraplength=620, justify="left",
    )
    note.pack(fill="x", padx=4, pady=(8, 0))
    return page


SettingsWindow._page_sub_fillers = _page_sub_fillers

# ---------------------------------------------------------------------------
# PÁGINA: INTELIGÊNCIA ARTIFICIAL
# ---------------------------------------------------------------------------

def _page_ai(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell(*self.SECTION_TITLES["ai"])

    card = self._card(body, "Reescrita Inteligente")

    if self.literal_mode_var.get():
        self._row_base(
            card,
            "Pós-Processamento Inteligente",
            "Inativo durante a Transcrição Literal para não alterar palavras reconhecidas.",
        )
        self._row_base(
            card,
            "Estilo da Transcrição",
            "Inativo durante a Transcrição Literal.",
        )
        card = self._card(body, "Aprendizado")
        self._row_base(
            card,
            "Aprendizado Contínuo",
            "Inativo durante a Transcrição Literal para preservar o texto reconhecido.",
        )
    else:
        self._row_toggle(
            card, "Pós-Processamento Inteligente",
            "Reescreve o texto com um modelo de linguagem local (Mini-LLM), "
            "aplicando o estilo escolhido sem enviar nada à nuvem.",
            self.rewriter_var, "use_llm_rewriter",
            on_change=lambda _v: self._rebuild_page("ai"),
        )

        # Status e download do Mini-LLM com percentual real
        if self.rewriter_var.get():
            from .rewriter import is_rewriter_downloaded
            repo_id = self._cfg.llm_model_repo
            downloaded = is_rewriter_downloaded(repo_id)

            if downloaded:
                row = self._row_base(card, "Modelo de Reescrita",
                                     "Mini-LLM instalado e pronto para uso offline.")
                tk.Label(row, text="✓ Instalado", font=(self.font_name, 9, "bold"),
                         fg=t.success, bg=t.card_bg).grid(row=0, column=1, sticky="e")
            elif self._llm_dl_active:
                row = self._row_base(card, "Baixando Mini-LLM…", None)
                dl_box = tk.Frame(row, bg=t.card_bg)
                dl_box.grid(row=0, column=1, sticky="e")
                self._llm_pct_var = getattr(self, "_llm_pct_var", tk.DoubleVar(value=0.0))
                bar = ttk.Progressbar(dl_box, orient="horizontal", mode="determinate",
                                      variable=self._llm_pct_var, maximum=100.0, length=180,
                                      style="Accent.Horizontal.TProgressbar")
                bar.pack(side="left")
                self._llm_pct_label = tk.Label(dl_box, text="0%", width=5, anchor="e",
                                               font=(self.font_name, 9, "bold"),
                                               fg=t.accent, bg=t.card_bg)
                self._llm_pct_label.pack(side="left", padx=(8, 0))
            else:
                self._row_action(card, "Modelo de Reescrita",
                                 "Necessário baixar o pacote de IA (~400 MB) uma única vez.",
                                 "Baixar Mini-LLM", lambda: self._start_llm_download(), "primary")

        self._row_nav(card, "Estilo da Transcrição",
                      "Tom de voz aplicado na reescrita do texto.",
                      lambda: self._tone_display_name(self._cfg.tone_style), "sub_tone")

        card = self._card(body, "Aprendizado")

        self._row_toggle(
            card, "Aprendizado Contínuo",
            "Aprende com as suas notas do diário e prioriza o vocabulário que você mais usa.",
            self.learning_var, "continuous_learning")

    note = tk.Label(
        body,
        text="Todo o processamento é 100% local: nenhum áudio ou texto sai do seu computador.",
        font=(self.font_name, 8, "italic"), fg=t.muted, bg=t.bg, anchor="w",
    )
    note.pack(fill="x", padx=4, pady=(10, 0))
    return page


SettingsWindow._page_ai = _page_ai


def _tone_display_name(self: SettingsWindow, tone_id: str) -> str:
    builtin = {k: n for k, n, _d in TONES}
    return builtin.get(tone_id, tone_id.capitalize())


SettingsWindow._tone_display_name = _tone_display_name


def _start_llm_download(self: SettingsWindow) -> None:
    if self._llm_dl_active:
        return
    self._llm_dl_active = True
    self._llm_pct_var = tk.DoubleVar(value=0.0)

    def on_progress(percent: float, downloaded: int, total: int) -> None:
        def update() -> None:
            if not self.winfo_exists():
                return
            try:
                self._llm_pct_var.set(percent)
                if hasattr(self, "_llm_pct_label") and self._llm_pct_label.winfo_exists():
                    self._llm_pct_label.configure(text=f"{percent:.0f}%")
            except Exception:
                pass
        try:
            self.after(0, update)
        except Exception:
            pass

    def worker() -> None:
        from .rewriter import _get_model_path
        repo_id = self._cfg.llm_model_repo
        error: Exception | None = None
        try:
            revision = _PINNED_REVISIONS.get(repo_id)
            if revision is None:
                raise ValueError("Repositório de Mini-LLM não aprovado nesta versão do Quantum Scribe")
            download_snapshot_with_progress(
                repo_id,
                _get_model_path(repo_id),
                on_progress,
                revision=revision,
            )
        except Exception as exc:  # noqa: BLE001
            error = exc

        def finish() -> None:
            self._llm_dl_active = False
            if error is None:
                self._toast("Mini-LLM instalado com sucesso")
            else:
                self._toast(f"Falha ao baixar o Mini-LLM: {error}", kind="error")
            if self.winfo_exists():
                self._rebuild_page("ai")

        try:
            self.after(0, finish)
        except Exception:
            pass

    self._rebuild_page("ai")
    threading.Thread(target=worker, daemon=True).start()


SettingsWindow._start_llm_download = _start_llm_download


# ---------------------------------------------------------------------------
# SUBPÁGINA: ESTILO DA TRANSCRIÇÃO (tons)
# ---------------------------------------------------------------------------

def _page_sub_tone(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    page, body = self._page_shell("Estilo da Transcrição",
                                  "Escolha o tom aplicado pelo pós-processamento inteligente.",
                                  back_to="ai")
    card = self._card(body)

    custom = self._cfg.custom_tones or {}
    for tone_id, name, desc in TONES:
        self._radio_row(card, name, desc,
                        selected=(self._cfg.tone_style == tone_id),
                        command=lambda tid=tone_id: self._select_tone(tid))

    for tone_id in custom:
        self._radio_row(card, tone_id.capitalize(), "Estilo personalizado criado por você.",
                        selected=(self._cfg.tone_style == tone_id),
                        command=lambda tid=tone_id: self._select_tone(tid))

    self._row_action(card, "Editor de Estilos",
                     "Crie novos tons ou ajuste as instruções dos existentes.",
                     "Abrir Editor", lambda: self._show("sub_tone_editor", update_sidebar=True),
                     "secondary")
    return page


SettingsWindow._page_sub_tone = _page_sub_tone


def _select_tone(self: SettingsWindow, tone_id: str) -> None:
    self._set("tone_style", tone_id,
              toast=f"Estilo definido: {self._tone_display_name(tone_id)}")
    self._rebuild_page("sub_tone")


SettingsWindow._select_tone = _select_tone


def _page_sub_tone_editor(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell("Editor de Estilos",
                                  "Ajuste as instruções enviadas ao Whisper e ao Mini-LLM.",
                                  back_to="sub_tone")

    custom = self._cfg.custom_tones or {}
    all_tones = [k for k, _n, _d in TONES] + list(custom.keys())
    selected = tk.StringVar(value=self._cfg.tone_style if self._cfg.tone_style in all_tones else all_tones[0])

    # Seletor do estilo
    card = self._card(body)
    row = self._row_base(card, "Estilo Selecionado", None)
    selector = ThemedDropdown(row, t, self.font_name, selected, all_tones,
                              command=lambda *_: load_style())
    selector.grid(row=0, column=1, sticky="e")

    # Prompt do Whisper
    tk.Label(body, text="PROMPT DO WHISPER (VOCABULÁRIO / REGRAS)",
             font=(self.font_name, 8, "bold"), fg=t.muted, bg=t.bg, anchor="w").pack(
        fill="x", padx=4, pady=(14, 6))
    whisper_text = self._styled_text(body, height=4)
    whisper_text.pack(fill="x")

    # Instrução do Mini-LLM
    tk.Label(body, text="INSTRUÇÃO DO MINI-LLM (COMPORTAMENTO DE REESCRITA)",
             font=(self.font_name, 8, "bold"), fg=t.muted, bg=t.bg, anchor="w").pack(
        fill="x", padx=4, pady=(14, 6))
    llm_text = self._styled_text(body, height=5)
    llm_text.pack(fill="x")

    def load_style() -> None:
        sel = selected.get()
        whisper_text.delete("1.0", "end")
        llm_text.delete("1.0", "end")
        whisper_text.insert("1.0", custom.get(sel, DEFAULT_WHISPER_PROMPTS.get(sel, "")))
        llm_text.insert("1.0", self._cfg.llm_custom_tones.get(
            sel, DEFAULT_LLM_PROMPTS.get(sel, "Reescreva o texto com clareza.")))

    def create_style() -> None:
        from tkinter import simpledialog
        name = simpledialog.askstring("Novo Estilo", "Nome do novo estilo:", parent=self)
        if not name or not name.strip():
            return
        name = name.strip().lower()
        if name not in all_tones:
            all_tones.append(name)
            selector.configure_values(all_tones)
        selected.set(name)
        load_style()

    def save_style() -> None:
        sel = selected.get()
        self._cfg.custom_tones[sel] = whisper_text.get("1.0", "end-1c").strip()
        self._cfg.llm_custom_tones[sel] = llm_text.get("1.0", "end-1c").strip()
        self._set("custom_tones", self._cfg.custom_tones)
        self._set("llm_custom_tones", self._cfg.llm_custom_tones,
                  toast=f"Estilo “{sel}” salvo")
        if self._cfg.tone_style not in all_tones:
            self._cfg.tone_style = sel
        self._rebuild_page("sub_tone_editor")

    btn_row = tk.Frame(body, bg=t.bg)
    btn_row.pack(fill="x", pady=(14, 0))
    self._button(btn_row, "Novo Estilo", create_style, "secondary").pack(side="left")
    self._button(btn_row, "Salvar Estilo", save_style, "primary").pack(side="right")

    load_style()
    return page


SettingsWindow._page_sub_tone_editor = _page_sub_tone_editor


class ThemedDropdown(tk.Frame):
    """Dropdown temático simples baseado em Menu, no padrão visual do app."""

    def __init__(self, parent: tk.Widget, theme: Theme, font_name: str,
                 variable: tk.StringVar, values: list[str],
                 command: Callable[[], None] | None = None, width: int = 22) -> None:
        super().__init__(parent, bg=theme.input_bg, highlightthickness=1,
                         highlightbackground=theme.border)
        self.theme = theme
        self.variable = variable
        self.values = list(values)
        self.command = command

        self.btn = tk.Label(self, textvariable=self.variable, bg=theme.input_bg,
                            fg=theme.text, font=(font_name, 10), anchor="w",
                            padx=10, pady=6, width=width, cursor="hand2")
        self.btn.pack(side="left", fill="both", expand=True)
        arrow = tk.Label(self, text="▾", bg=theme.input_bg, fg=theme.muted,
                         font=(font_name, 10))
        arrow.pack(side="right", padx=(0, 8))
        for w in (self.btn, arrow):
            w.bind("<Button-1>", lambda _e: self._show_menu())

        self.menu = tk.Menu(self, tearoff=0, bg=theme.card_bg, fg=theme.text,
                            activebackground=theme.accent,
                            activeforeground=theme.on_accent,
                            font=(font_name, 10), bd=0)
        self._rebuild_menu()

    def _rebuild_menu(self) -> None:
        self.menu.delete(0, "end")
        for value in self.values:
            self.menu.add_command(label=value, command=lambda v=value: self._select(v))

    def _select(self, value: str) -> None:
        self.variable.set(value)
        if self.command:
            self.command()

    def _show_menu(self) -> None:
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        try:
            self.menu.tk_popup(x, y)
        finally:
            self.menu.grab_release()

    def configure_values(self, values: list[str]) -> None:
        self.values = list(values)
        self._rebuild_menu()


# ---------------------------------------------------------------------------
# PÁGINA: MICROFONE E ÁUDIO
# ---------------------------------------------------------------------------

def _page_audio(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell(*self.SECTION_TITLES["audio"])

    card = self._card(body, "Entrada de Áudio")

    self._row_nav(card, "Microfone",
                  "Dispositivo usado para capturar a sua voz.",
                  lambda: self._cfg.audio_device or "Padrão do Sistema", "sub_mic")

    if self.streaming_var.get():
        self._row_toggle(card, "Aprimorar Áudio",
                         "Filtro de graves, redução de ruído e normalização de volume "
                         "antes da transcrição contínua.",
                         self.audio_enhance_var, "audio_enhance",
                         on_change=lambda _v: self._rebuild_page("audio"))

        if self.audio_enhance_var.get():
            self._row_nav(card, "Perfil de Aprimoramento",
                          "Intensidade do processamento de áudio.",
                          lambda: dict((k, n) for k, n, _d in ENHANCE_PROFILES).get(
                              self._cfg.audio_enhance_profile, "Equilibrado"),
                          "sub_profile")
        else:
            self._row_base(
                card,
                "Perfil de Aprimoramento",
                "Inativo — ative Aprimorar Áudio para escolher um perfil.",
            )
    else:
        self._row_base(card, "Aprimoramento de Áudio",
                       "Inativo — requer Modo Streaming Contínuo. O modo clássico "
                       "mantém seu próprio filtro de fala do faster-whisper.")

    # Status dos filtros
    nr_ok = (importlib.util.find_spec("noisereduce") is not None
             and importlib.util.find_spec("scipy") is not None)
    status_text = ("✓ Filtros inteligentes de ruído disponíveis" if nr_ok
                   else "⚠ noisereduce não instalado — apenas normalização de volume")
    status_color = t.success if nr_ok else t.warning
    row = self._row_base(card, "Filtros de Ruído", None)
    tk.Label(row, text=status_text, font=(self.font_name, 8, "bold"),
             fg=status_color, bg=t.card_bg).grid(row=0, column=1, sticky="e")

    card = self._card(body, "Streaming em Tempo Real")

    self._row_toggle(card, "Modo Streaming Contínuo",
                     "Transcreve em blocos enquanto você fala, mostrando o texto em tempo real.",
                     self.streaming_var, "streaming_mode",
                     on_change=lambda _v: self._rebuild_page("audio"))

    if self.streaming_var.get():
        self._row_nav(card, "Silêncio para Corte",
                      "Pausa necessária para separar os blocos de fala.",
                      lambda: f"{self._cfg.stream_min_silence_ms} ms", "sub_silence")

        from .stream_transcriber import is_silero_available

        silero_ok = is_silero_available()
        vad_text = ("✓ Silero VAD neural (alta qualidade)" if silero_ok else
                    "⚠ Silero será instalado ao ativar o modo contínuo")
        vad_color = t.success if silero_ok else t.warning
        row = self._row_base(card, "Detecção de Fala (VAD)",
                             "Motor usado pelo streaming para identificar fala.")
        tk.Label(row, text=vad_text, font=(self.font_name, 8, "bold"),
                 fg=vad_color, bg=t.card_bg).grid(row=0, column=1, sticky="e")
    else:
        self._row_base(card, "Silêncio para Corte e Silero VAD",
                       "Inativos — requerem Modo Streaming Contínuo e não são "
                       "carregados enquanto ele estiver desligado.")

    self._row_base(card, "Filtro de fala do modo clássico",
                   "Ativo somente no ditado clássico pelo faster-whisper; é um "
                   "mecanismo separado do Silero VAD do streaming.")

    card = self._card(body, "Efeitos Sonoros")

    self._row_toggle(card, "Efeitos Sonoros",
                     "Toca sons suaves ao iniciar, concluir e cancelar o ditado.",
                     self.sounds_var, "play_sounds",
                     on_change=lambda _v: self._rebuild_page("audio"))

    if self.sounds_var.get():
        row = self._row_base(card, "Volume dos Efeitos", None)
        vol_box = tk.Frame(row, bg=t.card_bg)
        vol_box.grid(row=0, column=1, sticky="e")

        self._vol_pct = tk.Label(vol_box, text=f"{int(self._cfg.sound_volume * 100)}%",
                                 font=(self.font_name, 9, "bold"), fg=t.muted,
                                 bg=t.card_bg, width=4, anchor="e")
        self._vol_pct.pack(side="right", padx=(8, 0))

        slider = tk.Scale(
            vol_box, from_=0.0, to=1.0, resolution=0.05, orient="horizontal",
            variable=self.sound_volume_var, showvalue=False, length=160,
            bg=t.card_bg, fg=t.text, troughcolor=t.track,
            activebackground=t.accent, highlightthickness=0, bd=0,
            command=self._on_volume_change,
        )
        slider.pack(side="right")

    return page


SettingsWindow._page_audio = _page_audio


def _on_volume_change(self: SettingsWindow, _raw=None) -> None:
    # Grava o volume diretamente do DoubleVar (não depende de widget preguiçoso)
    self._cfg.sound_volume=float(self.sound_volume_var.get())
    try:
        self.on_save_callback(self._cfg)
        self._vol_pct.configure(text=f"{int(self._cfg.sound_volume * 100)}%")
    except Exception:
        pass


SettingsWindow._on_volume_change = _on_volume_change


# ---------------------------------------------------------------------------
# SUBPÁGINA: MICROFONE (seleção + teste em tempo real)
# ---------------------------------------------------------------------------

def _page_sub_mic(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell("Microfone",
                                  "Escolha o dispositivo de entrada e teste o nível do sinal.",
                                  back_to="audio")

    devices = getattr(self, "_mic_devices", None)
    if devices is None:
        devices = ["Padrão do Sistema"]
        current = self._cfg.audio_device
        if current and current not in devices:
            devices.append(current)
        self._mic_devices = devices
        threading.Thread(target=self._load_mic_devices, daemon=True).start()

    card = self._card(body, "Dispositivo de Entrada")
    for name in devices:
        current = self._cfg.audio_device or "Padrão do Sistema"
        self._radio_row(card, name, None,
                        selected=(current == name),
                        command=lambda n=name: self._select_mic(n))

    card = self._card(body, "Teste do Microfone")
    row = self._row_base(card, "Nível do Sinal",
                         "Fale próximo ao microfone e observe o medidor.")
    test_box = tk.Frame(row, bg=t.card_bg)
    test_box.grid(row=0, column=1, sticky="e")

    self.meter_canvas = tk.Canvas(test_box, width=170, height=20, bg=t.input_bg,
                                  highlightthickness=1, highlightbackground=t.border)
    self.meter_canvas.pack(side="left", padx=(0, 10))
    self.meter_bar = self.meter_canvas.create_rectangle(1, 1, 1, 19, fill=t.accent, outline="")

    self.test_btn = self._button(test_box, "Iniciar Teste", self._toggle_test_stream, "secondary")
    self.test_btn.pack(side="left")
    return page


SettingsWindow._page_sub_mic = _page_sub_mic


def _load_mic_devices(self: SettingsWindow) -> None:
    try:
        import sounddevice as sd
        found = ["Padrão do Sistema"]
        for d in sd.query_devices():
            if d.get("max_input_channels", 0) > 0 and d["name"] not in found:
                found.append(d["name"])
        current = self._cfg.audio_device
        if current and current not in found:
            found.append(current)
        self._mic_devices = found
        if self.winfo_exists():
            self.after(0, lambda: self._rebuild_page("sub_mic")
                       if self._current_page == "sub_mic" else None)
    except Exception:
        pass


SettingsWindow._load_mic_devices = _load_mic_devices


def _select_mic(self: SettingsWindow, name: str) -> None:
    value = "" if name == "Padrão do Sistema" else name
    self._set("audio_device", value, toast=f"Microfone definido: {name}")
    if self._test_stream_active:
        self._start_test_stream()
    self._rebuild_page("sub_mic")


SettingsWindow._select_mic = _select_mic


def _toggle_test_stream(self: SettingsWindow) -> None:
    if self._test_stream_active:
        self._stop_test_stream()
        try:
            self.test_btn.configure(text="Iniciar Teste")
            self.meter_canvas.coords(self.meter_bar, 1, 1, 1, 19)
        except Exception:
            pass
    else:
        self._start_test_stream()
        if self._test_stream:
            self.test_btn.configure(text="Parar Teste")
            self._update_test_meter()


SettingsWindow._toggle_test_stream = _toggle_test_stream


def _start_test_stream(self: SettingsWindow) -> None:
    self._stop_test_stream()
    from .audio import get_device_index_by_name
    device_index = get_device_index_by_name(self._cfg.audio_device or "Padrão do Sistema")

    import numpy as np
    import sounddevice as sd

    self._test_amplitude = 0.0
    self._test_stream_active = True

    def callback(indata, frames, time_info, status):
        if not self._test_stream_active or status.input_overflow or len(indata) == 0:
            return
        rms = np.sqrt(np.mean(indata.astype(np.float32) ** 2))
        self._test_amplitude = float(rms / 32768.0)

    try:
        self._test_stream = sd.InputStream(device=device_index, samplerate=16000,
                                           channels=1, dtype="int16", callback=callback)
        self._test_stream.start()
    except Exception as error:
        self._toast(f"Erro no microfone: {error}", kind="error")
        self._test_stream = None
        self._test_stream_active = False


SettingsWindow._start_test_stream = _start_test_stream


def _stop_test_stream(self: SettingsWindow) -> None:
    self._test_stream_active = False
    stream = getattr(self, "_test_stream", None)
    if stream:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass
        self._test_stream = None


SettingsWindow._stop_test_stream = _stop_test_stream


def _update_test_meter(self: SettingsWindow) -> None:
    if not self._test_stream_active:
        return
    amp_clean = max(0.0, self._test_amplitude - 0.0015)
    target_amp = min(1.0, amp_clean * 300.0)
    self._smooth_level = self._smooth_level * 0.7 + target_amp * 0.3
    try:
        max_w = self.meter_canvas.winfo_width() - 2
        w = int(self._smooth_level * max_w)
        self.meter_canvas.coords(self.meter_bar, 1, 1, 1 + w, 19)
    except Exception:
        pass
    self.after(40, self._update_test_meter)


SettingsWindow._update_test_meter = _update_test_meter


# ---------------------------------------------------------------------------
# SUBPÁGINAS: PERFIL DE APRIMORAMENTO / SILÊNCIO
# ---------------------------------------------------------------------------

def _page_sub_profile(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    page, body = self._page_shell("Perfil de Aprimoramento",
                                  "Quanto processamento é aplicado ao áudio antes de transcrever.",
                                  back_to="audio")
    card = self._card(body)
    for profile_id, name, desc in ENHANCE_PROFILES:
        self._radio_row(card, name, desc,
                        selected=(self._cfg.audio_enhance_profile == profile_id),
                        command=lambda p=profile_id: self._select_profile(p))
    return page


SettingsWindow._page_sub_profile = _page_sub_profile


def _select_profile(self: SettingsWindow, profile_id: str) -> None:
    name = dict((k, n) for k, n, _d in ENHANCE_PROFILES).get(profile_id, profile_id)
    self._set("audio_enhance_profile", profile_id, toast=f"Perfil definido: {name}")
    self._rebuild_page("sub_profile")


SettingsWindow._select_profile = _select_profile


def _page_sub_silence(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    page, body = self._page_shell("Silêncio para Corte",
                                  "Tempo de pausa que separa os blocos de ditado no streaming.",
                                  back_to="audio")
    card = self._card(body)
    for ms, label in SILENCE_OPTIONS:
        self._radio_row(card, label, None,
                        selected=(self._cfg.stream_min_silence_ms == ms),
                        command=lambda v=ms: self._select_silence(v))
    return page


SettingsWindow._page_sub_silence = _page_sub_silence


def _select_silence(self: SettingsWindow, ms: int) -> None:
    self._set("stream_min_silence_ms", ms, toast=f"Silêncio para corte: {ms} ms")
    self._rebuild_page("sub_silence")


SettingsWindow._select_silence = _select_silence


# ---------------------------------------------------------------------------
# PÁGINA: ATALHOS
# ---------------------------------------------------------------------------

def _page_shortcuts(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell(*self.SECTION_TITLES["shortcuts"])

    card = self._card(body, "Atalhos Globais")

    self._hotkey_row(card, "Ditado Normal",
                     "Inicia e para a gravação, colando o texto no cursor.",
                     "hotkey", required=True)
    self._hotkey_row(card, "Ditado + Traduzir",
                     "Dita em qualquer idioma e cola o texto traduzido para o inglês.",
                     "hotkey_translate")
    self._hotkey_row(card, "Ditado + Enviar",
                     "Cola o texto e pressiona Enter automaticamente.",
                     "hotkey_auto_send")
    self._hotkey_row(card, "Ditado + Quantum Brain",
                     "Envia o ditado direto para as suas notas do Quantum Brain.",
                     "hotkey_quantum_brain")

    note = tk.Label(
        body,
        text="Use o formato Ctrl+Shift+Tecla. Deixe em branco para desativar um atalho opcional. "
             "A tecla Esc sempre cancela a gravação em andamento.",
        font=(self.font_name, 8, "italic"), fg=t.muted, bg=t.bg, anchor="w",
        wraplength=620, justify="left",
    )
    note.pack(fill="x", padx=4, pady=(10, 0))
    return page


SettingsWindow._page_shortcuts = _page_shortcuts


def _hotkey_row(self: SettingsWindow, card: tk.Frame, label: str, desc: str,
                field: str, required: bool = False) -> None:
    row = self._row_base(card, label, desc)
    entry = self._styled_entry(row, getattr(self._cfg, field, "") or "", width=22)
    entry.grid(row=0, column=1, sticky="e")

    def apply(_event=None) -> None:
        value = entry.get().strip()
        if value == (getattr(self._cfg, field, "") or ""):
            return
        if not value:
            if required:
                entry.delete(0, "end")
                entry.insert(0, getattr(self._cfg, field, ""))
                self._toast("O atalho principal não pode ficar vazio", kind="error")
                return
            self._set(field, "", toast=f"Atalho “{label}” desativado", toast_kind="info")
            return
        try:
            _parse_hotkey(value)
        except ValueError as exc:
            entry.delete(0, "end")
            entry.insert(0, getattr(self._cfg, field, "") or "")
            self._toast(f"Atalho inválido: {exc}", kind="error")
            return
        conflict = hotkey_conflict(self._cfg, field, value)
        if conflict is not None:
            entry.delete(0, "end")
            entry.insert(0, getattr(self._cfg, field, "") or "")
            self._toast(f"Atalho já usado por “{conflict}”", kind="error")
            return
        self._set(field, value, toast=f"Atalho “{label}” atualizado")

    entry.bind("<FocusOut>", apply)
    entry.bind("<Return>", apply)


SettingsWindow._hotkey_row = _hotkey_row

# ---------------------------------------------------------------------------
# PÁGINA: QUANTUM BRAIN
# ---------------------------------------------------------------------------

def _page_brain(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell(*self.SECTION_TITLES["brain"])

    card = self._card(body, "Segundo Cérebro")

    self._row_toggle(card, "Ativar Quantum Brain",
                     "Captura pensamentos ditados como notas e os compila em projetos e insights.",
                     self.quantum_brain_enabled_var, "quantum_brain_enabled",
                     on_change=lambda _v: self._rebuild_page("brain"))

    if self.quantum_brain_enabled_var.get():
        self._row_toggle(card, "Também Colar no Cursor",
                         "Além de salvar a nota, insere o texto no cursor como no ditado normal.",
                         self.quantum_brain_also_paste_var, "quantum_brain_also_paste")

        interval_var = tk.StringVar(value=f"{self._cfg.quantum_brain_sync_interval_min} min")
        row = self._row_base(card, "Intervalo de Síntese",
                             "Tempo máximo entre compilações automáticas das notas.")
        interval_dd = ThemedDropdown(
            row, t, self.font_name, interval_var,
            [f"{v} min" for v in (15, 30, 45, 60, 120)],
            command=lambda: self._set(
                "quantum_brain_sync_interval_min",
                int(interval_var.get().replace(" min", "")),
                toast="Intervalo de síntese atualizado"),
            width=10)
        interval_dd.grid(row=0, column=1, sticky="e")

        threshold_var = tk.StringVar(value=f"{self._cfg.quantum_brain_sync_threshold} notas")
        row = self._row_base(card, "Notas para Síntese Imediata",
                             "Quantidade de notas pendentes que dispara uma síntese na hora.")
        threshold_dd = ThemedDropdown(
            row, t, self.font_name, threshold_var,
            [f"{v} notas" for v in (3, 5, 10, 15, 25)],
            command=lambda: self._set(
                "quantum_brain_sync_threshold",
                int(threshold_var.get().replace(" notas", "")),
                toast="Limite de notas atualizado"),
            width=10)
        threshold_dd.grid(row=0, column=1, sticky="e")

        card = self._card(body, "Atividade")
        stats_frame = tk.Frame(card, bg=t.card_bg)
        stats_frame.pack(fill="x", padx=16, pady=12)
        self.stats_label = tk.Label(
            stats_frame, text="Carregando estatísticas…",
            font=(self.font_name, 9), fg=t.text, bg=t.card_bg,
            justify="left", anchor="w",
        )
        self.stats_label.pack(anchor="w", fill="x")
        self._update_quantum_brain_stats()

        self._row_action(card, "Pasta de Notas",
                         "Abra o diretório onde as notas e sínteses são gravadas.",
                         "Abrir Pasta", self._open_quantum_brain_folder, "secondary")

        self._row_action(card, "Síntese Manual",
                         "Compila imediatamente todas as notas pendentes.",
                         "Sintetizar Agora", self._trigger_manual_synthesis, "primary")

    return page


SettingsWindow._page_brain = _page_brain


def _open_quantum_brain_folder(self: SettingsWindow) -> None:
    try:
        from .quantum_brain import quantum_brain_dir
        os.startfile(str(quantum_brain_dir(self._cfg)))
    except Exception as error:
        self._toast(f"Não foi possível abrir a pasta: {error}", kind="error")


SettingsWindow._open_quantum_brain_folder = _open_quantum_brain_folder


def _trigger_manual_synthesis(self: SettingsWindow) -> None:
    try:
        from .quantum_brain import QuantumBrainOrchestrator
        orchestrator = QuantumBrainOrchestrator.get_instance(self._cfg)

        def run_sync() -> None:
            try:
                orchestrator._trigger_synthesis()
                self.after(0, lambda: self._toast("Síntese concluída"))
            except Exception as error:
                message = str(error)
                self.after(0, lambda m=message: self._toast(f"Falha na síntese: {m}", kind="error"))
            finally:
                self.after(1500, lambda: self._update_quantum_brain_stats()
                           if self.winfo_exists() else None)

        self._toast("Sintetizando notas em segundo plano…", kind="info")
        threading.Thread(target=run_sync, daemon=True).start()
    except Exception as error:
        self._toast(f"Erro: {error}", kind="error")


SettingsWindow._trigger_manual_synthesis = _trigger_manual_synthesis


def _update_quantum_brain_stats(self: SettingsWindow) -> None:
    if not hasattr(self, "stats_label") or self.stats_label is None:
        return
    try:
        if not self.stats_label.winfo_exists():
            return
    except Exception:
        return
    try:
        from .quantum_brain import QuantumBrainOrchestrator
        orchestrator = QuantumBrainOrchestrator.get_instance(self._cfg)
        stats = orchestrator.get_stats()

        last = "Nunca"
        if stats["last_synthesis"]:
            import datetime
            last = datetime.datetime.fromtimestamp(stats["last_synthesis"]).strftime("%d/%m/%Y %H:%M")

        self.stats_label.configure(
            text=f"•  Notas aguardando síntese: {stats['unsynthesized']}\n"
                 f"•  Projetos ativos mapeados: {stats['projects']}\n"
                 f"•  Última síntese: {last}")
    except Exception as error:
        try:
            self.stats_label.configure(text=f"Estatísticas indisponíveis: {error}")
        except Exception:
            pass


SettingsWindow._update_quantum_brain_stats = _update_quantum_brain_stats


# ---------------------------------------------------------------------------
# PÁGINA: ARMAZENAMENTO
# ---------------------------------------------------------------------------

def _page_storage(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell(*self.SECTION_TITLES["storage"])

    # --- Histórico de transcrições ---
    card = self._card(body, "Histórico de Transcrições")

    search_row = tk.Frame(card, bg=t.card_bg)
    search_row.pack(fill="x", padx=16, pady=(14, 0))
    search_row.columnconfigure(0, weight=1)
    self._history_search_var = tk.StringVar()
    search_box = tk.Entry(
        search_row, textvariable=self._history_search_var, bg=t.input_bg,
        fg=t.text, insertbackground=t.text, relief="flat", bd=0,
        highlightthickness=1, highlightbackground=t.border,
        highlightcolor=t.accent, font=(self.font_name, 9),
    )
    search_box.grid(row=0, column=0, sticky="ew", ipady=6)
    search_box.bind("<Return>", lambda _event: self._run_history_search())
    self._button(search_row, "Buscar", self._run_history_search, "secondary").grid(
        row=0, column=1, padx=(8, 0), sticky="e"
    )

    log_view = tk.Frame(card, bg=t.input_bg, highlightthickness=1,
                        highlightbackground=t.border)
    log_view.pack(fill="x", padx=16, pady=(14, 6))

    self.logs_text = tk.Text(log_view, height=6, bg=t.input_bg, fg=t.text,
                             font=(self.font_name, 9), relief="flat", bd=0,
                             state="disabled")
    logs_scroll = ttk.Scrollbar(log_view, command=self.logs_text.yview,
                                style="Vertical.TScrollbar")
    self.logs_text.configure(yscrollcommand=logs_scroll.set)
    self.logs_text.tag_config("link", foreground=t.accent, underline=True)
    self.logs_text.tag_bind("link", "<Enter>",
                            lambda _e: self.logs_text.config(cursor="hand2"))
    self.logs_text.tag_bind("link", "<Leave>",
                            lambda _e: self.logs_text.config(cursor=""))
    self.logs_text.tag_bind("link", "<Button-1>", self._on_transcription_clicked)
    self.logs_text.pack(side="left", fill="both", expand=True, padx=8, pady=6)
    logs_scroll.pack(side="right", fill="y")

    self._row_action(card, "Pasta do Histórico",
                     f"Gravado em {diary_dir()}",
                     "Abrir Pasta", lambda: os.startfile(diary_dir()), "secondary")

    self._row_action(card, "Apagar Histórico",
                     "Remove permanentemente todas as transcrições salvas.",
                     "Apagar Tudo", self._delete_all_transcriptions, "danger")

    self._refresh_transcriptions_list()
    return page


SettingsWindow._page_storage = _page_storage


# ---------------------------------------------------------------------------
# PÁGINA: SISTEMA
# ---------------------------------------------------------------------------

def _page_system(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    """Preferências do ciclo de vida do aplicativo e integração com o SO."""
    page, body = self._page_shell(*self.SECTION_TITLES["system"])

    card = self._card(body, "Inicialização")
    if supports_startup():
        self._row_toggle(
            card,
            "Iniciar com o Windows",
            "Abre o Quantum Scribe automaticamente quando você entrar na sua conta. "
            "Não exige permissão de administrador.",
            self.start_with_windows_var,
            "start_with_windows",
            toast="Inicialização com o Windows atualizada",
        )
        self._row_base(
            card,
            "Escopo da inicialização",
            "A opção vale somente para este usuário do Windows e pode ser desligada a qualquer momento.",
        )
    else:
        self._row_base(
            card,
            "Iniciar com o Windows",
            "Disponível somente quando o aplicativo está sendo executado no Windows.",
        )

    card = self._card(body, "Aplicação das configurações")
    self._row_base(
        card,
        "Alterações instantâneas",
        "Os controles são aplicados assim que você os altera. Se o sistema rejeitar uma mudança, "
        "o botão volta automaticamente ao estado anterior.",
    )
    return page


SettingsWindow._page_system = _page_system


def _refresh_transcriptions_list(self: SettingsWindow, query: str = "") -> None:
    if not hasattr(self, "logs_text") or self.logs_text is None:
        return
    try:
        if not self.logs_text.winfo_exists():
            return
    except Exception:
        return
    self.logs_text.configure(state="normal")
    self.logs_text.delete("1.0", "end")
    self._listed_files = []

    query = query.strip()
    if query:
        results = search_entries(query)
        if not results:
            self.logs_text.insert("end", f"Nenhuma transcrição encontrada para “{query}”.\n")
        else:
            for result in results:
                self._listed_files.append(str(result.path))
                self.logs_text.insert(
                    "end",
                    f"🔎 {result.date:%d/%m/%Y} {result.time}  {result.preview}\n",
                    "link",
                )
        self.logs_text.configure(state="disabled")
        return

    files = glob.glob(os.path.join(diary_dir(), "*.md"))
    files.sort(reverse=True)

    if not files:
        self.logs_text.insert("end", "Nenhuma transcrição salva ainda.\n")
    else:
        for f in files:
            basename = os.path.basename(f)
            try:
                with open(f, "r", encoding="utf-8") as f_obj:
                    entries = sum(1 for line in f_obj if line.startswith("## "))
            except Exception:
                entries = 0
            self._listed_files.append(f)
            self.logs_text.insert("end", f"📄 {basename:<25} {entries} entrada(s)\n", "link")

    self.logs_text.configure(state="disabled")


SettingsWindow._refresh_transcriptions_list = _refresh_transcriptions_list


def _run_history_search(self: SettingsWindow) -> None:
    query = getattr(self, "_history_search_var", tk.StringVar()).get()
    self._refresh_transcriptions_list(query)


SettingsWindow._run_history_search = _run_history_search


def _on_transcription_clicked(self: SettingsWindow, event) -> None:
    index_str = self.logs_text.index(f"@{event.x},{event.y}")
    line_num = int(index_str.split(".")[0]) - 1
    if 0 <= line_num < len(self._listed_files):
        file_path = self._listed_files[line_num]
        if os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as error:
                self._toast(f"Não foi possível abrir: {error}", kind="error")


SettingsWindow._on_transcription_clicked = _on_transcription_clicked


def _delete_all_transcriptions(self: SettingsWindow) -> None:
    if messagebox.askyesno(
            "Apagar Histórico",
            "Tem certeza que deseja apagar permanentemente todas as transcrições salvas?",
            parent=self):
        files = glob.glob(os.path.join(diary_dir(), "*.md"))
        for f in files:
            try:
                os.remove(f)
            except Exception:
                pass
        self._refresh_transcriptions_list()
        self._toast("Histórico apagado com sucesso")


SettingsWindow._delete_all_transcriptions = _delete_all_transcriptions


# ---------------------------------------------------------------------------
# PÁGINA: SOBRE
# ---------------------------------------------------------------------------

def _page_about(self: SettingsWindow, parent: tk.Widget) -> tk.Frame:
    t = self.theme
    page, body = self._page_shell(*self.SECTION_TITLES["about"])

    card = self._card(body)
    row_id = tk.Frame(card, bg=t.card_bg)
    row_id.pack(fill="x", padx=18, pady=18)

    if self._icon_img is not None:
        try:
            self._logo_photo = ImageTk.PhotoImage(
                self._icon_img.resize((64, 64), Image.Resampling.LANCZOS))
            tk.Label(row_id, image=self._logo_photo, bg=t.card_bg).pack(side="left")
        except Exception:
            pass

    text_block = tk.Frame(row_id, bg=t.card_bg)
    text_block.pack(side="left", padx=(16, 0))

    from . import __version__
    tk.Label(text_block, text="Quantum Scribe", font=(self.font_name, 17, "bold"),
             fg=t.text, bg=t.card_bg).pack(anchor="w")
    tk.Label(text_block, text=f"Versão {__version__}", font=(self.font_name, 10, "bold"),
             fg=t.accent, bg=t.card_bg).pack(anchor="w", pady=(2, 4))
    tk.Label(text_block, text="Transcrição de voz privada e offline com inteligência artificial.",
             font=(self.font_name, 9), fg=t.muted, bg=t.card_bg).pack(anchor="w")

    card = self._card(body, "Detalhes do Sistema")

    import sys
    row = self._row_base(card, "Interpretador Python", None)
    tk.Label(row, text=sys.version.split(" ")[0], font=(self.font_name, 9, "bold"),
             fg=t.text, bg=t.card_bg).grid(row=0, column=1, sticky="e")

    row = self._row_base(card, "Versão do Tk/Tcl", None)
    tk.Label(row, text=str(self.tk.call("info", "patchlevel")),
             font=(self.font_name, 9, "bold"),
             fg=t.text, bg=t.card_bg).grid(row=0, column=1, sticky="e")

    row = self._row_base(card, "Diretório de Instalação", str(get_project_root()))
    self._button(row, "Abrir Pasta", lambda: os.startfile(get_project_root()),
                 "secondary").grid(row=0, column=1, sticky="e")

    card = self._card(body, "Atualizações")
    update_row = self._row_base(
        card,
        "Atualização do aplicativo",
        "Baixa somente o instalador oficial. Modelos, configurações e transcrições são preservados.",
    )
    update_controls = tk.Frame(update_row, bg=t.card_bg)
    update_controls.grid(row=0, column=1, sticky="e")
    self._update_status_label = tk.Label(
        update_controls,
        text=self._update_status_text,
        font=(self.font_name, 8),
        fg=t.muted,
        bg=t.card_bg,
        wraplength=275,
        justify="right",
    )
    self._update_status_label.pack(anchor="e", pady=(0, 7))
    self._update_button = self._button(
        update_controls,
        "Verificar atualização",
        self._start_update_check,
        "primary",
    )
    self._update_button.pack(anchor="e")
    if self._update_active:
        self._set_update_ui(self._update_status_text, busy=True)

    tk.Label(
        body,
        text="Desenvolvido por Natan Melquiades.\n"
             "Quantum Scribe utiliza CTranslate2, faster-whisper e sounddevice.",
        font=(self.font_name, 8, "italic"), fg=t.muted, bg=t.bg,
        justify="center", pady=16,
    ).pack(fill="x")
    return page


SettingsWindow._page_about = _page_about


def _set_update_ui(self: SettingsWindow, message: str, *, busy: bool) -> None:
    self._update_status_text = message
    label = self._update_status_label
    button = self._update_button
    try:
        if label is not None and label.winfo_exists():
            label.configure(text=message)
        if button is not None and button.winfo_exists():
            button.configure(
                text="Aguarde…" if busy else "Verificar atualização",
                cursor="arrow" if busy else "hand2",
            )
    except tk.TclError:
        pass


def _finish_update_error(self: SettingsWindow, error: Exception) -> None:
    self._update_active = False
    self._set_update_ui(str(error), busy=False)
    messagebox.showerror("Não foi possível atualizar", str(error), parent=self)


def _start_update_check(self: SettingsWindow) -> None:
    if self._update_active:
        return
    self._update_active = True
    self._set_update_ui("Verificando a release oficial no GitHub…", busy=True)

    def worker() -> None:
        try:
            from .updater import check_for_update

            info = check_for_update()
        except Exception as error:
            self.after(0, lambda e=error: self._finish_update_error(e))
            return
        self.after(0, lambda: self._handle_update_check(info))

    threading.Thread(target=worker, daemon=True, name="quantumscribe-update-check").start()


def _handle_update_check(self: SettingsWindow, info) -> None:
    if info is None:
        self._update_active = False
        self._set_update_ui("Você já está usando a versão mais recente.", busy=False)
        self._toast("Quantum Scribe está atualizado")
        return

    size_mb = info.installer.size / (1024 * 1024)
    confirmed = messagebox.askyesno(
        "Atualização disponível",
        f"A versão {info.version} está disponível.\n\n"
        f"O Quantum Scribe baixará o pacote oficial ({size_mb:.0f} MB), validará a integridade, "
        "fechará o aplicativo, instalará a atualização e abrirá novamente.\n\n"
        "Modelos, configurações e transcrições não serão alterados.\n\nAtualizar agora?",
        parent=self,
    )
    if not confirmed:
        self._update_active = False
        self._set_update_ui(f"Versão {info.version} disponível. Atualização adiada.", busy=False)
        return
    self._set_update_ui(f"Baixando a versão {info.version}…", busy=True)

    def progress(received: int, total: int) -> None:
        percent = min(100, int(received * 100 / total)) if total else 0
        try:
            self.after(0, lambda p=percent: self._set_update_ui(f"Baixando atualização… {p}%", busy=True))
        except tk.TclError:
            pass

    def worker() -> None:
        try:
            from .updater import download_update

            installer, expected_hash = download_update(info, progress)
        except Exception as error:
            self.after(0, lambda e=error: self._finish_update_error(e))
            return
        self.after(0, lambda: self._apply_downloaded_update(installer, expected_hash))

    threading.Thread(target=worker, daemon=True, name="quantumscribe-update-download").start()


def _apply_downloaded_update(self: SettingsWindow, installer: Path, expected_hash: str) -> None:
    self._set_update_ui("Pacote verificado. Preparando a atualização…", busy=True)
    try:
        if self.on_install_update_callback is None:
            raise RuntimeError("O aplicativo não disponibilizou a atualização automática.")
        self.on_install_update_callback(installer, expected_hash)
    except Exception as error:
        self._finish_update_error(error)


SettingsWindow._set_update_ui = _set_update_ui
SettingsWindow._finish_update_error = _finish_update_error
SettingsWindow._start_update_check = _start_update_check
SettingsWindow._handle_update_check = _handle_update_check
SettingsWindow._apply_downloaded_update = _apply_downloaded_update
