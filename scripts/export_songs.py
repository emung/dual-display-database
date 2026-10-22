#!/usr/bin/env python3
"""Export songs from a cantari-textele CSV to one .txt file per song.

Only rows with Stearsa == 0 (not deleted) are exported. The file name is the
song title (Titlu), the content is the song text (Textul). Raw mdb-export
input with cp1252 mojibake is repaired on the fly (see fix_diacritics.py), so
both cantari-textele.csv and cantari-textele.fixed.csv can be used.

Usage:
    python3 scripts/export_songs.py <input.csv> [--out output/cantari] [--dry-run]

Titles that clash (also case-insensitively, as on macOS) get " (<CantareID>)"
appended. Characters not allowed in file names are replaced with "-".
Lines that only hold a verse separator ("---") are emptied, not removed.
"""
import argparse
import csv
import io
import re
import sys
from pathlib import Path

from fix_diacritics import MOJIBAKE, SOFT_HYPHEN, repair

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "output" / "cantari"
INVALID_CHARS = re.compile(r'[/\\:*?"<>|\x00-\x1f]')
# Verse separators ("---", "----", "---.") become empty lines so FreeShow
# splits the verses into slides.
SEPARATOR = re.compile(r"^[ \t\xa0]*-{3,}\.?[ \t\xa0]*$", re.MULTILINE)


def load_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    if any(c in MOJIBAKE for c in text):
        fixed = repair(text)
        if fixed is None:
            sys.exit(f"{path.name}: contains mojibake but cannot be repaired")
        print(f"{path.name}: repaired cp1252 mojibake")
        text = fixed
    text = text.replace(SOFT_HYPHEN, "")
    return list(csv.DictReader(io.StringIO(text, newline="")))


def file_stem(title):
    stem = INVALID_CHARS.sub("-", title.replace("\xa0", " "))
    stem = re.sub(r"\s+", " ", stem).strip(" .")
    return stem or "untitled"


def export(rows, out_dir, dry_run):
    songs = [r for r in rows if r["Stearsa"].strip() == "0"]
    taken = set()
    for row in songs:
        stem = file_stem(row["Titlu"])
        if stem.lower() in taken:
            stem = f"{stem} ({row['CantareID']})"
        taken.add(stem.lower())

        content = row["Textul"].replace("\r\n", "\n").replace("\r", "\n")
        content = SEPARATOR.sub("", content)
        if not dry_run:
            (out_dir / f"{stem}.txt").write_text(content, encoding="utf-8")
    print(f"{'DRY ' if dry_run else ''}exported {len(songs)} of {len(rows)} rows -> {out_dir}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output folder (default: {DEFAULT_OUT.relative_to(REPO_ROOT)})")
    parser.add_argument("--dry-run", action="store_true", help="print statistics only, write nothing")
    args = parser.parse_args()

    rows = load_rows(args.input)
    missing = {"CantareID", "Titlu", "Textul", "Stearsa"} - set(rows[0] if rows else {})
    if missing:
        sys.exit(f"{args.input.name}: missing columns {sorted(missing)}")

    if not args.dry_run:
        args.out.mkdir(parents=True, exist_ok=True)
    export(rows, args.out, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
