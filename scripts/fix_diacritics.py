#!/usr/bin/env python3
"""Repair Romanian diacritics in CSV exports of Baza.mdb.

Baza.mdb stores text as Windows-1250, but the CSV export decoded it as
Windows-1252, producing mojibake (ã->ă, º->ș, ª->Ș, þ->ț, Þ->Ț). This script
reverses that and normalizes cedilla ş/ţ to the correct comma-below ș/ț.

Usage:
    python3 scripts/fix_diacritics.py [--dry-run] [files...]
    python3 scripts/fix_diacritics.py --check [files...]

Without files, all *.csv in the repo root are processed (except *.fixed.csv
and video-files.csv). Output is written to <name>.fixed.csv next to the input.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP = {"video-files.csv"}

MOJIBAKE = set("ãºªþÞ")
COMMA_BELOW = str.maketrans("şŞţŢ", "șȘțȚ")
# Non-ASCII characters expected in correct Romanian text.
ALLOWED = set("ăâîșțĂÂÎȘȚ„”“«»–—…’")
# Typos in the source: "à" (cp1250 "ŕ") was typed instead of "ă"/"a".
TYPOS = {
    "ce-nseamnŕ": "ce-nseamnă",
    "aratatŕ": "arătată",
    "ŕ venit": "a venit",
}


def repair(text):
    """Return the repaired text, or None if it is not cp1252-mojibake."""
    try:
        fixed = text.encode("cp1252").decode("cp1250").translate(COMMA_BELOW)
    except UnicodeError:
        return None
    for wrong, right in TYPOS.items():
        fixed = fixed.replace(wrong, right)
    return fixed


def default_files():
    return sorted(
        p for p in REPO_ROOT.glob("*.csv")
        if not p.name.endswith(".fixed.csv") and p.name not in SKIP
    )


def check(paths):
    ok = True
    for path in paths:
        text = path.read_text(encoding="utf-8-sig")
        bad = Counter(c for c in text if c in MOJIBAKE)
        if bad:
            ok = False
            print(f"FAIL {path.name}: mojibake {dict(bad)}")
        else:
            print(f"OK   {path.name}")
    return 0 if ok else 1


def fix(paths, dry_run):
    for path in paths:
        with open(path, encoding="utf-8-sig", newline="") as f:
            text = f.read()

        fixed = repair(text)
        if fixed is None:
            print(f"SKIP {path.name}: not cp1252-mojibake (already fixed?)")
            continue

        changes = Counter(
            f"{a}->{b}" for a, b in zip(text, fixed) if a != b
        )
        unexpected = Counter(
            c for c in fixed if ord(c) > 127 and c not in ALLOWED
        )
        print(f"{'DRY ' if dry_run else 'FIX '}{path.name}: {dict(changes.most_common()) or 'no changes'}")
        if unexpected:
            print(f"     WARNING unexpected characters: {dict(unexpected)}")

        if not dry_run:
            out = path.with_name(path.stem + ".fixed.csv")
            with open(out, "w", encoding="utf-8", newline="") as f:
                f.write(fixed)
            print(f"     -> {out.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="print statistics only, write nothing")
    parser.add_argument("--check", action="store_true", help="exit 1 if any file still contains mojibake")
    args = parser.parse_args()

    if args.check:
        paths = args.files or sorted(REPO_ROOT.glob("*.fixed.csv"))
        return check(paths)

    fix(args.files or default_files(), args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
