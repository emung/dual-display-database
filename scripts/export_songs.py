#!/usr/bin/env python3
"""Export songs from a cantari-textele CSV to one .txt file per song.

Only rows with Stearsa == 0 (not deleted) are exported. The file name is the
song title (Titlu), the content is the song text (Textul). Raw mdb-export
input with cp1252 mojibake is repaired on the fly (see fix_diacritics.py), so
both cantari-textele.csv and cantari-textele.fixed.csv can be used.

Usage:
    python3 scripts/export_songs.py <input.csv> [--out output/cantari] [--dry-run] [--two-lines]

Titles that clash (also case-insensitively, as on macOS) get " (<CantareID>)"
appended. Characters not allowed in file names are replaced with "-".

Verses are separated by empty lines or "---" lines; each verse is written as
one slide, with one empty line between verses and the "---" lines removed.
A refrain that starts a verse block ("/: … :/", "//: … ://", "//; … ;//",
"R: …") is split off as its own block; a repetition inside a verse stays part
of it. Markers are kept in the text.

Every block gets a FreeShow group label: [Chorus] for a refrain or a block
that occurs more than once, otherwise [Verse N] (N from a leading "2." or
counted in order).

With --two-lines, every block is split into slides of two lines (an odd last
line becomes its own slide); the slides stay in the group of their label.
"""
import collections
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
VERSE_NUMBER = re.compile(r"^\s*(\d+)\s*[.)]")
# FreeShow's txt import moves everything after "---" in a slide to the notes
# and repeats a section for a line holding only "x2" (up to x9).
INLINE_DASHES = re.compile(r"-{3,}")
REPEAT_LINE = re.compile(r"^\s*[xXхХ]\s*\d\s*$")
LINES_PER_SLIDE = 2


def blocks(text):
    """Split text into blocks of non-empty lines at empty lines and separators."""
    block = []
    for line in text.splitlines() + [""]:
        if REPEAT_LINE.match(line):
            continue
        if line.strip() and not SEPARATOR.match(line):
            block.append(INLINE_DASHES.sub("—", line.rstrip()))
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


def is_refrain(segment):
    first = segment[0]
    return bool(LABEL_START.match(first) or (SLASH_START.match(first) and not SLASH_END.search(first)))


def normalized(segment):
    return " ".join(" ".join(segment).lower().split())


def slides(text, two_lines=False):
    """Return the labelled blocks with an empty line between blocks, or with
    two_lines after every two lines of a block."""
    segs = [segment for block in blocks(text) for segment in segments(block)]
    counts = collections.Counter(normalized(segment) for segment in segs)
    out = []
    verse = 0
    for segment in segs:
        if is_refrain(segment) or counts[normalized(segment)] > 1:
            label = "[Chorus]"
        else:
            number = VERSE_NUMBER.match(segment[0])
            verse = int(number.group(1)) if number else verse + 1
            label = f"[Verse {verse}]"
        size = LINES_PER_SLIDE if two_lines else len(segment)
        parts = ["\n".join(segment[i:i + size]) for i in range(0, len(segment), size)]
        # An empty line after the label would make FreeShow create an empty group.
        out.append(label + "\n" + "\n\n".join(parts))
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


def export(rows, out_dir, dry_run, two_lines):
    songs = [r for r in rows if r["Stearsa"].strip() == "0"]
    taken = set()
    for row in songs:
        stem = file_stem(row["Titlu"])
        if stem.lower() in taken:
            stem = f"{stem} ({row['CantareID']})"
        taken.add(stem.lower())

        content = slides(row["Textul"], two_lines)
        if not dry_run:
            (out_dir / f"{stem}.txt").write_text(content, encoding="utf-8")
    print(f"{'DRY ' if dry_run else ''}exported {len(songs)} of {len(rows)} rows -> {out_dir}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output folder (default: {DEFAULT_OUT.relative_to(REPO_ROOT)})")
    parser.add_argument("--dry-run", action="store_true", help="print statistics only, write nothing")
    parser.add_argument("--two-lines", action="store_true", help="split verses into 2-line slides, refrains as own blocks")
    args = parser.parse_args()

    rows = load_rows(args.input)
    missing = {"CantareID", "Titlu", "Textul", "Stearsa"} - set(rows[0] if rows else {})
    if missing:
        sys.exit(f"{args.input.name}: missing columns {sorted(missing)}")

    if not args.dry_run:
        args.out.mkdir(parents=True, exist_ok=True)
    export(rows, args.out, args.dry_run, args.two_lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
