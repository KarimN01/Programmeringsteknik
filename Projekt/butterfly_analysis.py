#!/usr/bin/env python3
"""Generate E-level analysis for Artportalen butterfly CSV exports.

Usage: python butterfly_analysis.py --csv PATH [--species NAME]

Produces three PDF figures (saved in the current directory):
- {species}_northernmost_per_year.pdf
- {species}_observations_per_year.pdf
- {species}_weekly_2022.pdf

The script uses only the Python stdlib plus matplotlib and numpy.
"""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
import math
import sys

import numpy as np
import matplotlib.pyplot as plt


def parse_args():
    p = argparse.ArgumentParser(description='Butterfly distribution plots (E-level)')
    p.add_argument('--csv', required=True, help='Path to semicolon-separated CSV from Artportalen, or a directory containing CSVs')
    p.add_argument('--species', required=False, help='Species name to analyse (Artnamn). If omitted, the most common species is used')
    p.add_argument('--outdir', required=False, help='Directory to write PDF plots to (default: current directory)')
    p.add_argument('--all', dest='all_files', action='store_true', help='If set and --csv is a directory, process all CSV files inside')
    return p.parse_args()


def normalize_header(h: str) -> str:
    return h.strip().lower()


def read_records(csv_path: Path):
    records = []
    with csv_path.open(encoding='utf-8', newline='') as fh:
        # Artportalen CSV uses semicolon separation
        reader = csv.DictReader(fh, delimiter=';')
        # normalize keys
        fieldmap = {normalize_header(k): k for k in reader.fieldnames or []}
        for i, row in enumerate(reader, start=1):
            try:
                # pull raw values using normalized names
                get = lambda name: row.get(fieldmap.get(name, ''), '').strip()
                art = get('artnamn')
                antal = get('antal')
                nord = get('nord')
                slut = get('slutdatum')
                records.append({'art': art, 'antal': antal, 'nord': nord, 'slut': slut})
            except Exception as e:
                print(f'Warning: failed to parse row {i}: {e}', file=sys.stderr)
                continue
    return records


def safe_int(x):
    try:
        return int(float(x))
    except Exception:
        return 1


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def parse_date(s: str):
    if not s:
        return None
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(s.split()[0], '%Y-%m-%d').date()
        except Exception:
            pass
    try:
        # try fromisoformat
        return datetime.fromisoformat(s).date()
    except Exception:
        return None


def analyse(records, species, outdir: Path):
    species_records = [r for r in records if r['art'] == species]
    if not species_records:
        raise SystemExit(f'No records for species: {species}')

    # northernmost per year
    north_by_year = defaultdict(lambda: -math.inf)
    counts_by_year = defaultdict(int)
    weekly_2022 = Counter()
    total_2022 = 0

    for r in species_records:
        nord = safe_float(r['nord'])
        antal = safe_int(r['antal'])
        slut = parse_date(r['slut'])
        # use Slutdatum for year/week
        year = slut.year if slut else None
        if nord is not None and year is not None:
            # store north as meters (RT90); later scale for plotting
            if nord > north_by_year[year]:
                north_by_year[year] = nord
        if year is not None:
            counts_by_year[year] += 1
        if slut and slut.year == 2022:
            week = int(slut.isocalendar()[1])
            weekly_2022[week] += 1
            total_2022 += 1

    # Prepare northernmost per year plot
    years = sorted(north_by_year.keys())
    if years:
        north_vals = [north_by_year[y] / 1e6 for y in years]  # scale to millions as in spec
        plt.figure()
        plt.plot(years, north_vals, marker='o')
        plt.xlabel('År')
        plt.ylabel('Latitude (RT90 / 1e6)')
        # Add horizontal lines for Ystad and Abisko (approx)
        ystad = 6164000 / 1e6
        abisko = 7585000 / 1e6
        plt.axhline(ystad, color='gray', linestyle='--', label='Ystad')
        plt.axhline(abisko, color='gray', linestyle=':', label='Abisko')
        plt.legend()
        plt.title(f'Northernmost observation per year — {species}')
        out = outdir / f"{species.replace(' ', '_')}_northernmost_per_year.pdf"
        png_out = outdir / f"{species.replace(' ', '_')}_northernmost_per_year.png"
        plt.tight_layout()
        plt.savefig(out)
        plt.savefig(png_out, dpi=150)
        plt.close()
        print(f'Wrote {out}')

    # observations per year
    years2 = sorted(counts_by_year.keys())
    if years2:
        counts = [counts_by_year[y] for y in years2]
        plt.figure()
        plt.bar(years2, counts)
        plt.xlabel('År')
        plt.ylabel('Antal')
        plt.title(f'Observations per year — {species}')
        out = outdir / f"{species.replace(' ', '_')}_observations_per_year.pdf"
        png_out = outdir / f"{species.replace(' ', '_')}_observations_per_year.png"
        plt.tight_layout()
        plt.savefig(out)
        plt.savefig(png_out, dpi=150)
        plt.close()
        print(f'Wrote {out}')

    # weekly distribution for 2022
    weeks = list(range(1, 54))
    freqs = [weekly_2022[w] / total_2022 if total_2022 > 0 else 0 for w in weeks]
    plt.figure(figsize=(10, 4))
    bars = plt.bar(weeks, freqs)
    plt.xlabel('Week number')
    plt.ylabel('Proportion of 2022 observations')
    plt.title(f'Weekly observations 2022 — {species}')

    # compute 5% and 95% percentiles over cumulative distribution
    if total_2022 > 0:
        cum = np.cumsum(freqs)
        lower_week = next((w for w, c in zip(weeks, cum) if c >= 0.05), 1)
        upper_week = next((w for w, c in zip(weeks, cum) if c >= 0.95), weeks[-1])
        for w in weeks:
            if lower_week <= w <= upper_week:
                bars[w - 1].set_color('C0')
            else:
                bars[w - 1].set_color('lightgray')
        plt.annotate(f'90% period: week {lower_week}–{upper_week}', xy=(0.99, 0.95), xycoords='axes fraction', ha='right')

    out = outdir / f"{species.replace(' ', '_')}_weekly_2022.pdf"
    png_out = outdir / f"{species.replace(' ', '_')}_weekly_2022.png"
    plt.tight_layout()
    plt.savefig(out)
    plt.savefig(png_out, dpi=150)
    plt.close()
    print(f'Wrote {out}')


def main():
    args = parse_args()
    csv_path = Path(args.csv)
    outdir = Path(args.outdir) if args.outdir else Path.cwd()
    outdir.mkdir(parents=True, exist_ok=True)

    def process_file(path: Path):
        records = read_records(path)
        if not records:
            print(f'No records read from {path}; skipping')
            return
        species = args.species
        if not species:
            c = Counter(r['art'] for r in records if r['art'])
            if not c:
                print(f'No species names found in {path}; skipping')
                return
            species_local = c.most_common(1)[0][0]
            print(f'File {path.name}: no species given — using most common: {species_local}')
            species = species_local
        # create subfolder per input file to avoid name clashes
        file_outdir = outdir
        analyse(records, species, file_outdir)

    if csv_path.is_dir():
        if not args.all_files:
            raise SystemExit(f'{csv_path} is a directory — use --all to process all CSVs inside')
        for f in sorted(csv_path.glob('*.csv')):
            process_file(f)
    else:
        if not csv_path.exists():
            raise SystemExit(f'CSV file not found: {csv_path}')
        process_file(csv_path)


if __name__ == '__main__':
    main()
