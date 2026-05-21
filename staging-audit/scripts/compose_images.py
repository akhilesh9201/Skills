#!/usr/bin/env python3
"""
Compose a side-by-side image (Figma left, staging right) with a cropped callout inset.
Usage:
  python compose_images.py --figma figma.png --staging staging.png --crop x1,y1,x2,y2 --output out.png
  python compose_images.py --figma figma.png --staging staging.png --output out.png  # no callout
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

THUMB_W = 400
THUMB_H = 300
CALLOUT_W = 300
CALLOUT_H = 200
BORDER = 4
GAP = 10
LABEL_H = 24
RED = (220, 50, 50)
DARK = (26, 26, 46)
WHITE = (255, 255, 255)


def fit(img: Image.Image, w: int, h: int) -> Image.Image:
    img.thumbnail((w, h), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), (245, 245, 245))
    x = (w - img.width) // 2
    y = (h - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def add_label(img: Image.Image, text: str) -> Image.Image:
    canvas = Image.new("RGB", (img.width, img.height + LABEL_H), DARK)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, img.width, LABEL_H], fill=DARK)
    draw.text((6, 4), text, fill=WHITE)
    canvas.paste(img, (0, LABEL_H))
    return canvas


def red_border(img: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for t in range(BORDER):
        draw.rectangle([t, t, w - 1 - t, h - 1 - t], outline=RED)
    return img


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--figma", required=True)
    p.add_argument("--staging", required=True)
    p.add_argument("--crop", default=None, help="x1,y1,x2,y2 on the staging screenshot")
    p.add_argument("--output", required=True)
    args = p.parse_args()

    figma = fit(Image.open(args.figma).convert("RGB"), THUMB_W, THUMB_H)
    staging = fit(Image.open(args.staging).convert("RGB"), THUMB_W, THUMB_H)

    figma = add_label(figma, "Figma design")
    staging = add_label(staging, "Staging build")

    if args.crop:
        x1, y1, x2, y2 = map(int, args.crop.split(","))
        src = Image.open(args.staging).convert("RGB")
        crop = src.crop((x1, y1, x2, y2))
        callout = fit(crop, CALLOUT_W, CALLOUT_H)
        callout = red_border(callout)
        callout = add_label(callout, "Issue detail")
        total_w = THUMB_W + GAP + THUMB_W + GAP + CALLOUT_W
        total_h = max(figma.height, staging.height, callout.height)
        canvas = Image.new("RGB", (total_w, total_h), (255, 255, 255))
        canvas.paste(figma, (0, 0))
        canvas.paste(staging, (THUMB_W + GAP, 0))
        canvas.paste(callout, (THUMB_W * 2 + GAP * 2, 0))
    else:
        total_w = THUMB_W + GAP + THUMB_W
        total_h = max(figma.height, staging.height)
        canvas = Image.new("RGB", (total_w, total_h), (255, 255, 255))
        canvas.paste(figma, (0, 0))
        canvas.paste(staging, (THUMB_W + GAP, 0))

    canvas.save(args.output)
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
