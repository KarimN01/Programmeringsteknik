"""Inläsning av observationsdata exporterad från Artportalen.

Modulen innehåller två klasser:

* ``Observation`` -- en enskild observation, med de fyra fält som
  projektet behöver (art, antal, nordkoordinat och slutdatum).
* ``ObservationReader`` -- läser en CSV-fil och bygger en lista av
  ``Observation``.

Ingen kod i modulen skriver ut något till användaren. Problem som
upptäcks vid inläsningen samlas i stället i en lista av ``ReadIssue``
som anroparen får tillbaka och kan presentera på lämpligt sätt. På så
sätt kan inläsningen både testas automatiskt och användas av program
med olika sorts användargränssnitt.
"""
from __future__ import annotations

import csv
from datetime import date


# Textvärden som Artportalen använder i kolumnen "Antal" i stället för
# ett tal. Enligt uppgiftslydelsen tolkas "noterad" som en individ, och
# vi behandlar övriga kända textmarkeringar på samma sätt eftersom de
# alla betyder att arten har setts men inte räknats.
TEXTUAL_COUNTS = {'noterad', 'ej återfunnen'}

# Kolumnrubriker som måste finnas i filen för att den ska kunna
# analyseras. Namnen skrivs som i Artportalens export, men jämförs
# skiftlägesoberoende.
REQUIRED_COLUMNS = ('Artnamn', 'Antal', 'Nord', 'Slutdatum')


class ObservationError(Exception):
    """Fel som gör att en fil eller en rad inte kan tolkas."""


class ReadIssue:
    """Ett problem som upptäcktes vid inläsning av en rad eller fil.

    Objektet beskriver problemet men skriver inte ut det; det gör den
    som anropat inläsningen.
    """

    def __init__(self, source: str, line: int | None, message: str):
        """Skapa ett problem för en fil, ett radnummer och en text."""
        self.source = source
        self.line = line
        self.message = message

    def __str__(self) -> str:
        """Problemet som en rad text att visa för användaren."""
        if self.line is None:
            return f'{self.source}: {self.message}'
        return f'{self.source} rad {self.line}: {self.message}'

    def __repr__(self) -> str:
        """Entydig form som underlättar felsökning och testning."""
        return f'ReadIssue({self.source!r}, {self.line!r}, {self.message!r})'


class Observation:
    """En observation av en fjärilsart vid ett tillfälle.

    Attributen är redan tolkade till Python-typer: ``species`` är en
    sträng, ``count`` ett heltal, ``northing`` ett flyttal (meter i
    RT 90) eller ``None`` om koordinaten saknas, och ``end_date`` ett
    ``datetime.date`` (Slutdatum).
    """

    # __slots__ sparar minne; datafilerna innehåller tiotusentals rader.
    __slots__ = ('species', 'count', 'northing', 'end_date')

    def __init__(self, species: str, count: int,
                 northing: float | None, end_date: date):
        """Skapa en observation av redan tolkade värden."""
        self.species = species
        self.count = count
        self.northing = northing
        self.end_date = end_date

    @property
    def year(self) -> int:
        """Året då observationen avslutades."""
        return self.end_date.year

    @property
    def iso_week(self) -> int:
        """ISO-veckonumret för observationens slutdatum."""
        return self.end_date.isocalendar()[1]

    @property
    def iso_year(self) -> int:
        """ISO-året för slutdatumet.

        Skiljer sig från ``year`` för dagar kring nyår, eftersom vecka 1
        kan börja i december och vecka 52/53 sträcka sig in i januari.
        """
        return self.end_date.isocalendar()[0]

    def __repr__(self) -> str:
        """Entydig form som underlättar felsökning och testning."""
        return (f'Observation({self.species!r}, {self.count!r}, '
                f'{self.northing!r}, {self.end_date!r})')

    @staticmethod
    def normalize_species(name: str) -> str:
        """Ta bort Artportalens hakparenteser kring ett artnamn.

        Artportalen skriver artnamnet inom hakparenteser, till exempel
        "[Amiral]", när bestämningen är osäker. Observationen gäller
        ändå samma art, och uppgiften säger att data inte får kastas
        bort, så namnet normaliseras i stället till "Amiral".
        """
        return name.strip().strip('[]').strip()

    @staticmethod
    def parse_count(raw: str) -> int:
        """Tolka kolumnen "Antal" som ett heltal.

        Tomt fält och Artportalens textmarkeringar (t.ex. "noterad")
        tolkas som en individ. Andra värden som inte går att tolka ger
        ``ObservationError``.
        """
        text = raw.strip()
        if not text or text.lower() in TEXTUAL_COUNTS:
            return 1
        try:
            return int(float(text.replace(',', '.')))
        except ValueError:
            raise ObservationError(f'kan inte tolka Antal: {raw!r}')

    @staticmethod
    def parse_northing(raw: str) -> float:
        """Tolka kolumnen "Nord" som meter norrut i RT 90."""
        text = raw.strip()
        if not text:
            raise ObservationError('Nord saknas')
        try:
            return float(text.replace(',', '.'))
        except ValueError:
            raise ObservationError(f'kan inte tolka Nord: {raw!r}')

    @staticmethod
    def parse_date(raw: str) -> date:
        """Tolka ett datum på ISO-form, t.ex. "2023-06-01".

        Ett eventuellt klockslag efter datumet ignoreras.
        """
        text = raw.strip()
        if not text:
            raise ObservationError('Slutdatum saknas')
        try:
            return date.fromisoformat(text.split()[0].split('T')[0])
        except ValueError:
            raise ObservationError(f'kan inte tolka Slutdatum: {raw!r}')


