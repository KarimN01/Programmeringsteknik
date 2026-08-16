#!/usr/bin/env python3
"""Huvudprogram för analys av fjärilars utbredning i Sverige.

Programmet läser observationsdata exporterad från Artportalen och
skapar tre diagram per art:

* nordligaste observationen per år,
* antalet observationer per år,
* andelen observationer per vecka för ett valt år (2022 som standard),
  med den period då 90 % av observationerna görs markerad.

Körs så här::

    python butterfly_analysis.py --csv butterfly_data/amiral.csv
    python butterfly_analysis.py --csv butterfly_data --all --outdir plots

Klassen ``ButterflyApplication`` sköter dialogen med användaren:
utskrifter, felmeddelanden och val av filer. Själva beräkningarna
ligger i ``analysis`` och diagrammen i ``plotting``.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analysis import SpeciesAnalysis
from observations import ObservationError, ObservationReader
from plotting import FigureWriter

# Uppgiften efterfrågar veckodiagrammet för 2022. Året går att ändra
# med flaggan --year för att kunna titta på andra år i samma data.
DEFAULT_WEEK_YEAR = 2022

# Hur många inläsningsproblem som skrivs ut per fil. Datafilerna har
# tiotusentals rader, och en fil med systematiska fel skulle annars
# fylla hela terminalen; resten sammanfattas med en räknare.
MAX_REPORTED_ISSUES = 10


class ButterflyApplication:
    """Kör analysen för en eller flera datafiler och rapporterar läget.

    Klassen samlar all användarinteraktion: den skriver ut vad som
    hittats, vilka problem som uppstått och var diagrammen sparats.
    """

    def __init__(self, outdir: Path, week_year: int = DEFAULT_WEEK_YEAR,
                 species: str | None = None, write_png: bool = False,
                 stream=sys.stdout, error_stream=sys.stderr):
        """Ställ in var diagram sparas och vart utskrifter går.

        Strömmarna går att byta ut, vilket testerna använder för
        att fånga utskrifterna i minnet.
        """
        self.outdir = Path(outdir)
        self.week_year = week_year
        self.species = species
        self.write_png = write_png
        self.stream = stream
        self.error_stream = error_stream
        self.reader = ObservationReader()

    def _say(self, message: str) -> None:
        """Skriv ett meddelande till användaren."""
        print(message, file=self.stream)

    def _warn(self, message: str) -> None:
        """Skriv ett felmeddelande utan att avbryta körningen."""
        print(message, file=self.error_stream)

    def run(self, csv_path: Path, process_all: bool = False) -> int:
        """Analysera en fil eller alla CSV-filer i en katalog.

        Returnerar antalet filer som kunde analyseras. En fil som inte
        går att läsa ger ett felmeddelande, men körningen fortsätter
        med nästa fil.
        """
        paths = self._collect_paths(csv_path, process_all)
        self.outdir.mkdir(parents=True, exist_ok=True)
        analysed = 0
        for path in paths:
            if self.process_file(path):
                analysed += 1
        return analysed

    def _collect_paths(self, csv_path: Path,
                       process_all: bool) -> list[Path]:
        """Ta fram vilka filer som ska analyseras.

        Lyfter ``ObservationError`` om sökvägen inte går att använda,
        eftersom det är ett fel i anropet snarare än i en enskild fil.
        """
        if csv_path.is_dir():
            if not process_all:
                raise ObservationError(
                    f'{csv_path} är en katalog – använd --all för att '
                    'analysera alla CSV-filer i den')
            paths = sorted(csv_path.glob('*.csv'))
            if not paths:
                raise ObservationError(f'{csv_path} innehåller inga CSV-filer')
            return paths
        if not csv_path.exists():
            raise ObservationError(f'hittar inte filen {csv_path}')
        return [csv_path]

    def process_file(self, path: Path) -> bool:
        """Läs en fil och skapa diagrammen för den valda arten.

        Returnerar ``True`` om diagram kunde skapas. Fel i en fil
        rapporteras men avbryter inte programmet, eftersom
        beräkningarna ska fortsätta med övriga filer.
        """
        self._say(f'\n=== {path.name} ===')
        try:
            observations, issues = self.reader.read(path)
        except ObservationError as err:
            self._warn(f'Fel: {err}')
            return False

        self._report_issues(issues)
        if not observations:
            self._warn(f'Fel: {path.name} innehåller inga läsbara '
                       'observationer')
            return False

        species = self._choose_species(observations, path)
        if species is None:
            return False

        analysis = SpeciesAnalysis(species, observations)
        if len(analysis) == 0:
            self._warn(f'Fel: {path.name} innehåller inga observationer '
                       f'av {species}')
            return False
        self._present(analysis)
        return True

    def _report_issues(self, issues: list) -> None:
        """Skriv ut de problem som upptäcktes vid inläsningen."""
        if not issues:
            return
        rows = 'rad' if len(issues) == 1 else 'rader'
        self._warn(f'{len(issues)} {rows} gav problem vid inläsningen:')
        for issue in issues[:MAX_REPORTED_ISSUES]:
            self._warn(f'  {issue}')
        remaining = len(issues) - MAX_REPORTED_ISSUES
        if remaining > 0:
            self._warn(f'  ... och {remaining} till')

    def _choose_species(self, observations: list,
                        path: Path) -> str | None:
        """Bestäm vilken art som ska analyseras i en fil.

        Är ingen art vald på kommandoraden används den vanligaste arten
        i filen, vilket gör att programmet kan köras på nya filer utan
        att man vet vad de innehåller.
        """
        if self.species:
            return self.species
        names = SpeciesAnalysis.available_species(observations)
        if not names:
            self._warn(f'Fel: {path.name} saknar artnamn')
            return None
        if len(names) > 1:
            self._say(f'Filen innehåller flera arter: {", ".join(names)}')
        self._say(f'Analyserar den vanligaste arten: {names[0]}')
        return names[0]

    def _present(self, analysis: SpeciesAnalysis) -> None:
        """Skriv ut sammanfattningen och spara diagrammen för en art."""
        northernmost = analysis.northernmost_per_year()
        per_year = analysis.observations_per_year()
        individuals = analysis.individuals_per_year()
        proportions = analysis.weekly_proportions(self.week_year)
        period = analysis.active_period(self.week_year)

        self._say(f'{analysis.species}: {len(analysis)} observationer '
                  f'({sum(individuals.values())} individer) '
                  f'{min(per_year)}–{max(per_year)}')
        if period is None:
            self._warn(f'Varning: inga observationer {self.week_year}, '
                       'veckodiagrammet blir tomt')
        else:
            self._say(f'90 % av observationerna {self.week_year} görs '
                      f'från vecka {period[0]} till vecka {period[1]}')

        writer = FigureWriter(self.outdir, analysis.species, self.write_png)
        written = []
        if northernmost:
            written += writer.plot_northernmost(northernmost)
        else:
            self._warn('Varning: inga användbara nordkoordinater, '
                       'utbredningsdiagrammet hoppas över')
        if per_year:
            written += writer.plot_observations_per_year(per_year)
        written += writer.plot_weekly(proportions, self.week_year, period)
        for path in written:
            self._say(f'Skrev {path}')


def parse_args(argv=None):
    """Tolka kommandoradsargumenten."""
    parser = argparse.ArgumentParser(
        description='Analyserar fjärilars utbredning utifrån data '
                    'från Artportalen')
    parser.add_argument(
        '--csv', required=True,
        help='CSV-fil från Artportalen, eller en katalog med CSV-filer')
    parser.add_argument(
        '--species',
        help='Art att analysera (Artnamn). Utan denna flagga används '
             'den vanligaste arten i varje fil')
    parser.add_argument(
        '--outdir', default='.',
        help='Katalog att spara diagrammen i (standard: aktuell katalog)')
    parser.add_argument(
        '--all', dest='process_all', action='store_true',
        help='Analysera alla CSV-filer när --csv är en katalog')
    parser.add_argument(
        '--year', type=int, default=DEFAULT_WEEK_YEAR,
        help=f'År för veckodiagrammet (standard: {DEFAULT_WEEK_YEAR})')
    parser.add_argument(
        '--png', action='store_true',
        help='Spara diagrammen som PNG vid sidan av PDF-filerna')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Startpunkt för programmet; returnerar en statuskod till skalet."""
    args = parse_args(argv)
    app = ButterflyApplication(Path(args.outdir), args.year, args.species,
                               args.png)
    try:
        analysed = app.run(Path(args.csv), args.process_all)
    except ObservationError as err:
        print(f'Fel: {err}', file=sys.stderr)
        return 1
    if analysed == 0:
        print('Inga filer kunde analyseras', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
