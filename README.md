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
