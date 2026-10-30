"""
Generates an "Add to Google Wallet" link for the pass.

The link carries a signed JWT that contains the whole pass definition, so no
API calls are made: Google reads the pass from the token when you tap Save.

Config comes from .env (see .env.example):
    WALLET_ISSUER_ID                 issuer ID from the Google Pay & Wallet console
    GOOGLE_APPLICATION_CREDENTIALS   path to the service account JSON key
    HERO_URL                         public URL of output/hero.png

Usage:
    python scripts/create_pass.py
"""
import json
import os
import sys
from pathlib import Path

import jwt
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

NAME = "Veertej Sehdave"
BG_HEX = "#1A76E8"
CLASS_SUFFIX = "personal_qr_card"
OBJECT_SUFFIX = "veertej_sehdave_v3"   # bump to issue a fresh pass; Wallet caches by ID

# Google requires a cardTitle (the small top-row text). A non-breaking space
# keeps that row empty so the name in the header is the first thing you see.
CARD_TITLE = " "


def env(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        sys.exit(f"Missing {key}. Copy .env.example to .env and fill it in.")
    return value


def lv(value: str) -> dict:
    return {"defaultValue": {"language": "en-US", "value": value}}


def build_pass(issuer_id: str, hero_url: str) -> tuple[dict, dict]:
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
            "contentDescription": lv("Contact details and a QR code to LinkedIn."),
        },
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
    key_path = ROOT / env("GOOGLE_APPLICATION_CREDENTIALS")
    cls, obj = build_pass(env("WALLET_ISSUER_ID"), env("HERO_URL"))
    print(save_link(key_path, cls, obj))


if __name__ == "__main__":
    main()
