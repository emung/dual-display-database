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

Every verse is split into slides of two lines (an empty line between slides,
an odd last line becomes its own slide). Verses are separated by empty lines
or "---" lines. A refrain that starts a verse block ("/: … :/", "//: … ://",
"//; … ;//", "R: …") is split off as its own block; a repetition inside a
verse stays part of it. Markers are kept in the text.
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
# Verse separators ("---", "----", "---.") end a block like an empty line.
SEPARATOR = re.compile(r"^[ \t\xa0]*-{3,}\.?[ \t\xa0]*$")
# Refrain markers at the start of a block: "/: … :/" (also "//:", "//;",
# "/;") ends at the closing marker, "R: …" (also "Ref:", "Refren") ends with
# the block.
SLASH_START = re.compile(r"^\s*/{1,2}\s*[:;]")
LABEL_START = re.compile(r"^\s*(?:(?:r|ref|refren)\s*[:.]|refren\b)", re.IGNORECASE)
SLASH_END = re.compile(r"[:;]/")
LINES_PER_SLIDE = 2


def blocks(text):
    """Split text into blocks of non-empty lines at empty lines and separators."""
    block = []
    for line in text.splitlines() + [""]:
        if line.strip() and not SEPARATOR.match(line):
            block.append(line.rstrip())
        elif block:
            yield block
            block = []


def segments(block):
    """Split a refrain at the start of a block off the verse lines after it.

    A repetition that does not start the block, or that opens and closes on
    the first line ("/: … :/ 3x"), stays part of the verse.
    """
    if LABEL_START.match(block[0]):
        return [block]
    if SLASH_START.match(block[0]) and not SLASH_END.search(block[0]):
        for i, line in enumerate(block):
            if SLASH_END.search(line):
                rest = block[i + 1:]
                return [block[:i + 1]] + (segments(rest) if rest else [])
    return [block]


def slides(text):
    """Return the text with an empty line after every two lines of a block."""
    out = []
    for block in blocks(text):
        for segment in segments(block):
            for i in range(0, len(segment), LINES_PER_SLIDE):
                out.append("\n".join(segment[i:i + LINES_PER_SLIDE]))
    return "\n\n".join(out) + "\n" if out else ""


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

        content = slides(row["Textul"])
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
