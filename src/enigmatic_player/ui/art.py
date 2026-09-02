"""Render embedded album art as pixel-art.

Album covers are reduced to a 4-shade mint-green palette (dark -> bright,
matching the matrix-on-black theme) with ordered (Bayer 4x4) dithering, then
drawn as half-block cells for a chunky pixel look.
"""

from __future__ import annotations

import io
from typing import List, Optional, Tuple

# lightest -> darkest spring greens, tuned for a black background
GREENSHADES = [(160, 255, 210), (70, 220, 140), (16, 120, 78), (4, 32, 20)]

BAYER4 = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]


def _rgb(marker: str, pix: Tuple[int, int, int]) -> str:
    r, g, b = pix
    return f"[{marker}rgb({r},{g},{b})]"


def _shade_map(img, cols: int, rows2: int) -> List[List[int]]:
    """Return a cols x rows2 grid of shade indices 0..3 (lightest -> darkest)."""
    px = img.load()
    out: List[List[int]] = []
    for y in range(rows2):
        row = []
        for x in range(cols):
            lum = px[x, y]
            level = min(1.0, max(0.0, lum / 255.0))
            dither = (BAYER4[y % 4][x % 4] + 0.5) / 16.0 - 0.5
            q = int(min(3, max(0, level * 4.0 + dither)))
            row.append(q)
        out.append(row)
    return out


def render_gameboy(art_bytes: bytes, cols: int = 16) -> Optional[str]:
    """Render cover art as dither-mapped Game Boy cells (Rich markup lines)."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        img = Image.open(io.BytesIO(art_bytes)).convert("L")
    except Exception:  # noqa: BLE001
        return None

    aspect = img.height / img.width
    rows2 = max(4, round(cols * aspect * 2.0))
    img = img.resize((cols, rows2), Image.Resampling.LANCZOS)
    grid = _shade_map(img, cols, rows2)

    lines = []
    for r in range(0, rows2, 2):
        cells = []
        for x in range(cols):
            top = grid[r][x]
            bot = grid[r + 1][x] if r + 1 < rows2 else top
            ct = GREENSHADES[top]
            cb = GREENSHADES[bot]
            if top == bot:
                cells.append(f"[on rgb({ct[0]},{ct[1]},{ct[2]})] ")
            else:
                cells.append(
                    f"[rgb({ct[0]},{ct[1]},{ct[2]}) on rgb({cb[0]},{cb[1]},{cb[2]})]▀"
                )
        lines.append("".join(cells))
    return "\n".join(lines) + "\n"


PLACEHOLDER = (
    "[on rgb(4,32,20)]                                        [/]\n"
    "[on rgb(16,120,78)]      [on rgb(4,32,20)]    [/][on rgb(16,120,78)]      [/]\n"
    "[on rgb(16,120,78)]  ▄▄  [on rgb(4,32,20)]▓▓[/][on rgb(16,120,78)]  ▄▄  [/]\n"
    "[on rgb(0,0,0)]  [on rgb(16,120,78)]▀▀▀ [on rgb(4,32,20)]▓▓[/][on rgb(16,120,78)]▀▀▀ [on rgb(0,0,0)]  [/]\n"
    "[on rgb(0,0,0)] [on rgb(16,120,78)]▀▀▀▀▀ [on rgb(4,32,20)]▓▓[/][on rgb(16,120,78)]▀▀▀▀▀[/]\n"
)
