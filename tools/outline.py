"""Outline display text to SVG path data in Instrument Serif (shaped by hb-shape, so kerning is kept).

    python3 tools/outline.py regular "46.85" 96        # style, text, size in px, optional tracking in px
    python3 tools/outline.py                           # self-check

Prints the width, then the path data. Paste the data into the d="..." of the matching <path>.
The path origin is the left end of the baseline. Needs: pip install fonttools, brew install harfbuzz.
"""
import json, subprocess, sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

FONTS = Path(__file__).parent / "fonts"
STYLES = {"regular": FONTS / "InstrumentSerif-Regular.ttf", "italic": FONTS / "InstrumentSerif-Italic.ttf"}


def outline(style, text, size, tracking=0.0):
    """Return (path_d, width_px). y grows downward."""
    path = str(STYLES[style])
    font = TTFont(path)
    s = size / font["head"].unitsPerEm
    glyphs = json.loads(subprocess.run(
        ["hb-shape", "--output-format=json", "--no-glyph-names", path, text],
        check=True, capture_output=True, text=True).stdout)
    gs, order = font.getGlyphSet(), font.getGlyphOrder()
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    x = 0.0
    for i, g in enumerate(glyphs):
        gs[order[g["g"]]].draw(TransformPen(pen, (s, 0, 0, -s, x + g.get("dx", 0) * s, -g.get("dy", 0) * s)))
        x += g["ax"] * s + (tracking if i < len(glyphs) - 1 else 0)
    return pen.getCommands(), x


if __name__ == "__main__":
    if len(sys.argv) < 4:
        d, w = outline("regular", "SPIRA", 44)
        _, w2 = outline("regular", "SPIRA", 44, tracking=12)
        assert d.startswith("M") and w > 0 and abs((w2 - w) - 48) < 1e-6, (w, w2)
        print("self-check ok")
    else:
        d, w = outline(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]) if len(sys.argv) > 4 else 0.0)
        print(f"width {w:.1f}px", file=sys.stderr)
        print(d)