class ObservationReader:
    """Läser Artportalens CSV-filer till ``Observation``-objekt.

    Filerna är "CSV UTF-8" från Excel, alltså semikolonseparerade. De
    läses med modulen ``csv`` eftersom fält som Lokalnamn kan innehålla
    semikolon inom citattecken.
    """

    DELIMITER = ';'

    # utf-8-sig tar bort den byte order mark som Excel lägger först i
    # filen. Klarar filen inte UTF-8 provas Windows-kodningen i stället,
    # som är vanlig i exporter från äldre Excel.
    ENCODINGS = ('utf-8-sig', 'cp1252')

    def __init__(self, delimiter: str = DELIMITER):
        """Skapa en inläsare för ett givet fältavskiljartecken."""
        self.delimiter = delimiter

    def read(self, path) -> tuple[list[Observation], list[ReadIssue]]:
        """Läs en fil och returnera observationerna och funna problem.

        Rader som inte går att tolka hoppas över och beskrivs i den
        returnerade listan av ``ReadIssue``; resten av filen läses
        ändå. Går hela filen inte att läsa lyfts ``ObservationError``.
        """
        last_error: UnicodeDecodeError | None = None
        for encoding in self.ENCODINGS:
            try:
                return self._read_with_encoding(path, encoding)
            except UnicodeDecodeError as err:
                last_error = err
        raise ObservationError(
            f'{path}: filen är varken UTF-8 eller CP1252 ({last_error})')

    def _read_with_encoding(self, path, encoding: str):
        """Läs filen med en bestämd teckenkodning.

        Hjälpmetod till ``read``; lyfter ``UnicodeDecodeError`` om
        kodningen är fel så att anroparen kan prova nästa.
        """
        observations: list[Observation] = []
        issues: list[ReadIssue] = []
        source = getattr(path, 'name', str(path))
        try:
            handle = open(path, encoding=encoding, newline='')
        except OSError as err:
            raise ObservationError(f'kan inte öppna {path}: {err}')

        with handle:
            reader = csv.DictReader(handle, delimiter=self.delimiter)
            columns = self._column_map(reader.fieldnames, source)
            self._read_rows(reader, columns, source, observations, issues)
        return observations, issues

    def _read_rows(self, reader, columns, source, observations, issues):
        """Tolka raderna i en öppnad ``csv.DictReader``.

        Fyller på ``observations`` och ``issues`` i stället för att
        returnera dem, så att redan inlästa rader behålls även om
        ``csv`` avbryter läsningen med ett fel.
        """
        line = 1  # rad 1 är rubrikraden
        try:
            for line, row in enumerate(reader, start=2):
                try:
                    observation, warnings = self._build(row, columns)
                except ObservationError as err:
                    issues.append(ReadIssue(source, line, str(err)))
                    continue
                observations.append(observation)
                for warning in warnings:
                    issues.append(ReadIssue(source, line, warning))
        except csv.Error as err:
            issues.append(ReadIssue(
                source, line, f'läsningen avbröts: {err}'))

    def _column_map(self, fieldnames, source: str) -> dict[str, str]:
        """Matcha kolumnrubrikerna mot de fält programmet behöver.

        Jämförelsen är skiftlägesoberoende och tål extra blanktecken,
        så att filer med lite olika rubrikstil kan läsas.
        """
        if not fieldnames:
            raise ObservationError(f'{source}: filen saknar rubrikrad')
        found = {name.strip().lower(): name for name in fieldnames if name}
        missing = [c for c in REQUIRED_COLUMNS if c.lower() not in found]
        if missing:
            raise ObservationError(
                f'{source}: kolumnerna {", ".join(missing)} saknas')
        return {c.lower(): found[c.lower()] for c in REQUIRED_COLUMNS}

    def _build(self, row: dict,
               columns: dict) -> tuple[Observation, list[str]]:
        """Skapa en ``Observation`` från en rad, med eventuella varningar.

        Art och slutdatum krävs, eftersom en observation utan dem inte
        kan placeras i något diagram; saknas de lyfts
        ``ObservationError`` och raden hoppas över. Saknad eller
        felaktig nordkoordinat gör däremot bara att observationen inte
        används i utbredningsdiagrammet -- den räknas fortfarande som
        en observation för sitt år. Sådana mindre problem returneras
        som varningstexter i stället för att kasta bort raden.
        """
        warnings: list[str] = []
        raw_species = row.get(columns['artnamn'], '')
        species = Observation.normalize_species(raw_species)
        if not species:
            raise ObservationError('Artnamn saknas')
        end_date = Observation.parse_date(row.get(columns['slutdatum'], ''))
        try:
            northing = Observation.parse_northing(row.get(columns['nord'], ''))
        except ObservationError as err:
            northing = None
            warnings.append(f'{err}; raden används inte i utbredningen')
        try:
            count = Observation.parse_count(row.get(columns['antal'], ''))
        except ObservationError as err:
            count = 1
            warnings.append(f'{err}; antalet räknas som 1')
        return Observation(species, count, northing, end_date), warnings
