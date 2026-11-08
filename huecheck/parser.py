"""Parse ANSI SGR styling into text spans while retaining control-free text."""
from __future__ import annotations

from dataclasses import dataclass
import re

from .contrast import RGB
from .themes import xterm_256

@dataclass(frozen=True)
class Span:
    foreground: tuple | str | None
    background: tuple | str | None
    text: str
    bold: bool = False
    reverse: bool = False

SGR_RE = re.compile(r"\x1b\[([0-9;:]*)m")
ANSI_TO_INDEX = {30:0,31:1,32:2,33:3,34:4,35:5,36:6,37:7,90:8,91:9,92:10,93:11,94:12,95:13,96:14,97:15}


def parse_ansi(data: str | bytes) -> list[Span]:
    """Parse SGR sequences. Other CSI/OSC controls are removed from visible text."""
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="replace")
    # State uses None for theme default, and resets correctly at SGR 0.
    fg: tuple | str | None = None
    bg: tuple | str | None = None
    bold = reverse = False
    spans: list[Span] = []
    pos = 0
    for match in SGR_RE.finditer(data):
        if match.start() > pos:
            text = data[pos:match.start()]
            if text:
                spans.append(Span(fg, bg, text, bold, reverse))
        raw = match.group(1)
        # Colon subparameters are normalized to semicolons for common xterm forms.
        parts = raw.replace(":", ";").split(";") if raw else ["0"]
        nums = [int(x) if x.isdigit() else 0 for x in parts]
        i = 0
        while i < len(nums):
            n = nums[i]
            if n == 0: fg, bg, bold, reverse = None, None, False, False
            elif n == 1: bold = True
            elif n == 22: bold = False
            elif n == 7: reverse = True
            elif n == 27: reverse = False
            elif n == 39: fg = None
            elif n == 49: bg = None
            elif n in ANSI_TO_INDEX: fg = ("ansi", ANSI_TO_INDEX[n])
            elif n in (38, 48) and i + 1 < len(nums):
                is_fg = n == 38
                mode = nums[i + 1]
                if mode == 5 and i + 2 < len(nums):
                    value = ("rgb", xterm_256(nums[i + 2]))
                    i += 2
                elif mode == 2 and i + 4 < len(nums):
                    value = ("rgb", tuple(max(0,min(255,c)) for c in nums[i + 2:i + 5]))
                    i += 4
                else:
                    i += 1
                    continue
                if is_fg: fg = value
                else: bg = value
            i += 1
        pos = match.end()
    if pos < len(data):
        spans.append(Span(fg, bg, data[pos:], bold, reverse))
    # Strip non-SGR terminal control strings from text (OSC, other CSI, C0 except newline/tab).
    clean = []
    for span in spans:
        text = re.sub(r"\x1b\][^\x07]*(?:\x07|\x1b\\)", "", span.text)
        text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
        text = re.sub(r"\x1b[@-_]", "", text)
        if text:
            clean.append(Span(span.foreground, span.background, text, span.bold, span.reverse))
    return clean
