# dual-display-database

## Quick start

Export the songs from `Baza.mdb` as `.txt` files for FreeShow (run from the repo root, needs Python 3):

```bash
brew install mdbtools                                       # once
mdb-export Baza.mdb Cantari_Textele > cantari-textele.csv   # export the songs table
python3 scripts/fix_diacritics.py cantari-textele.csv       # repair diacritics -> cantari-textele.fixed.csv
python3 scripts/export_songs.py cantari-textele.fixed.csv   # write output/cantari/<Titlu>.txt
```

Then import the files from `output/cantari/` into FreeShow. The sections below explain each step.

## Exporting tables from Baza.mdb

The CSV exports are not part of the repo. Create them with [mdbtools](https://github.com/mdbtools/mdbtools)
(`brew install mdbtools`):

```bash
mdb-tables -1 Baza.mdb                                      # list all tables, one per line
mdb-schema -T Cantari_Textele Baza.mdb                      # show columns and types of a table
mdb-export Baza.mdb Cantari_Textele > cantari-textele.csv   # export one table to CSV
```

Table names are case-sensitive. The file names used by the scripts:

| Table | CSV file |
| --- | --- |
| `Biblia_Capitole` | `biblia-capitole.csv` |
| `Biblia_Carti` | `biblia-carti.csv` |
| `Biblia_Versete` | `biblia-versete.csv` |
| `Cantari_Textele` | `cantari-textele.csv` |
| `Cantari_Versuri` | `cantari-versuri.csv` |
| `CustomTextSettings` | `custom-text-settings.csv` |
| `Diacritice` | `diacritice.csv` |
| `Video_Files` | `video-files.csv` |

Every export contains broken diacritics, so run `fix_diacritics.py` on it afterwards (see below).

## Fixing Romanian diacritics in CSV exports

`Baza.mdb` stores text as Windows-1250, but the CSV exports were decoded as
Windows-1252, so diacritics appear as `ã º ª þ Þ` instead of `ă ș Ș ț Ț`.

```bash
python3 scripts/fix_diacritics.py --dry-run   # show what would change
python3 scripts/fix_diacritics.py             # write <name>.fixed.csv (UTF-8, ș/ț comma-below)
python3 scripts/fix_diacritics.py --check     # exit 1 if any *.fixed.csv still has mojibake
```

Pass file names to process specific files. Already-fixed files are skipped.

`Baza.mdb` is JET4 (Unicode), so the wrong characters are stored in the database itself;
`MDB_JET3_CHARSET` has no effect and the script is always needed.

## Exporting songs as .txt files (for FreeShow)

`scripts/export_songs.py` writes one UTF-8 `.txt` file per song from `cantari-textele` to
`output/cantari/` (git-ignored). Only rows with `Stearsa = 0` are exported; the file name is
`Titlu`, the content is `Textul`.

```bash
python3 scripts/export_songs.py cantari-textele.fixed.csv --dry-run    # count songs, write nothing
python3 scripts/export_songs.py cantari-textele.fixed.csv              # write output/cantari/*.txt
python3 scripts/export_songs.py cantari-textele.fixed.csv --out <dir>  # write to another folder
```

- The raw `cantari-textele.csv` works too: mojibake is repaired the same way as in `fix_diacritics.py`.
- Every verse is split into slides of two lines, separated by an empty line (FreeShow starts a new
  slide at each empty line). An odd last line becomes its own slide, e.g. 7 lines → 2 + 2 + 2 + 1.
- Verses are separated by empty lines or separator lines (`---`, `----`, `---.`); separators are removed.
- A refrain that starts a verse is split off as its own block, so the slide pairs restart after it:
  `/: … :/`, `//: … ://`, `//; … ;//` end at the closing marker; `R:`, `Ref:`, `Refren` run to the end
  of the verse. A repetition inside a verse (`/: … :/` after verse lines, or `/: x :/ 3x` on one line)
  stays part of the verse. Markers are kept in the text.
- Characters not allowed in file names (`/ : ? * " < > |`) are replaced with `-`.
- Duplicate titles (also differing only in case) get the song ID appended, e.g. `Aleluia (3).txt`.
