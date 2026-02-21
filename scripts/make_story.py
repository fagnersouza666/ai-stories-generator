#!/usr/bin/env python3
"""Generate Instagram Story images (1080x1920) from article screenshots + copy.

Input: a JSON file with items:
[
  {
    "title": "...",
    "url": "https://...",
    "subtitle": "...",   # 1-2 lines
    "impact": "...",     # 1 line
    "screenshot": "path/to/screenshot.png"
  }
]

Output: PNGs in out-dir.

Usage:
  python make_story.py --in items.json --out-dir out/

"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920


def fit_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    # cover crop
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    # Use DejaVu fonts typically present
    paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int):
    words = text.split()
    lines = []
    cur = ''
    for w in words:
        test = (cur + ' ' + w).strip()
        tw = draw.textlength(test, font=font)
        if tw <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render(item: dict, out_path: Path):
    shot = Image.open(item['screenshot']).convert('RGB')
    bg = fit_cover(shot, W, H)

    # Darken + slight blur for readability
    bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 140))
    bg = bg.convert('RGBA')
    bg.alpha_composite(overlay)

    draw = ImageDraw.Draw(bg)

    title_font = load_font(64, bold=True)
    sub_font = load_font(42, bold=False)
    impact_font = load_font(48, bold=True)
    small_font = load_font(28, bold=False)

    margin = 70
    maxw = W - 2 * margin

    y = 140
    # Title (max ~3 lines)
    title_lines = wrap_text(draw, item.get('title','').strip(), title_font, maxw)[:3]
    for ln in title_lines:
        draw.text((margin, y), ln, font=title_font, fill=(255, 255, 255, 255))
        y += title_font.size + 10

    y += 20
    subtitle = item.get('subtitle','').strip()
    if subtitle:
        sub_lines = wrap_text(draw, subtitle, sub_font, maxw)[:3]
        for ln in sub_lines:
            draw.text((margin, y), ln, font=sub_font, fill=(230, 230, 230, 255))
            y += sub_font.size + 8

    # Impact bar near bottom
    impact = item.get('impact','').strip()
    if impact:
        bar_h = 220
        bar_y = H - bar_h - 170
        bar = Image.new('RGBA', (W, bar_h), (0, 0, 0, 170))
        bg.alpha_composite(bar, (0, bar_y))
        draw = ImageDraw.Draw(bg)
        y2 = bar_y + 40
        lines = wrap_text(draw, impact, impact_font, maxw)[:3]
        for ln in lines:
            draw.text((margin, y2), ln, font=impact_font, fill=(255, 255, 255, 255))
            y2 += impact_font.size + 10

    # Footer
    url = item.get('url','')
    footer = url.replace('https://','').replace('http://','')
    draw.text((margin, H-70), footer[:60], font=small_font, fill=(200, 200, 200, 255))

    bg.convert('RGB').save(out_path, 'PNG')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out-dir', required=True)
    args = ap.parse_args()

    items = json.loads(Path(args.inp).read_text(encoding='utf-8'))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, it in enumerate(items, start=1):
        out = out_dir / f"story_{i:02d}.png"
        render(it, out)
        print('WROTE', out)


if __name__ == '__main__':
    main()
