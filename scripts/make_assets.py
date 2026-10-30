"""
Builds output/hero.png, the image that fills the body of the Wallet pass,
and output/preview.png, a rough mock of the whole card front.

Layout, top to bottom: role lines, a gap, contact rows (icon + text),
then the QR with the "Yes. It's a QR." tagline beside it.

Usage:
    python scripts/make_assets.py
"""
from functools import lru_cache
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"

# ---------- content ----------
ROLE_LINES = [
    "Analytics Engineer Intern @ Ratehub.ca",
    "Statistics @ UWaterloo ’28",
]
CONTACTS = [
    ("mail", "vssehdave@uwaterloo.ca"),
    ("phone", "+1 (548)-577-3771"),
    ("github", "github.com/VS3hdav3"),
]
TAGLINE = ("Yes.", "It’s a QR.")
CARD_TITLE = "⋅.˳˳.⋅ॱ˙˙ॱ⋅.˳˳.⋅ॱ˙˙ॱ⋅.˳˳.⋅ॱ˙˙ॱ⋅"   # keep in sync with create_pass.py

# Inter has no glyph for some of the title's symbols, so the preview falls back
# to whichever of these system fonts is installed (Windows, then Linux).
FALLBACK_FONTS = ["seguisym.ttf", "Nirmala.ttc", "NotoSansDevanagari-Regular.ttf", "FreeSans.ttf"]

# ---------- style ----------
BLUE = (26, 118, 232)          # card background, matches hexBackgroundColor
WHITE = (255, 255, 255)
SOFT = (222, 235, 252)         # muted white for the contact rows

W, H = 1032, 812               # Google recommends a near-square hero, 1032 wide
PAD_X, PAD_BOTTOM = 40, 56
TOP_PAD = 6                    # role lines sit tight under the name above them
ROLE_GAP = 64                  # space between the education line and the email row
ICON, ROW = 26, 42


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(ASSETS / "fonts" / f"{name}.otf"), size)


def has_glyph(f: ImageFont.FreeTypeFont, ch: str) -> bool:
    return ord(ch) in _cmap(f.path)


@lru_cache(maxsize=None)
def _cmap(path: str) -> frozenset:
    return frozenset(TTFont(path, fontNumber=0).getBestCmap())


def draw_mixed(d: ImageDraw.ImageDraw, xy: tuple, text: str, primary: ImageFont.FreeTypeFont, fill) -> None:
    """Draws text left to right, switching to a fallback font per character."""
    fallbacks = []
    for name in FALLBACK_FONTS:
        try:
            fallbacks.append(ImageFont.truetype(name, primary.size))
        except OSError:
            pass
    x, y = xy
    for ch in text:
        f = next((c for c in [primary, *fallbacks] if has_glyph(c, ch)), primary)
        d.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += f.getlength(ch)


def icon(name: str, px: int) -> Image.Image:
    img = Image.open(ASSETS / "icons" / f"{name}.png").convert("RGBA")
    return img.resize((px, px), Image.LANCZOS)


def build_hero() -> Image.Image:
    hero = Image.new("RGBA", (W, H), BLUE + (255,))
    d = ImageDraw.Draw(hero)

    y = TOP_PAD
    role_font = font("Inter-Medium", 36)
    for line in ROLE_LINES:
        d.text((PAD_X, y), line, font=role_font, fill=WHITE)
        y += 50

    y += ROLE_GAP - 14
    contact_font = font("Inter-Regular", 24)
    for name, text in CONTACTS:
        hero.alpha_composite(icon(name, ICON), (PAD_X, y))
        d.text((PAD_X + ICON + 14, y + ICON / 2), text, font=contact_font, fill=SOFT, anchor="lm")
        y += ROW

    # QR fills whatever height is left. The source image keeps its own
    # white quiet zone, which matters for scanning at this size.
    y += 28
    size = H - PAD_BOTTOM - y
    qr = Image.open(ASSETS / "qr" / "qr.png").convert("RGB").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=18, fill=255)
    hero.paste(qr, (PAD_X, y), mask)

    tag_font = font("InterDisplay-Bold", 84)
    tx, mid = PAD_X + size + 48, y + size / 2
    d.text((tx, mid - 8), TAGLINE[0], font=tag_font, fill=WHITE, anchor="ls")
    d.text((tx, mid + 92), TAGLINE[1], font=tag_font, fill=WHITE, anchor="ls")

    return hero.convert("RGB")


def build_preview(hero: Image.Image, name: str = "Veertej Sehdave") -> Image.Image:
    """Approximates the card front. Wallet draws the name itself in its own
    font and size, so treat this as a layout check, not a pixel match."""
    top = 170                  # card-title row + the name in Wallet's header line
    front = Image.new("RGB", (W, top + H), BLUE)
    fd = ImageDraw.Draw(front)
    draw_mixed(fd, (PAD_X, 62), CARD_TITLE, font("Inter-Regular", 24), SOFT)
    fd.text((PAD_X, top - 14), name, font=font("Inter-SemiBold", 64), fill=WHITE, anchor="ls")
    front.paste(hero, (0, top))

    canvas = Image.new("RGB", (W + 80, top + H + 80), (242, 242, 242))
    mask = Image.new("L", front.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 1, top + H - 1), radius=40, fill=255)
    canvas.paste(front, (40, 40), mask)
    return canvas


if __name__ == "__main__":
    OUTPUT.mkdir(exist_ok=True)
    hero = build_hero()
    hero.save(OUTPUT / "hero.png")
    build_preview(hero).save(OUTPUT / "preview.png")
    print(f"wrote {OUTPUT / 'hero.png'} and {OUTPUT / 'preview.png'}")
