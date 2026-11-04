"""Build assets/header.svg. Run: python3 scripts/build.py

GitHub shows it through <img>, so no scripts or web fonts: CSS only.
assets/tools.svg is a saved skillicons.dev grid, plus Claude and Oracle tiles
from Simple Icons, which skill-icons lacks.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

ASSETS = Path(__file__).resolve().parent.parent / "assets"

W, H = 960, 320
BG, BAR, LINE, GLOW = "#0a0e0e", "#121717", "#6f9c8e", "#a9cdbf"
GHOST = "#3d5a52"
LEFT = 150
PROMPT, TEXT, ACCENT = "#5fbfa2", "#f4f4f5", "#a3d9c5"
MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace'
SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif'

ROLE = "Distributed Systems · Payments Infrastructure · AI Agents..."
LOOP = 17.0
SPEED = 0.05

# (prompt, text, baseline, size, colour, weight)
LINES = [
    ("~$", "Hey, I'm Jack", 104, 38, TEXT, 700),
    ("❯", "Welcome to my GitHub Corner", 156, 20, TEXT, 400),
    ("❯", "Let's chat and build:", 194, 20, TEXT, 400),
    ("", ROLE, 232, 18, ACCENT, 600),
]

# Where the nodes gather: (x from, x to, y from, y to, count). A light spread across
# the whole card, weighted to the top left and bottom right.
AREAS = [(-40, 1000, 30, 350, 16), (-40, 270, -30, 165, 13), (690, 1000, 185, 350, 13)]
TEXT_BOX = (150, 62, 850, 245)


def scatter(rng: random.Random, scale: float) -> list[tuple[float, float]]:
    left, top, right, bottom = TEXT_BOX
    nodes: list[tuple[float, float]] = []
    for x0, x1, y0, y1, count in AREAS:
        added = 0
        while added < round(count * scale):
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            if left < x < right and top < y < bottom and rng.random() < 0.75:
                continue  # few nodes directly behind the words
            if all(math.dist((x, y), other) > 36 for other in nodes):
                nodes.append((x, y))
                added += 1
    return nodes


def layer(seed: int, *, ghost: bool) -> str:
    rng = random.Random(seed)
    nodes = scatter(rng, 0.8 if ghost else 1.0)
    links: set[tuple[int, int]] = set()
    for i, point in enumerate(nodes):
        ranked = sorted((j for j in range(len(nodes)) if j != i), key=lambda j: math.dist(point, nodes[j]))
        picks = rng.sample(ranked[:5], 2) + rng.sample(ranked[5:14], 1 if rng.random() < 0.6 else 0)
        links.update((min(i, j), max(i, j)) for j in picks)
    colour, width, opacity = (GHOST, 0.7, 0.5) if ghost else (LINE, 0.8, 0.6)
    out = [f'<g stroke="{colour}" stroke-width="{width}" stroke-opacity="{opacity}" fill="none">']
    out += [
        f'<line x1="{nodes[a][0]:.1f}" y1="{nodes[a][1]:.1f}" x2="{nodes[b][0]:.1f}" y2="{nodes[b][1]:.1f}"/>'
        for a, b in sorted(links)
    ]
    out.append("</g>")
    for i, (x, y) in enumerate(nodes):
        radius = rng.uniform(4, 7) if ghost else rng.choice((2.4, 3, 3.6, 4.4, 5.2))
        fill = GHOST if ghost else GLOW
        twinkle = f' class="tw" style="animation-delay:-{rng.uniform(0, 8):.1f}s"' if i % 3 == 0 else ""
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{fill}" fill-opacity="{0.45 if ghost else 0.95}"{twinkle}/>')
    return "".join(out)


def typed(text: str, x: float, y: float, size: float, fill: str, weight: int, clock: float, name: str) -> tuple[str, str, float]:
    """One line revealed a character at a time.

    The card behind it is not a flat colour, so nothing can slide off the text
    to uncover it. Each character is a tspan with its own moment to appear.
    """
    spans: list[str] = []
    css: list[str] = []
    for i, ch in enumerate(text):
        at = (clock + i * SPEED) / LOOP * 100
        spans.append(f'<tspan class="{name}{i}">{escape(ch)}</tspan>')
        css.append(
            f".{name}{i} {{ animation: {name}{i} {LOOP}s steps(1) infinite; }}"
            f"@keyframes {name}{i} {{ 0% {{ fill-opacity: 0; }} {at:.2f}%,100% {{ fill-opacity: 1; }} }}"
        )
    svg = (
        f'<text class="mono" x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" style="white-space:pre">{"".join(spans)}</text>'
    )
    return svg, "".join(css), clock + len(text) * SPEED


def prompt(symbol: str, x: float, y: float, size: float, clock: float, name: str) -> tuple[str, str]:
    at = clock / LOOP * 100
    svg = f'<text class="mono {name}" x="{x}" y="{y}" font-size="{size}" font-weight="600" fill="{PROMPT}">{symbol}</text>'
    css = (
        f".{name} {{ animation: {name} {LOOP}s steps(1) infinite; }}"
        f"@keyframes {name} {{ 0% {{ opacity: 0; }} {at:.2f}%,100% {{ opacity: 1; }} }}"
    )
    return svg, css


def session() -> tuple[str, str]:
    svg: list[str] = []
    css: list[str] = []
    clock = 0.5
    for n, (symbol, text, y, size, fill, weight) in enumerate(LINES):
        left = LEFT
        if symbol:
            mark, mark_css = prompt(symbol, left, y, size, clock, f"m{n}")
            svg.append(mark)
            css.append(mark_css)
        start = left + (len(symbol) + 1) * size * 0.6 if symbol else left + 27
        line, line_css, clock = typed(text, start, y, size, fill, weight, clock, f"c{n}x")
        svg.append(line)
        css.append(line_css)
        clock += 0.45
    # A blinking block after the last character, once typing is done.
    left = LEFT + 27 + len(LINES[-1][1]) * LINES[-1][3] * 0.6 + 6
    blink = [f"0% {{ opacity: 0; }}"]
    t = clock
    on = True
    while t < LOOP:
        blink.append(f"{t / LOOP * 100:.2f}% {{ opacity: {1 if on else 0}; }}")
        on = not on
        t += 0.5
    svg.append(f'<rect class="cur" x="{left:.1f}" y="{LINES[-1][2] - 15}" width="10" height="19" fill="{PROMPT}"/>')
    css.append(f".cur {{ animation: cur {LOOP}s steps(1) infinite; }}@keyframes cur {{ {' '.join(blink)} }}")
    return "".join(svg), "".join(css)


def header() -> str:
    term, term_css = session()
    title = "Hey, I'm Jack. Welcome to my GitHub Corner. Let's chat and build: " + ROLE.rstrip(".")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">{escape(title)}</title>
<defs>
<linearGradient id="border" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".12"/><stop offset=".55" stop-color="#ffffff" stop-opacity=".06"/><stop offset="1" stop-color="#10b981" stop-opacity=".22"/></linearGradient>
<filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="62"/></filter>
<radialGradient id="clear" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{BG}" stop-opacity=".8"/><stop offset=".72" stop-color="{BG}" stop-opacity=".62"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>
</defs>
<style>
.mono {{ font-family: {MONO}; }} .sans {{ font-family: {SANS}; }}
.orb {{ animation: orb 20s ease-in-out infinite alternate; }}
@keyframes orb {{ to {{ transform: translate(-90px, -26px); }} }}
.far {{ animation: far 34s ease-in-out infinite alternate; }}
@keyframes far {{ from {{ transform: translate(7px, -4px); }} to {{ transform: translate(-7px, 4px); }} }}
.near {{ animation: near 26s ease-in-out infinite alternate; }}
@keyframes near {{ from {{ transform: translate(-12px, -6px); }} to {{ transform: translate(12px, 6px); }} }}
.tw {{ animation: tw 7s ease-in-out infinite; }} @keyframes tw {{ 50% {{ opacity: .4; }} }}
{term_css}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<circle class="orb" cx="800" cy="240" r="170" fill="#10b981" opacity=".075" filter="url(#blur)"/>
<circle cx="130" cy="60" r="130" fill="#ffffff" opacity=".05" filter="url(#blur)"/>
<g class="far">{layer(5, ghost=True)}</g>
<g class="near">{layer(32, ghost=False)}</g>
<ellipse cx="490" cy="160" rx="470" ry="130" fill="url(#clear)"/>
<rect width="{W}" height="38" fill="{BAR}"/>
</g>
<line x1="0" y1="38" x2="{W}" y2="38" stroke="#ffffff" stroke-opacity=".08"/>
<circle cx="22" cy="19" r="6" fill="#ff5f57"/><circle cx="42" cy="19" r="6" fill="#febc2e"/><circle cx="62" cy="19" r="6" fill="#28c840"/>
{term}
<text x="{LEFT}" y="296" class="sans" font-size="12.5" font-style="italic" fill="#a1a1aa">UTC+3</text>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="url(#border)"/>
</svg>
"""


if __name__ == "__main__":
    (ASSETS / "header.svg").write_text(header(), encoding="utf-8")
