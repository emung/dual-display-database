# Project memories

- Text in `Baza.mdb` is Windows-1250 (the app uses `FontCharSet=238`). CSV exports decoded as Windows-1252 show mojibake: `ã→ă`, `º→ș`, `ª→Ș`, `þ→ț`, `Þ→Ț` (`â î Î „ ”` are unaffected). Diacritics are not missing.
- `scripts/fix_diacritics.py` repairs this (`encode cp1252 → decode cp1250`, then cedilla ş/ţ → comma-below ș/ț). It writes `<name>.fixed.csv` in UTF-8, skips files that are already fixed, and `--check` detects leftover mojibake.
- The target is a new UTF-8 app. The legacy Delphi app (Tahoma, charset 238) cannot render comma-below ș/ț, so do not write the fixed text back into `Baza.mdb`.
- `Baza.mdb` is JET4: the mojibake is stored in the DB itself (`MDB_JET3_CHARSET` has no effect), so every `mdb-export` must be followed by `scripts/fix_diacritics.py`.
- `scripts/export_songs.py <csv>` exports `cantari-textele` rows with `Stearsa = 0` to `output/cantari/<Titlu>.txt` (UTF-8) for import into FreeShow. It imports `repair()` from `fix_diacritics.py`, so raw exports work. `output/` is git-ignored.
- Slide rules in `export_songs.py` (decided with the user): verses split into 2-line slides, an odd last line is its own slide (7 → 2+2+2+1). A refrain counts only if a marker starts the block (`/:`, `//:`, `//;` end at `:/`, `://`, `;//`; `R:`/`Ref:` run to block end); a `/: … :/` after verse lines or on one line is a repetition and stays in the verse. Markers are kept.
- Never run export scripts against the real `cantari-textele*.csv` unless the user asks; test with a small `test.csv` or a synthetic CSV.
