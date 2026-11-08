"""Load bundled terminal themes and resolve ANSI palette colors."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .contrast import RGB, parse_hex

THEME_DIR = Path(__file__).with_name("themes")


@lru_cache(maxsize=1)
def load_themes() -> dict[str, dict]:
    themes = {}
    for path in sorted(THEME_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            theme = json.load(handle)
        if len(theme.get("ansi", [])) != 16 or not theme.get("foreground") or not theme.get("background"):
            raise ValueError(f"invalid theme definition: {path}")
        themes[theme["name"]] = theme
    return themes


def resolve_color(color: tuple | str | None, theme: dict, *, foreground: bool = True) -> RGB:
    if color is None or color == "default":
        return parse_hex(theme["foreground" if foreground else "background"])
    if isinstance(color, tuple):
        if color[0] == "ansi":
            return parse_hex(theme["ansi"][color[1]])
        if color[0] == "rgb":
            return color[1]
    raise ValueError(f"unsupported color value: {color!r}")


def xterm_256(index: int) -> RGB:
    """Convert an xterm 256-color index to RGB."""
    if not 0 <= index <= 255:
        raise ValueError("color index must be between 0 and 255")
    base = ((0, 0, 0), (205, 0, 0), (0, 205, 0), (205, 205, 0), (0, 0, 238), (205, 0, 205), (0, 205, 205), (229, 229, 229), (127, 127, 127), (255, 0, 0), (0, 255, 0), (255, 255, 0), (92, 92, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255))
    if index < 16:
        return base[index]
    if index < 232:
        n = index - 16
        levels = (0, 95, 135, 175, 215, 255)
        return levels[n // 36], levels[(n // 6) % 6], levels[n % 6]
    gray = 8 + 10 * (index - 232)
    return gray, gray, gray
