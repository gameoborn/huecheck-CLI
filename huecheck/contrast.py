"""Color parsing and WCAG contrast calculations."""
from __future__ import annotations

from typing import TypeAlias

RGB: TypeAlias = tuple[int, int, int]


def parse_hex(value: str) -> RGB:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        raise ValueError(f"expected 3- or 6-digit hex color, got {value!r}")
    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError as exc:
        raise ValueError(f"invalid hex color: {value!r}") from exc


def to_hex(rgb: RGB) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c))) for c in rgb)


def relative_luminance(rgb: RGB) -> float:
    channels = []
    for component in rgb:
        c = component / 255.0
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(foreground: RGB, background: RGB) -> float:
    lighter, darker = sorted((relative_luminance(foreground), relative_luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)
