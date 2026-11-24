#!/usr/bin/env python3
"""Share-Bild (Open Graph, 1200×630) und Favicons für winddashboard.at.

Aufruf:  python3 scripts/render_social.py
Braucht geopandas, matplotlib, Pillow und die Schrift DM Sans (~/Library/Fonts).
Schreibt nach static/: og-image.jpg, apple-touch-icon.png, icon-192.png,
icon-512.png, favicon.ico. favicon.svg ist handgeschrieben und dient als Vorlage
für die Rasterfassungen (gleiche Geometrie wie TURBINE unten).
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image, ImageDraw
from shapely.geometry import Polygon

REPO = Path(__file__).resolve().parent.parent
STATIC = REPO / "static"

for f in Path.home().joinpath("Library/Fonts").glob("DMSans-*.ttf"):
    font_manager.fontManager.addfont(str(f))
plt.rcParams["font.family"] = "DM Sans"

BG = "#f8f9fc"
TEXT = "#1a1a2e"
MUTED = "#475569"
BLUE = "#2563eb"
BRAND = "#1d4ed8"  # theme-color in app.html
LAND = "#e2e8f0"


# ── Share-Bild ────────────────────────────────────────────────────────────────
def render_og() -> None:
    crs = 31287  # MGI / Austria Lambert
    outline = gpd.read_file(STATIC / "data/austria_outline.json").to_crs(crs)
    union = outline.union_all()
    main = max(getattr(union, "geoms", [union]), key=lambda g: g.area)
    austria = gpd.GeoSeries([Polygon(main.exterior)], crs=crs)
    zones = gpd.read_file(REPO / "geodata/possible_zones.geojson").to_crs(crs)

    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor(BG)

    # Karte rechts unten, groß; Österreich ist etwa 2,2 : 1.
    ax = fig.add_axes([0.30, 0.02, 0.70, 0.64])
    ax.set_facecolor(BG)
    austria.plot(ax=ax, color=LAND, linewidth=0)
    # Dünne Kontur in derselben Farbe: Die Flächen sind im Vorschaubild
    # (oft ~500 px breit) sonst kaum mehr als Punkte.
    zones.plot(ax=ax, color=BLUE, edgecolor=BLUE, linewidth=0.45)
    austria.boundary.plot(ax=ax, color=TEXT, linewidth=1.4)
    ax.set_axis_off()
    ax.set_aspect("equal")
    minx, miny, maxx, maxy = austria.total_bounds
    pad = (maxx - minx) * 0.015
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)

    x0 = 0.055
    fig.text(x0, 0.865, "WINDDASHBOARD.AT", fontsize=17, fontweight="bold", color=BRAND)
    fig.text(x0, 0.775, "Wo in Österreich", fontsize=50, fontweight="bold", color=TEXT, va="top")
    fig.text(x0, 0.665, "Windräder möglich sind", fontsize=50, fontweight="bold", color=TEXT, va="top")

    # Kennzahl links unten neben der Karte
    fig.text(x0, 0.36, "4,2 %", fontsize=64, fontweight="bold", color=BLUE, va="bottom")
    fig.text(x0, 0.34, "der Landesfläche eignen\nsich für Windkraft", fontsize=19,
             color=MUTED, va="top", linespacing=1.3)
    fig.text(x0, 0.085, "Interaktive Karte für alle 2.116 Gemeinden", fontsize=15, color=MUTED)

    out = STATIC / "og-image.jpg"
    fig.savefig(out, dpi=100, facecolor=BG, format="jpg", pil_kwargs={"quality": 88, "optimize": True})
    plt.close(fig)
    with Image.open(out) as im:
        assert im.size == (1200, 630), im.size
    print("og-image.jpg", out.stat().st_size // 1024, "KB")


# ── Favicons ──────────────────────────────────────────────────────────────────
# Windrad auf 64er-Raster, identisch mit static/favicon.svg.
def turbine_icon(size: int, radius_frac: float = 0.22, safe: float = 1.0) -> Image.Image:
    """Blaues Quadrat mit weißem Windrad. `safe` < 1 verkleinert das Motiv
    (Android-Maskable: wichtiger Inhalt in der inneren Kreisfläche)."""
    s = 8  # Supersampling
    n = size * s
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(n * radius_frac)
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=r, fill=BRAND)

    k = n / 64 * safe
    off = n / 2 - 32 * k

    def P(x: float, y: float) -> tuple[float, float]:
        return (off + x * k, off + y * k)

    white = (255, 255, 255, 255)
    # Mast (leicht konisch)
    d.polygon([P(30.2, 25), P(33.8, 25), P(35.2, 56), P(28.8, 56)], fill=white)
    # Drei Rotorblätter um die Nabe (32, 24), je 120°
    import math
    hub = (32, 24)
    for ang in (-90, 30, 150):
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux
        L, w = 20, 3.6
        tip = (hub[0] + ux * L, hub[1] + uy * L)
        base1 = (hub[0] + px * w / 2, hub[1] + py * w / 2)
        base2 = (hub[0] - px * w / 2, hub[1] - py * w / 2)
        mid = (hub[0] + ux * L * 0.35 + px * w * 0.75, hub[1] + uy * L * 0.35 + py * w * 0.75)
        d.polygon([P(*base1), P(*mid), P(*tip), P(*base2)], fill=white)
    c = P(*hub)
    rr = 3.6 * k
    d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=white)
    return img.resize((size, size), Image.LANCZOS)


def turbine_svg() -> str:
    """Dasselbe Windrad als SVG (64er-Raster) für static/favicon.svg."""
    import math
    hub = (32, 24)
    blades = []
    for ang in (-90, 30, 150):
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux
        L, w = 20, 3.6
        pts = [
            (hub[0] + px * w / 2, hub[1] + py * w / 2),
            (hub[0] + ux * L * 0.35 + px * w * 0.75, hub[1] + uy * L * 0.35 + py * w * 0.75),
            (hub[0] + ux * L, hub[1] + uy * L),
            (hub[0] - px * w / 2, hub[1] - py * w / 2),
        ]
        blades.append('<path d="M' + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + 'Z"/>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<title>winddashboard.at</title><rect width="64" height="64" rx="14" fill="{BRAND}"/>'
        '<g fill="#fff"><path d="M30.2 25 L33.8 25 L35.2 56 L28.8 56Z"/>'
        + "".join(blades)
        + '<circle cx="32" cy="24" r="3.6"/></g></svg>\n'
    )


def render_icons() -> None:
    (STATIC / "favicon.svg").write_text(turbine_svg())
    turbine_icon(180, radius_frac=0).convert("RGB").save(STATIC / "apple-touch-icon.png")
    turbine_icon(192).save(STATIC / "icon-192.png")
    turbine_icon(512).save(STATIC / "icon-512.png")
    turbine_icon(512, radius_frac=0, safe=0.78).save(STATIC / "icon-maskable-512.png")
    ico = [turbine_icon(s) for s in (16, 32, 48)]
    ico[2].save(STATIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])
    print("icons ok")


if __name__ == "__main__":
    render_og()
    render_icons()
