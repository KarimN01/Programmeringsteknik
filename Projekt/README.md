# Fjärilars utbredning i Sverige

Program som läser observationsdata exporterad från Artportalen
(semikolonseparerade CSV-filer) och skapar tre diagram per art:

- nordligaste observationen per år, med linjer för Ystad och Abisko
- antalet observationer per år
- andelen observationer per vecka för ett valt år (2022 som standard),
  med den period då 90 % av observationerna görs markerad

Diagrammen sparas som PDF (och som PNG med flaggan `--png`).

## Kör programmet

```bash
# en art
python butterfly_analysis.py --csv butterfly_data/amiral.csv --outdir plots

# alla filer i en katalog
python butterfly_analysis.py --csv butterfly_data --all --outdir plots
```

Flaggor:

| Flagga | Betydelse |
| --- | --- |
| `--csv` | CSV-fil eller katalog med CSV-filer (obligatorisk) |
| `--all` | analysera alla CSV-filer när `--csv` är en katalog |
| `--species` | art att analysera; utan flaggan används vanligaste arten |
| `--outdir` | katalog för diagrammen (standard: aktuell katalog) |
| `--year` | år för veckodiagrammet (standard: 2022) |
| `--png` | spara även PNG-versioner av diagrammen |

## Kör testerna

```bash
python -m unittest -v test_butterfly_analysis
```

## Filer

| Fil | Innehåll |
| --- | --- |
| `butterfly_analysis.py` | huvudprogram, klassen `ButterflyApplication` |
| `observations.py` | `Observation` och `ObservationReader` (inläsning) |
| `analysis.py` | `SpeciesAnalysis` (alla beräkningar) |
| `plotting.py` | `FigureWriter` (diagrammen) |
| `test_butterfly_analysis.py` | enhetstester |
| `butterfly_data/` | datafiler från Artportalen |
| `plots/` | genererade diagram |
| `report.pdf` | rapporten |

## Beroenden

Endast `matplotlib` utöver Pythons standardbibliotek (Pandas används
inte). Installeras med:

```bash
python -m pip install -r requirements.txt
```

Kräver Python 3.9 eller senare.
