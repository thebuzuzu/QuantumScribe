"""Renderizadores portáteis para efeitos visuais do HUD.

O Liquid Orb é deliberadamente rasterizado em baixa resolução. Assim ele pode
ser usado pelo Canvas atual tanto no Windows quanto no Linux, sem navegador,
GPU, processo externo ou dependências além do Pillow já usado pelo HUD.
"""

from __future__ import annotations

import math
from typing import Literal

from PIL import Image

LiquidOrbState = Literal["recording", "transcribing", "error", "exploding", "success"]

ORB_THEMES = frozenset({"liquid_orb", "prismatic_bubble"})

DEFAULT_ORB_COLOR = "#BF5AF2"
ERROR_ORB_COLOR = "#FF647C"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _parse_hex_color(value: str) -> tuple[int, int, int]:
    try:
        hex_value = str(value).strip().lstrip("#")
        if len(hex_value) != 6:
            raise ValueError
        return tuple(int(hex_value[index:index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]
    except (TypeError, ValueError):
        fallback = DEFAULT_ORB_COLOR.lstrip("#")
        return tuple(int(fallback[index:index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]


def _mix_color(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:
    ratio = _clamp(amount)
    return tuple(
        int(round(left + (right - left) * ratio))
        for left, right in zip(first, second)
    )  # type: ignore[return-value]


def _smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    ratio = _clamp((value - edge0) / (edge1 - edge0))
    return ratio * ratio * (3.0 - 2.0 * ratio)


def render_liquid_orb(
    size: int = 56,
    time_value: float = 0.0,
    color: str = DEFAULT_ORB_COLOR,
    amplitude: float = 0.0,
    state: LiquidOrbState = "recording",
    scale: float = 1.0,
    opacity: float = 1.0,
    jitter: tuple[float, float] = (0.0, 0.0),
) -> Image.Image:
    """Gera um frame determinístico do Liquid Orb em RGBA.

    ``time_value`` é fornecido pelo consumidor para que a animação permaneça
    testável. O frame não lê relógio, áudio, rede ou qualquer estado global.
    """
    if size < 20:
        raise ValueError("Liquid Orb exige uma área mínima de 20 pixels")

    size = int(size)
    phase = float(time_value)
    amp = _clamp(float(amplitude))
    orb_scale = _clamp(float(scale), 0.55, 2.4)
    global_alpha = _clamp(float(opacity))
    base_color = _parse_hex_color(color)

    if state == "error":
        base_color = _mix_color(base_color, _parse_hex_color(ERROR_ORB_COLOR), 0.72)
        energy = 0.65
    elif state == "transcribing":
        energy = 0.36
    elif state == "exploding":
        energy = 1.0
    elif state == "success":
        base_color = _mix_color(base_color, (92, 252, 124), 0.7)
        energy = 1.1
    else:
        energy = 0.8

    dark = tuple(max(2, int(channel * 0.22)) for channel in base_color)
    light = _mix_color(base_color, (255, 255, 255), 0.42)
    highlight = _mix_color(light, (255, 255, 255), 0.42)
    center = (size - 1) / 2.0
    radius = size * 0.335 * orb_scale
    pixels: list[tuple[int, int, int, int]] = []

    jitter_x, jitter_y = jitter
    for y in range(size):
        for x in range(size):
            dx = x - center - float(jitter_x)
            dy = y - center - float(jitter_y)
            nx = dx / max(radius, 1.0)
            ny = dy / max(radius, 1.0)
            distance = math.sqrt(nx * nx + ny * ny)

            fluid = (
                math.sin(nx * 3.4 + phase * 1.25 + math.sin(ny * 2.2 + phase * 0.6))
                + math.cos(ny * 4.1 - phase * 0.9 + nx * 1.4)
                + math.sin((nx + ny) * 5.2 + phase * 0.45) * 0.55
            ) / 2.55
            surface = distance + fluid * 0.075 * (0.6 + amp * 0.7)
            body_alpha = 1.0 - _smoothstep(0.91, 1.04, surface)
            rim = 1.0 - _smoothstep(0.84, 1.02, distance)
            specular = math.exp(-(((nx + 0.30) / 0.48) ** 2 + ((ny + 0.38) / 0.36) ** 2))
            inner_glow = math.exp(-((nx * 0.7) ** 2 + (ny * 0.7) ** 2))

            shade = _clamp(0.43 + fluid * 0.23 + amp * 0.18 + inner_glow * 0.1)
            rgb = _mix_color(dark, light, shade)
            rgb = _mix_color(rgb, highlight, _clamp(specular * 0.75))
            rgb = _mix_color(rgb, base_color, _clamp(rim * 0.24))

            glow_distance = max(0.0, distance - 0.88)
            glow = max(0.0, 1.0 - glow_distance / 0.58) ** 2 * 0.34
            alpha = _clamp((body_alpha * (0.78 + energy * 0.14) + glow) * global_alpha)

            if state == "exploding":
                flare = max(0.0, 1.0 - abs(distance - 1.0) / 0.22)
                alpha = _clamp(alpha + flare * 0.22)
                rgb = _mix_color(rgb, (255, 255, 255), flare * 0.5)

            pixels.append((*rgb, int(round(alpha * 255))))

    return Image.new("RGBA", (size, size), (0, 0, 0, 0)) if not pixels else Image.frombytes(
        "RGBA", (size, size), bytes(channel for pixel in pixels for channel in pixel)
    )


def render_prismatic_bubble(
    size: int = 56,
    time_value: float = 0.0,
    color: str = DEFAULT_ORB_COLOR,
    amplitude: float = 0.0,
    state: LiquidOrbState = "recording",
    scale: float = 1.0,
    opacity: float = 1.0,
    jitter: tuple[float, float] = (0.0, 0.0),
) -> Image.Image:
    """Render two overlapping liquid lobes with a prismatic color split."""
    if size < 20:
        raise ValueError("Prismatic Bubble exige uma área mínima de 20 pixels")

    size = int(size)
    lobe_size = max(20, int(round(size * 0.78)))
    center = max(0, (size - lobe_size) // 2)
    shift = min(max(1, size // 12), max(0, size - lobe_size))
    base = _parse_hex_color(color)
    blue = _mix_color(base, (55, 220, 255), 0.64)
    pink = _mix_color(base, (255, 74, 190), 0.64)

    def as_hex(rgb: tuple[int, int, int]) -> str:
        return "#%02X%02X%02X" % rgb

    left = render_liquid_orb(
        size=lobe_size,
        time_value=float(time_value) * 0.94,
        color=as_hex(blue),
        amplitude=amplitude,
        state=state,
        scale=scale,
        opacity=opacity * 0.90,
        jitter=jitter,
    )
    right = render_liquid_orb(
        size=lobe_size,
        time_value=float(time_value) * 1.08 + 0.42,
        color=as_hex(pink),
        amplitude=amplitude,
        state=state,
        scale=scale,
        opacity=opacity * 0.90,
        jitter=(-jitter[0], jitter[1]),
    )
    frame = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    frame.alpha_composite(left, dest=(max(0, center - shift), center))
    frame.alpha_composite(right, dest=(min(size - lobe_size, center + shift), center))
    return frame


class LiquidOrbRenderer:
    """Pequeno adaptador stateful para o loop de animação do ``Popup``."""

    def __init__(self, size: int = 56, effect: str = "liquid_orb") -> None:
        if size < 20:
            raise ValueError("Liquid Orb exige um tamanho mínimo de 20 pixels")
        if effect not in ORB_THEMES:
            raise ValueError(f"Efeito de HUD desconhecido: {effect}")
        self.size = int(size)
        self.effect = effect

    def render(
        self,
        *,
        time_value: float,
        color: str,
        amplitude: float,
        state: LiquidOrbState,
        scale: float,
        opacity: float,
        jitter: tuple[float, float] = (0.0, 0.0),
    ) -> Image.Image:
        render = render_prismatic_bubble if self.effect == "prismatic_bubble" else render_liquid_orb
        return render(
            size=self.size,
            time_value=time_value,
            color=color,
            amplitude=amplitude,
            state=state,
            scale=scale,
            opacity=opacity,
            jitter=jitter,
        )


class PrismaticBubbleRenderer(LiquidOrbRenderer):
    """Named adapter kept for callers that want the second bubble explicitly."""

    def __init__(self, size: int = 56) -> None:
        super().__init__(size=size, effect="prismatic_bubble")
