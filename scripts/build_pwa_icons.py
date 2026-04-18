"""Render the four PWA icon PNGs using Pillow alone (no SVG renderer needed).

Outputs (under ``icons/``):

- ``icon-192.png``           - standard PWA icon, 192x192
- ``icon-512.png``           - standard PWA icon, 512x512
- ``icon-512-maskable.png``  - 512x512 maskable variant (Android adaptive icons)
- ``apple-touch-icon.png``   - 180x180, iOS home-screen icon

We mirror the design captured in ``assets/icon-source.svg`` (rising sun over a
sandstone reef silhouette with a mustard route line tracing the loop). Pillow
draws all primitives directly, so the only dependency is ``pillow`` -- no
cairo, no system libraries, easy to install on any platform the build runs on.

The maskable variant fills the entire canvas with the theme color and shrinks
the artwork to the inner ~80% so adaptive-icon masks on Android can crop the
corners without ever revealing transparent pixels.
"""
from __future__ import annotations

import math
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
ICONS = BASE / 'icons'

THEME_COLOR = (13, 17, 23, 255)         # matches build_pwa_assets.THEME_COLOR (#0d1117)
SKY_TOP = (28, 35, 48, 255)
SKY_BOTTOM = (13, 17, 23, 255)
REEF_TOP = (210, 105, 30, 255)
REEF_BOTTOM = (139, 58, 15, 255)
SUN_CORE = (255, 213, 107, 255)
SUN_EDGE = (241, 162, 58, 255)
ROUTE_COLOR = (245, 194, 82, 255)
TEXT_COLOR = (245, 194, 82, 255)


def _ensure_pil():
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont  # noqa: F401
    except ImportError:
        sys.exit(
            'build_pwa_icons.py needs Pillow.\n'
            '  Install with: pip install pillow'
        )


def _vertical_gradient(size, top, bottom):
    from PIL import Image
    img = Image.new('RGBA', (1, size), top)
    pixels = img.load()
    for y in range(size):
        t = y / max(1, size - 1)
        pixels[0, y] = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
            255,
        )
    return img.resize((size, size))


def _radial_sun(size, center_color, edge_color, radius):
    """Return a 2*radius square RGBA image of a radial-gradient sun."""
    from PIL import Image
    diameter = radius * 2
    img = Image.new('RGBA', (diameter, diameter), (0, 0, 0, 0))
    pixels = img.load()
    for y in range(diameter):
        for x in range(diameter):
            dx = x - radius
            dy = y - radius
            d = math.hypot(dx, dy)
            if d > radius:
                continue
            t = d / radius  # 0 (center) -> 1 (edge)
            r = int(center_color[0] + (edge_color[0] - center_color[0]) * t)
            g = int(center_color[1] + (edge_color[1] - center_color[1]) * t)
            b = int(center_color[2] + (edge_color[2] - center_color[2]) * t)
            # Soft alpha falloff at edge for a glow look.
            alpha = int(255 * (1 - t * t))
            pixels[x, y] = (r, g, b, alpha)
    return img


def _scale_polygon(points_512, size):
    """Rescale a polygon defined in the 512x512 design space to ``size``."""
    s = size / 512
    return [(int(round(x * s)), int(round(y * s))) for (x, y) in points_512]


def _draw_route(draw, size):
    """Bezier-ish route line tracing across the reef, drawn as a polyline."""
    s = size / 512
    # Sample points along the same curve that the SVG path uses.
    samples = []
    # Approximate two cubic-ish segments with manual sampling.
    ctrl_pts = [
        (70, 420), (130, 380), (170, 360), (210, 350),
        (250, 340), (290, 320), (330, 330),
        (370, 340), (410, 360), (450, 380),
    ]
    for i in range(0, len(ctrl_pts) - 3, 3):
        p0, p1, p2, p3 = ctrl_pts[i: i + 4]
        for t_step in range(0, 21):
            t = t_step / 20
            x = (
                (1 - t) ** 3 * p0[0]
                + 3 * (1 - t) ** 2 * t * p1[0]
                + 3 * (1 - t) * t * t * p2[0]
                + t ** 3 * p3[0]
            )
            y = (
                (1 - t) ** 3 * p0[1]
                + 3 * (1 - t) ** 2 * t * p1[1]
                + 3 * (1 - t) * t * t * p2[1]
                + t ** 3 * p3[1]
            )
            samples.append((x * s, y * s))
    width = max(2, int(round(9 * s)))
    draw.line(samples, fill=ROUTE_COLOR, width=width, joint='curve')


def _load_font(size_px):
    """Best-effort load a bold sans-serif font; fall back to default."""
    from PIL import ImageFont
    candidates = [
        'arialbd.ttf',
        'arial.ttf',
        'segoeuib.ttf',
        'segoeui.ttf',
        'DejaVuSans-Bold.ttf',
        'DejaVuSans.ttf',
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size_px)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _draw_year(draw, size):
    s = size / 512
    font_px = max(10, int(round(34 * s)))
    font = _load_font(font_px)
    text = '2026'
    try:
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=0)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except AttributeError:
        tw, th = font.getsize(text)  # Pillow < 9.2 fallback
    cx = size // 2 - tw // 2
    cy = int(455 * s) - th // 2
    draw.text((cx, cy), text, fill=TEXT_COLOR, font=font)


def _render_icon(size):
    """Render the design at the requested square size."""
    from PIL import Image, ImageDraw

    img = _vertical_gradient(size, SKY_TOP, SKY_BOTTOM)

    # Sun (radial gradient blob, painted with alpha).
    sun_radius = max(6, int(round(70 * size / 512)))
    sun = _radial_sun(size, SUN_CORE, SUN_EDGE, sun_radius)
    sun_cx = size // 2
    sun_cy = int(round(210 * size / 512))
    img.alpha_composite(sun, (sun_cx - sun_radius, sun_cy - sun_radius))

    draw = ImageDraw.Draw(img, 'RGBA')

    # Reef silhouette: gradient fill via two-step trick (paint solid then
    # overlay vertical gradient masked by the polygon shape).
    reef_pts = [
        (56, 400), (110, 300), (150, 360), (200, 250), (240, 330),
        (280, 220), (320, 310), (360, 260), (400, 340), (456, 300),
        (456, 470), (56, 470),
    ]
    reef_poly = _scale_polygon(reef_pts, size)

    # Build a mask the size of the bounding box of the reef and paint a
    # gradient inside it.
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).polygon(reef_poly, fill=255)
    grad = _vertical_gradient(size, REEF_TOP, REEF_BOTTOM)
    img.paste(grad, (0, 0), mask)

    _draw_route(draw, size)
    _draw_year(draw, size)

    return img


def _write(img, name, size):
    out = ICONS / name
    img.save(out, format='PNG', optimize=True)
    print(f'Wrote {out.relative_to(BASE)} ({size}x{size})')


def _maskable(size):
    """Render artwork at 80% size and center it on a theme-color square."""
    from PIL import Image
    inner = int(size * 0.80)
    pad = (size - inner) // 2
    inner_img = _render_icon(inner)
    canvas = Image.new('RGBA', (size, size), THEME_COLOR)
    canvas.paste(inner_img, (pad, pad), inner_img)
    return canvas


def main() -> None:
    _ensure_pil()
    ICONS.mkdir(parents=True, exist_ok=True)
    _write(_render_icon(192), 'icon-192.png', 192)
    _write(_render_icon(512), 'icon-512.png', 512)
    _write(_render_icon(180), 'apple-touch-icon.png', 180)
    _write(_maskable(512), 'icon-512-maskable.png', 512)


if __name__ == '__main__':
    main()
