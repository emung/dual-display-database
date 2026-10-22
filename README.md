# dual-display-database

## Fixing Romanian diacritics in CSV exports

`Baza.mdb` stores text as Windows-1250, but the CSV exports were decoded as
Windows-1252, so diacritics appear as `ã º ª þ Þ` instead of `ă ș Ș ț Ț`.

```bash
python3 scripts/fix_diacritics.py --dry-run   # show what would change
python3 scripts/fix_diacritics.py             # write <name>.fixed.csv (UTF-8, ș/ț comma-below)
python3 scripts/fix_diacritics.py --check     # exit 1 if any *.fixed.csv still has mojibake
```

Pass file names to process specific files. Already-fixed files are skipped.

Re-export tables with `mdb-export Baza.mdb <Table> > <table>.csv`, then run the script.
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
- Verse separator lines (`---`, `----`, `---.`) become empty lines, so FreeShow splits verses into slides.
- Characters not allowed in file names (`/ : ? * " < > |`) are replaced with `-`.
- Duplicate titles (also differing only in case) get the song ID appended, e.g. `Aleluia (3).txt`.
