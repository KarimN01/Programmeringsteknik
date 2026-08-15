"""Ritar och sparar diagrammen för en art.

Klassen ``FigureWriter`` innehåller all kod som använder matplotlib och
skriver filer. Beräkningarna görs av ``analysis.SpeciesAnalysis``, så
den här modulen tar emot färdiga tal och ansvarar bara för hur de
presenteras.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

# Diagrammen sparas till fil och visas aldrig på skärmen. Agg är en
# ritmotor som inte kräver något fönstersystem, vilket gör att
# programmet fungerar likadant t.ex. på en server utan skärm.
matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402  (måste komma efter use)
from matplotlib.ticker import MaxNLocator  # noqa: E402

from analysis import ABISKO_NORTHING, YSTAD_NORTHING  # noqa: E402


class FigureWriter:
    """Skapar och sparar diagram för en art i en given katalog.

    Varje metod returnerar sökvägarna till de filer som skrevs, så att
    anroparen kan tala om för användaren var diagrammen hamnade.
    """

    # Uppgiften kräver PDF; PNG kan skrivas vid sidan av för den som
    # vill infoga figurerna i en rapport.
    PDF_SUFFIX = '.pdf'
    PNG_SUFFIX = '.png'
    PNG_DPI = 150

    def __init__(self, outdir: Path, species: str,
                 write_png: bool = False):
        """Ange var diagrammen sparas och vilken art de gäller."""
        self.outdir = Path(outdir)
        self.species = species
        self.write_png = write_png

    def _save(self, figure, name: str) -> list[Path]:
        """Spara en figur som PDF (och eventuellt PNG) och stäng den.

        Filnamnet byggs av artnamnet och ``name``, så att det går att se
        vad varje fil innehåller.
        """
        stem = f"{self.species.replace(' ', '_')}_{name}"
        written = []
        figure.tight_layout()
        pdf_path = self.outdir / (stem + self.PDF_SUFFIX)
        figure.savefig(pdf_path)
        written.append(pdf_path)
        if self.write_png:
            png_path = self.outdir / (stem + self.PNG_SUFFIX)
            figure.savefig(png_path, dpi=self.PNG_DPI)
            written.append(png_path)
        plt.close(figure)
        return written

    def plot_northernmost(self, northernmost: dict[int, float]) -> list[Path]:
        """Rita nordligaste observationen per år.

        Referenslinjer för Ystad och Abisko ritas ut så att man ser var
        i landet observationerna ligger.
        """
        years = sorted(northernmost)
        values = [northernmost[year] for year in years]
        figure, axes = plt.subplots()
        axes.plot(years, values, marker='o')
        axes.axhline(YSTAD_NORTHING, color='gray', linestyle='--',
                     label='Ystad')
        axes.axhline(ABISKO_NORTHING, color='gray', linestyle=':',
                     label='Abisko')
        axes.set_xlabel('År')
        axes.set_ylabel('Nordkoordinat (RT 90, meter)')
        axes.set_title(f'{self.species}: nordligaste observationen')
        axes.xaxis.set_major_locator(MaxNLocator(integer=True))
        axes.legend()
        return self._save(figure, 'northernmost_per_year')

    def plot_observations_per_year(self,
                                   counts: dict[int, int]) -> list[Path]:
        """Rita antalet observationer per år som ett stapeldiagram."""
        years = sorted(counts)
        figure, axes = plt.subplots()
        axes.bar(years, [counts[year] for year in years])
        axes.set_xlabel('År')
        axes.set_ylabel('Antal observationer')
        axes.set_title(f'{self.species}: observationer per år')
        axes.xaxis.set_major_locator(MaxNLocator(integer=True))
        return self._save(figure, 'observations_per_year')

    def plot_weekly(self, proportions: list[float], year: int,
                    period: tuple[int, int] | None) -> list[Path]:
        """Rita andelen observationer per vecka för ett år.

        Veckorna i ``period``, alltså de veckor då 90 % av
        observationerna görs, markeras med kraftigare färg och skrivs
        också ut i klartext i diagrammet.
        """
        weeks = list(range(1, len(proportions) + 1))
        figure, axes = plt.subplots(figsize=(10, 4))
        bars = axes.bar(weeks, proportions, color='lightgray')
        axes.set_xlabel('Veckonummer')
        axes.set_ylabel('Andel av årets observationer')
        axes.set_title(f'{self.species}: observationer per vecka {year}')
        if period is not None:
            first_week, last_week = period
            for week in range(first_week, last_week + 1):
                bars[week - 1].set_color('C0')
            axes.annotate(
                f'90 % av observationerna: vecka {first_week}–{last_week}',
                xy=(0.99, 0.95), xycoords='axes fraction', ha='right')
        else:
            axes.annotate(f'Inga observationer {year}', xy=(0.5, 0.5),
                          xycoords='axes fraction', ha='center')
        return self._save(figure, f'weekly_{year}')
