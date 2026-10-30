"""
Generates an "Add to Google Wallet" link for the pass.

The link carries a signed JWT that contains the whole pass definition, so no
API calls are made: Google reads the pass from the token when you tap Save.

Config comes from .env (see .env.example):
    WALLET_ISSUER_ID                 issuer ID from the Google Pay & Wallet console
    GOOGLE_APPLICATION_CREDENTIALS   path to the service account JSON key
    HERO_URL                         public URL of output/hero.png

Usage:
    python scripts/create_pass.py                 # print the link
    python scripts/create_pass.py --out link.txt  # also save it to a file
    python scripts/create_pass.py --barcode       # add Google's plain QR as a fallback
"""
import argparse
import json
import os
import sys
from pathlib import Path

import jwt
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

NAME = "Veertej Sehdave"
LINKEDIN_URL = "https://www.linkedin.com/in/veertej-sehdave/"
GITHUB_URL = "https://github.com/VS3hdav3"
EMAIL = "vssehdave@uwaterloo.ca"
PHONE_E164 = "+15485773771"
PHONE_DISPLAY = "+1 (548)-577-3771"
BG_HEX = "#1A76E8"
CLASS_SUFFIX = "personal_qr_card"
OBJECT_SUFFIX = "veertej_sehdave_v3"   # bump to issue a fresh pass; Wallet caches by ID

# Google requires a non-empty cardTitle (the small top-row text above the
# name). Blank or whitespace-only values are rejected as an empty LocalizedString.
CARD_TITLE = "Digital Business Card"


def env(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        sys.exit(f"Missing {key}. Copy .env.example to .env and fill it in.")
    return value


def lv(value: str) -> dict:
    return {"defaultValue": {"language": "en-US", "value": value}}


def build_pass(issuer_id: str, hero_url: str, barcode: bool = False) -> tuple[dict, dict]:
    generic_class = {"id": f"{issuer_id}.{CLASS_SUFFIX}"}
    generic_object = {
        "id": f"{issuer_id}.{OBJECT_SUFFIX}",
        "classId": generic_class["id"],
        "state": "ACTIVE",
        "hexBackgroundColor": BG_HEX,
        "cardTitle": lv(CARD_TITLE),
        "header": lv(NAME),
        "heroImage": {
            "sourceUri": {"uri": hero_url},
            "contentDescription": lv(
                "Analytics Engineer Intern @ Ratehub.ca, Statistics @ UWaterloo '28. "
                f"{EMAIL}, {PHONE_DISPLAY}, github.com/VS3hdav3. QR code to LinkedIn."
            ),
        },
        # Text in the hero image isn't tappable, so the same details go on
        # the back of the pass as real links.
        "linksModuleData": {
            "uris": [
                {"id": "email", "uri": f"mailto:{EMAIL}", "description": EMAIL},
                {"id": "phone", "uri": f"tel:{PHONE_E164}", "description": PHONE_DISPLAY},
                {"id": "github", "uri": GITHUB_URL, "description": "GitHub"},
                {"id": "linkedin", "uri": LINKEDIN_URL, "description": "LinkedIn"},
            ]
        },
    }
    if barcode:
        # Google renders this as a standard black QR above the hero image.
        # Easier to scan than the artistic QR, but it sits between the name and the art.
        generic_object["barcode"] = {
            "type": "QR_CODE",
            "value": LINKEDIN_URL,
            "alternateText": "Yes. It’s a QR.",
        }
    return generic_class, generic_object


def save_link(key_path: Path, generic_class: dict, generic_object: dict) -> str:
    sa = json.loads(key_path.read_text())
    claims = {
        "iss": sa["client_email"],
        "aud": "google",
        "typ": "savetowallet",
        "origins": [],
        "payload": {"genericClasses": [generic_class], "genericObjects": [generic_object]},
    }
    token = jwt.encode(claims, sa["private_key"], algorithm="RS256")
    return f"https://pay.google.com/gp/v/save/{token}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an Add to Google Wallet link.")
    parser.add_argument("--out", type=Path, help="also write the link to this file (gitignored)")
    parser.add_argument("--barcode", action="store_true", help="add Google's standard QR as a fallback")
    args = parser.parse_args()

    key_path = ROOT / env("GOOGLE_APPLICATION_CREDENTIALS")
    cls, obj = build_pass(env("WALLET_ISSUER_ID"), env("HERO_URL"), barcode=args.barcode)
    link = save_link(key_path, cls, obj)
    print(link)
    if args.out:
        args.out.write_text(link + "\n")


if __name__ == "__main__":
    main()
