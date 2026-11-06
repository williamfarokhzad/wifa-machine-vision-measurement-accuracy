"""Regenerate the editable SVG plots and optimized WebP from the CSV examples.

Optional figure tools: Inkscape and Pillow. The lab and tests do not need these.
Run from the repository root: python diagrams/render.py
"""
import csv
from decimal import Decimal
from pathlib import Path
import subprocess
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagrams"
W, H = 900, 420
COLORS = {"center": "#06736c", "edge": "#ad491e"}


def plot(example, title, filename):
    with (ROOT / "examples" / example).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows_by_cell = {}
    for row in rows:
        cell = (row["reference_id"], row["zone"])
        rows_by_cell.setdefault(cell, []).append(float(Decimal(row["reading_mm"]) -
                                                        Decimal(row["reference_mm"])))
    low, high = (-.10, .28) if filename.endswith("field-bias") else (-.10, .10)
    ticks = [-.1, 0, .1, .2] if high > .1 else [-.1, -.05, 0, .05, .1]
    x = lambda n: 260 + (n - low) * 590 / (high - low)
    elements = [f'<rect width="{W}" height="{H}" rx="18" fill="#f3f9f8"/>',
                f'<text x="33" y="51" font-size="36" font-weight="bold">{title}</text>',
                '<text x="34" y="87" font-size="24">Signed error: reading minus reference (mm)</text>']
    for tick in ticks:
        px = x(tick)
        color, width = ("#385365", 3) if tick == 0 else ("#bed2d5", 1)
        label = "0" if tick == 0 else f"{tick:+.2f}".replace("-", "−")
        elements += [f'<path d="M{px:.2f} 113 V333" stroke="{color}" stroke-width="{width}"/>',
                     f'<text x="{px:.2f}" y="365" text-anchor="middle" font-size="23">{label}</text>']
    for idx, ((ref, zone), readings) in enumerate(rows_by_cell.items()):
        y = 141 + idx * 54
        color = COLORS[zone]
        label = {"A10": "10 mm", "B30": "30 mm"}[ref]
        elements.append(f'<text x="34" y="{y+8}" font-size="24">{label} {zone}</text>')
        elements.append(f'<path d="M{x(min(readings)):.2f} {y} H{x(max(readings)):.2f}" stroke="{color}" stroke-width="4"/>')
        for value in readings:
            px = x(value)
            if zone == "center":
                elements.append(f'<circle cx="{px:.2f}" cy="{y}" r="7" fill="{color}"/>')
            else:
                elements.append(f'<rect x="{px-6:.2f}" y="{y-6}" width="12" height="12" rx="2" fill="{color}"/>')
    elements.append('<text x="34" y="400" font-size="20">Each mark is one synthetic reading.</text>')
    svg = OUT / (filename + ".svg")
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
                   '<g font-family="DejaVu Sans,sans-serif" fill="#173746">'
                   + "".join(elements) + "</g></svg>\n", encoding="utf-8")
    with tempfile.TemporaryDirectory() as temp:
        png = Path(temp) / "diagram.png"
        subprocess.run(["inkscape", str(svg), "--export-filename=" + str(png)], check=True)
        with Image.open(png) as image:
            image.convert("RGB").save(OUT / (filename + ".webp"), "WEBP", quality=87, method=6)


if __name__ == "__main__":
    plot("field-offset.csv", "Stable readings, shifted at the edge", "vision-gauge-field-bias")
    plot("noisy-center.csv", "Zero bias can hide scattered readings", "vision-gauge-reading-spread")
