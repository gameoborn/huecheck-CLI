"""Analysis, terminal summary, and self-contained HTML rendering."""
from __future__ import annotations

import html
from collections import defaultdict
from .contrast import contrast_ratio
from .cvd import delta_e_rgb, simulate
from .parser import Span
from .themes import load_themes, resolve_color


def analyze(spans: list[Span], min_contrast: float = 4.5, delta_threshold: float = 10.0) -> list[dict]:
    results = []
    for name, theme in load_themes().items():
        checked = []
        for span in spans:
            fg = resolve_color(span.foreground, theme, foreground=True)
            bg = resolve_color(span.background, theme, foreground=False)
            if span.reverse:
                fg, bg = bg, fg
            ratio = contrast_ratio(fg, bg)
            checked.append({"span":span,"fg":fg,"bg":bg,"ratio":ratio,"fails":ratio < min_contrast})
        # Text identity is used as a conservative proxy for semantic categories.
        # Compare distinct colors on distinct text runs after each CVD simulation.
        cvd_fails = []
        by_text = {}
        for item in checked:
            key = item["span"].text.strip()
            if key and key not in by_text:
                by_text[key] = item["fg"]
        entries = list(by_text.items())
        for deficiency in ("protanopia", "deuteranopia", "tritanopia"):
            transformed = [(label, simulate(rgb, deficiency)) for label, rgb in entries]
            for i, (left, c1) in enumerate(transformed):
                for j, (right, c2) in enumerate(transformed[i + 1:], i + 1):
                    # Identical source colors cannot distinguish two meanings in the first place.
                    if entries[i][1] == entries[j][1]:
                        continue
                    distance = delta_e_rgb(c1, c2)
                    if distance < delta_threshold:
                        cvd_fails.append({"deficiency":deficiency,"left":left,"right":right,"delta":distance})
        results.append({"theme":name,"theme_data":theme,"spans":checked,"worst":min((x["ratio"] for x in checked), default=21.0),"failures":sum(x["fails"] for x in checked),"cvd":cvd_fails})
    return sorted(results, key=lambda x: (x["worst"], -x["failures"], x["theme"]))


def terminal_summary(results: list[dict], min_contrast: float) -> str:
    lines = [f"Huecheck — minimum contrast {min_contrast:.2f}:1", "Theme                         Worst    Failing spans  CVD pairs", "----------------------------  -------  -------------  ---------"]
    for result in results:
        lines.append(f"{result['theme'][:28]:28}  {result['worst']:5.2f}:1  {result['failures']:13}  {len(result['cvd']):9}")
    return "\n".join(lines)


def html_report(spans: list[Span], results: list[dict], title: str = "Huecheck report", min_contrast: float = 4.5) -> str:
    sections=[]
    for result in results:
        theme=result["theme_data"]
        bits=[]
        for item in result["spans"]:
            span=item["span"]
            fg,bg=item["fg"],item["bg"]
            if span.bold:
                fg=tuple(min(255, round(c*1.15)) for c in fg)
            style=f"color:rgb{fg};background-color:rgb{bg};" + ("font-weight:bold;" if span.bold else "")
            if item["fails"]:
                style += "text-decoration:underline wavy #ff3b30;text-decoration-thickness:2px;"
            bits.append(f'<span style="{style}" title="Contrast {item["ratio"]:.2f}:1">{html.escape(span.text)}</span>')
        fail=result["failures"]
        sections.append(f'<details><summary>{html.escape(result["theme"])} — worst {result["worst"]:.2f}:1, {fail} failing spans, {len(result["cvd"])} CVD pairs</summary><div class="terminal" style="color:{theme["foreground"]};background:{theme["background"]}"><pre>{"".join(bits)}</pre></div></details>')
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(title)}</title><style>body{{font:15px system-ui,sans-serif;margin:2rem auto;max-width:1100px;padding:0 1rem;color:#222}}summary{{cursor:pointer;padding:.7rem;background:#f1f3f5;margin:.35rem 0}}.terminal{{padding:1rem;border-radius:6px;overflow:auto}}pre{{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace}}small{{color:#555}}</style></head><body><h1>{html.escape(title)}</h1><p>ANSI capture rendered across {len(results)} terminal themes. Wavy underlines mark spans below {min_contrast:.2f}:1 contrast.</p>{''.join(sections)}</body></html>'''
