# Project memories

- Text in `Baza.mdb` is Windows-1250 (the app uses `FontCharSet=238`). CSV exports decoded as Windows-1252 show mojibake: `ã→ă`, `º→ș`, `ª→Ș`, `þ→ț`, `Þ→Ț` (`â î Î „ ”` are unaffected). Diacritics are not missing.
- `scripts/fix_diacritics.py` repairs this (`encode cp1252 → decode cp1250`, then cedilla ş/ţ → comma-below ș/ț). It writes `<name>.fixed.csv` in UTF-8, skips files that are already fixed, and `--check` detects leftover mojibake.
- The target is a new UTF-8 app. The legacy Delphi app (Tahoma, charset 238) cannot render comma-below ș/ț, so do not write the fixed text back into `Baza.mdb`.
- `Baza.mdb` is JET4: the mojibake is stored in the DB itself (`MDB_JET3_CHARSET` has no effect), so every `mdb-export` must be followed by `scripts/fix_diacritics.py`.
