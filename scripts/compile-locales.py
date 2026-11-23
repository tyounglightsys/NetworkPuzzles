#!/usr/bin/env python3
"""Compile gettext .po files to .mo files (cross-platform; no GNU gettext needed)."""
import sys
from pathlib import Path

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

LOCALE_DIR = Path(__file__).resolve().parents[1] / "src/network_puzzles/resources/locale"
DOMAIN = "networkpuzzles"

errors = 0
for po_path in sorted(LOCALE_DIR.glob("*.po")):
    lang = po_path.stem
    with po_path.open("rb") as f:
        catalog = read_po(f, locale=lang)
    for message, errs in catalog.check():  # like `msgfmt -c`
        for err in errs:
            errors += 1
            print(f"{po_path.name}:{message.lineno}: {err}", file=sys.stderr)
    mo_path = LOCALE_DIR / lang / "LC_MESSAGES" / f"{DOMAIN}.mo"
    mo_path.parent.mkdir(parents=True, exist_ok=True)
    with mo_path.open("wb") as f:
        write_mo(f, catalog)
    print(f"{po_path.name} -> {mo_path.relative_to(LOCALE_DIR)}")
sys.exit(1 if errors else 0)
