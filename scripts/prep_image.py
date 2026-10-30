"""
Crops and compresses a photo so it's ready to upload to WOW QR's image editor.

Output is a square matching the source QR image (1176x1176 px), saved as an
optimized PNG plus a high-quality JPEG; use whichever is smaller.

Usage:
    python scripts/prep_image.py photo.jpg
    python scripts/prep_image.py photo.jpg --focus 0.5 0.3   # crop centre as x y fractions
    python scripts/prep_image.py photo.jpg --size 1500 --quality 92
"""
import argparse
from pathlib import Path

from PIL import Image, ImageOps

SIZE = 1176   # same as the source QR image


def square_crop(img: Image.Image, fx: float, fy: float) -> Image.Image:
    side = min(img.size)
    cx, cy = img.width * fx, img.height * fy
    left = int(min(max(cx - side / 2, 0), img.width - side))
    top = int(min(max(cy - side / 2, 0), img.height - side))
    return img.crop((left, top, left + side, top + side))


def main() -> None:
    p = argparse.ArgumentParser(description="Square-crop and compress an image for WOW QR.")
    p.add_argument("image", type=Path)
    p.add_argument("--focus", nargs=2, type=float, default=(0.5, 0.5), metavar=("X", "Y"),
                   help="where to centre the crop, as fractions of width/height (default: centre)")
    p.add_argument("--size", type=int, default=SIZE, help=f"output side length in px (default {SIZE})")
    p.add_argument("--quality", type=int, default=90, help="JPEG quality (default 90)")
    p.add_argument("--outdir", type=Path, default=Path("output/prepped"))
    a = p.parse_args()

    img = ImageOps.exif_transpose(Image.open(a.image)).convert("RGB")   # respect phone rotation
    sq = square_crop(img, *a.focus)
    if sq.width > a.size:   # never upscale; upscaling adds no detail
        sq = sq.resize((a.size, a.size), Image.LANCZOS)

    a.outdir.mkdir(parents=True, exist_ok=True)
    stem = a.outdir / f"{a.image.stem}-square"
    sq.save(stem.with_suffix(".png"), optimize=True)
    sq.save(stem.with_suffix(".jpg"), quality=a.quality, optimize=True, progressive=True, subsampling=0)

    src_kb = a.image.stat().st_size / 1024
    for f in (stem.with_suffix(".png"), stem.with_suffix(".jpg")):
        print(f"{f}  {sq.width}x{sq.height}  {f.stat().st_size / 1024:.0f} KB  (source {src_kb:.0f} KB)")


if __name__ == "__main__":
    main()
