"""
Checks that the QR inside output/hero.png still scans and points where it should.

The QR is artistic and fragile when small, so this decodes it at full
size and again shrunk and blurred, roughly what a phone camera sees when
scanning another phone's screen.

Usage:
    python scripts/verify_qr.py
"""
import sys
from pathlib import Path

import zxingcpp
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
HERO = ROOT / "output" / "hero.png"
EXPECTED = "https://www.linkedin.com/in/veertej-sehdave/"

# (scale, blur radius): full size, then progressively harsher conditions
CASES = [(1.0, 0), (1.0, 1), (0.75, 1)]


def decode(img: Image.Image) -> list[str]:
    return [r.text for r in zxingcpp.read_barcodes(img)]


def main() -> int:
    hero = Image.open(HERO).convert("RGB")
    failed = False
    for scale, blur in CASES:
        img = hero.resize((round(hero.width * scale), round(hero.height * scale)), Image.LANCZOS)
        if blur:
            img = img.filter(ImageFilter.GaussianBlur(blur))
        texts = decode(img)
        ok = EXPECTED in texts
        failed |= not ok
        print(f"{'PASS' if ok else 'FAIL'}  scale={scale:<4} blur={blur}  -> {texts or 'no QR found'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
