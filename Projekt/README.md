# Fjärilsutbredning — E-level analysis

This small tool produces the three required figures for the course project:

- Northernmost observation per year
- Number of observations per year
- Weekly observation distribution for 2022 (90% activity period highlighted)

Usage (example):

```bash
python butterfly_analysis.py --csv path/to/fjarilsdata.csv --species "Grönsnabbvinge"
```

If `--species` is omitted the script will pick the most common species found in the CSV.

The CSV must be exported from Artportalen (UTF-8 CSV with semicolon delimiter). The script uses only the `csv` module to read data (no pandas).

Dependencies: see `requirements.txt`.
