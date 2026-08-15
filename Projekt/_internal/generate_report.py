#!/usr/bin/env python3
"""Bygger rapporten (report.pdf) för fjärilsprojektet.

Skriptet ingår inte i själva inlämningsuppgiften utan är verktyget som
sätter ihop rapporten. Texten skrivs som riktig text i PDF:en (går att
markera och söka i), och siffrorna i appendix räknas fram med
projektets egna moduler så att rapporten inte kan hamna i otakt med
programmet.

Körs från projektkatalogen::

    python _internal/generate_report.py
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib                                        # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt                          # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages     # noqa: E402

from analysis import SpeciesAnalysis                     # noqa: E402
from observations import ObservationReader               # noqa: E402

OUT = ROOT / 'report.pdf'
DATA = ROOT / 'butterfly_data'
PLOTS = ROOT / 'plots'

# A4 i tum, samt marginaler och radavstånd uttryckta som andel av sidan.
PAGE_SIZE = (8.27, 11.69)
LEFT = 0.08
TOP = 0.955
LINE_HEIGHT = 0.0148
BODY_WIDTH = 96      # tecken per rad i brödtexten
EXAMPLE_SPECIES = 'Grönsnabbvinge'


class ReportPage:
    """En sida i rapporten som text skrivs på uppifrån och ned."""

    def __init__(self, pdf: PdfPages):
        """Börja en ny sida i den öppna PDF-filen."""
        self.pdf = pdf
        self.figure = plt.figure(figsize=PAGE_SIZE)
        self.y = TOP

    def write(self, text: str, size: int = 8.5, weight: str = 'normal',
              indent: float = 0.0, wrap: int = BODY_WIDTH,
              spacing: float = 1.0) -> None:
        """Skriv ett stycke och flytta ned skrivpositionen."""
        for line in textwrap.wrap(text, wrap) or ['']:
            self.figure.text(LEFT + indent, self.y, line, size=size,
                             weight=weight, va='top', family='DejaVu Sans')
            self.y -= LINE_HEIGHT * spacing * (size / 8.5)
        self.y -= LINE_HEIGHT * 0.35

    def heading(self, text: str, size: int = 13) -> None:
        """Skriv en rubrik med lite extra luft ovanför."""
        self.y -= LINE_HEIGHT * 0.6
        self.write(text, size=size, weight='bold')

    def bullets(self, items: list[str], indent: float = 0.025) -> None:
        """Skriv en punktlista."""
        for item in items:
            self.write(f'• {item}', indent=indent, wrap=BODY_WIDTH - 4)

    def images(self, paths: list[Path], height: float,
               caption: str = '') -> None:
        """Placera en eller flera bilder bredvid varandra.

        Bilderna delar på sidans bredd och behåller sina proportioner,
        så en enstaka bild fyller hela bredden.
        """
        missing = [p for p in paths if not p.exists()]
        if missing:
            self.write(f'(figurerna {", ".join(p.name for p in missing)} '
                       'saknas)')
            return
        self.y -= LINE_HEIGHT * 0.5
        gap = 0.02
        total = 1 - 2 * LEFT
        width = (total - gap * (len(paths) - 1)) / len(paths)
        for index, path in enumerate(paths):
            axes = self.figure.add_axes(
                (LEFT + index * (width + gap), self.y - height, width,
                 height))
            axes.imshow(plt.imread(str(path)))
            axes.axis('off')
        self.y -= height + LINE_HEIGHT * 0.5
        if caption:
            self.write(caption, size=7.5)

    def close(self) -> None:
        """Spara sidan i PDF:en."""
        self.pdf.savefig(self.figure)
        plt.close(self.figure)


def species_summary() -> list[tuple[str, str, str, str]]:
    """Räkna fram en rad per art till appendix.

    Returnerar art, nordligaste observation i början respektive slutet
    av perioden (medelvärde över tre år, i mil norrut) och den vecka
    då 90 % av observationerna 2022 görs.
    """
    reader = ObservationReader()
    rows = []
    for path in sorted(DATA.glob('*.csv')):
        observations, _ = reader.read(path)
        names = SpeciesAnalysis.available_species(observations)
        analysis = SpeciesAnalysis(names[0], observations)
        northernmost = analysis.northernmost_per_year()
        years = sorted(northernmost)
        first = sum(northernmost[y] for y in years[:3]) / 3 / 10000
        last = sum(northernmost[y] for y in years[-3:]) / 3 / 10000
        period = analysis.active_period(2022)
        weeks = f'{period[0]}–{period[1]}' if period else 'saknas'
        rows.append((names[0], f'{first:.0f}', f'{last:.0f}', weeks))
    return rows


def write_page_one(pdf: PdfPages) -> None:
    """Sida 1: de fyra obligatoriska punkterna."""
    page = ReportPage(pdf)
    page.write('INDU: Fjärilars utbredning i Sverige', size=15,
               weight='bold')
    page.write('Rapport för individuell uppgift i programmering '
               '(DA2004/DA2005)', size=9)

    page.heading('1. Vilken uppgift jag har implementerat')
    page.write(
        'Projektet "Fjärilars utbredning i Sverige" (nivå E–C). Programmet '
        'läser observationsdata som exporterats från Artportalen som '
        'semikolonseparerade CSV-filer och skapar tre diagram per art: '
        'nordligaste observationen per år med referenslinjer för Ystad och '
        'Abisko, antalet observationer per år, samt andelen observationer '
        'per vecka för ett valt år (2022 som standard). I veckodiagrammet '
        'markeras den period då 90 % av årets observationer görs, och '
        'samma period skrivs också ut i konsolen. Diagrammen sparas som '
        'PDF med filnamn som innehåller art och diagramtyp.')

    page.heading('2. Hur programmet startas och används')
    page.write('Programmet startas från projektkatalogen och styrs med '
               'flaggor på kommandoraden:')
    page.bullets([
        'En art: python butterfly_analysis.py --csv butterfly_data/'
        'amiral.csv --outdir plots',
        'Alla filer i en katalog: python butterfly_analysis.py --csv '
        'butterfly_data --all --outdir plots',
        '--species "Amiral" väljer art i en fil som innehåller flera; '
        'utan flaggan analyseras den vanligaste arten i varje fil.',
        '--year 2021 byter år för veckodiagrammet (standard 2022).',
        '--png sparar diagrammen som PNG vid sidan av PDF-filerna.',
        'Enhetstesterna körs med: python -m unittest -v '
        'test_butterfly_analysis',
    ])
    page.write(
        'Programmet skriver ut en sammanfattning per fil, samt vilka rader '
        'som inte kunde tolkas. En trasig fil avbryter inte körningen: '
        'övriga filer analyseras ändå.')

    page.heading('3. Bibliotek och installation')
    page.write(
        'Utöver Pythons standardbibliotek (csv, datetime, argparse, '
        'collections, pathlib och unittest) används endast '
        'matplotlib. Pandas används inte. Installation:')
    page.write('    python -m pip install -r requirements.txt', size=8.5,
               indent=0.02)
    page.write(
        'Programmet är skrivet för Python 3.9 eller senare (det använder '
        'date.fromisocalendar och typannoteringar via '
        'from __future__ import annotations).')

    page.heading('4. Så är programmet strukturerat')
    page.write(
        'Koden är uppdelad i tre moduler efter ansvar, plus ett '
        'huvudprogram och en testfil. Uppdelningen gör att beräkningarna '
        'kan testas utan att några filer eller diagram skapas:')
    page.bullets([
        'observations.py – klassen Observation (en observation, med '
        'metoder för att tolka fälten Artnamn, Antal, Nord och '
        'Slutdatum) och klassen ObservationReader som läser en CSV-fil '
        'till Observation-objekt. Problem returneras som ReadIssue-objekt '
        'i stället för att skrivas ut, så att inläsningen går att testa.',
        'analysis.py – klassen SpeciesAnalysis som gör alla beräkningar '
        'för en art: nordligaste observation per år, observationer och '
        'individer per år, veckofördelning och 90 %-perioden. Klassen '
        'innehåller varken print, open eller matplotlib.',
        'plotting.py – klassen FigureWriter som ritar och sparar de tre '
        'diagrammen. All matplotlib-kod ligger här.',
        'butterfly_analysis.py – huvudprogram. Klassen '
        'ButterflyApplication sköter användarinteraktionen: väljer filer '
        'och art, skriver ut sammanfattning och felmeddelanden och '
        'anropar de övriga modulerna. Utanför klasserna finns bara '
        'parse_args och main.',
        'test_butterfly_analysis.py – 39 enhetstester (unittest).',
        'butterfly_data/ – datafilerna, plots/ – de genererade '
        'diagrammen.',
    ])
    page.close()


def write_page_two(pdf: PdfPages) -> None:
    """Sida 2: reflektioner kring design, felhantering och testning."""
    page = ReportPage(pdf)
    page.write('Reflektioner kring lösningen', size=13, weight='bold')

    page.heading('Koddesign', size=11)
    page.write(
        'Den bärande tanken är att skilja beräkning från '
        'användarinteraktion. SpeciesAnalysis returnerar bara värden, '
        'FigureWriter ritar dem och ButterflyApplication skriver ut dem. '
        'Det gör beräkningarna testbara: ett test kan kontrollera att '
        '90 %-perioden blir vecka 20–21 utan att någon fil skapas. Samma '
        'princip gäller inläsningen, där ObservationReader returnerar '
        'ReadIssue-objekt i stället för att skriva ut felen själv – '
        'huvudprogrammet bestämmer att de tio första visas och resten '
        'sammanfattas, vilket behövs eftersom filerna har tiotusentals '
        'rader.')

    page.heading('Algoritmer', size=11)
    page.write(
        'Alla sammanställningar görs med en genomgång av '
        'observationslistan. Nordligaste observationen per år är ett '
        'löpande maximum per år, och antalet observationer per år en '
        'räknare per år. 90 %-perioden räknas ut genom att gå igenom '
        'veckorna i ordning och summera antalet observationer: den första '
        'veckan där den kumulativa andelen når 5 % blir periodens start '
        'och den första där den når 95 % blir dess slut. Alla stegen är '
        'linjära i antalet observationer, och en körning över alla sex '
        'datafilerna (drygt 130 000 rader) tar några sekunder.')

    page.heading('Datastrukturer', size=11)
    page.write(
        'Observationerna hålls som en lista av Observation-objekt med '
        '__slots__, vilket sparar minne när listan innehåller tiotusentals '
        'element. Årsvisa resultat returneras som ordböcker med året som '
        'nyckel, eftersom åren är glesa – en art behöver inte ha '
        'observationer varje år. Veckofördelningen är i stället en lista '
        'med 53 platser, eftersom veckonumren är tätt packade och alltid '
        'ligger i samma intervall; då blir både uppslagning och den '
        'kumulativa summeringen enkel. Observationerna grupperas efter '
        'ISO-år, så att dagarna kring nyår hamnar i den vecka de faktiskt '
        'tillhör.')

    page.heading('Felhantering', size=11)
    page.write(
        'Felen delas upp efter hur allvarliga de är. En rad utan tolkbart '
        'artnamn eller slutdatum kan inte placeras i något diagram och '
        'hoppas över med ett meddelande som anger radnummer och orsak. '
        'Saknad nordkoordinat är mindre allvarligt: observationen behålls '
        'och räknas för sitt år, men används inte i utbredningsdiagrammet. '
        'Enligt uppgiften tolkas "noterad" i kolumnen Antal som en individ. '
        'Fel som gäller hela filen – saknad rubrikrad, saknade kolumner '
        'eller en fil som inte går att öppna – lyfts som ObservationError '
        'och fångas i huvudprogrammet, som rapporterar felet och går '
        'vidare till nästa fil. Filer som inte är UTF-8 läses om med '
        'CP1252 innan de ges upp. Osäkra bestämningar, som Artportalen '
        'skriver "[Amiral]", räknas till samma art i stället för att '
        'kastas bort.')

    page.heading('Testning', size=11)
    page.write(
        'Programmet har 39 enhetstester i test_butterfly_analysis.py, '
        'körda med unittest. De täcker tolkningen av enskilda fält '
        '(datum, antal, koordinat, artnamn inom hakparenteser), '
        'inläsningen av hela filer (fält med semikolon inom citattecken, '
        'byte order mark från Excel, filer med fel teckenkodning, saknade '
        'kolumner, trasiga rader), beräkningarna (maximum per år, '
        'räknare per år, veckofördelning, 90 %-perioden med och utan '
        'data) samt att programmet fortsätter med nästa fil när en fil är '
        'trasig. Testerna använder temporära kataloger och lämnar inga '
        'filer efter sig.')
    page.write(
        'Kontrollräkning mot data: Grönsnabbvinge har 2 330 observationer '
        '2022 och 90 %-perioden vecka 16–25, vilket stämmer med en '
        'oberoende uträkning direkt ur CSV-filen.')
    page.close()


def write_page_three(pdf: PdfPages) -> None:
    """Sida 3: appendix med exempelfigurer och svar på frågorna."""
    page = ReportPage(pdf)
    page.write('Appendix: exempelfigurer och biologiska frågor', size=13,
               weight='bold')
    page.write(
        f'Figurerna nedan är programmets utdata för {EXAMPLE_SPECIES} '
        '(kommandot i punkt 2). Motsvarande figurer för samtliga sex '
        'arter finns i katalogen plots/.')

    stem = EXAMPLE_SPECIES.replace(' ', '_')
    page.images([PLOTS / f'{stem}_northernmost_per_year.png',
                 PLOTS / f'{stem}_observations_per_year.png'], 0.20,
                'Till vänster nordligaste observationen per år, med '
                'linjer för Ystad och Abisko; till höger antalet '
                'observationer per år.')
    page.images([PLOTS / f'{stem}_weekly_2022.png'], 0.20,
                'Andel observationer per vecka 2022. De blå staplarna är '
                'perioden då 90 % av observationerna görs.')

    page.heading('Svar på frågorna i uppgiften', size=11)
    page.write('Nordligaste observationen i början respektive slutet av '
               'perioden (mil norrut i RT 90, medelvärde över tre år) och '
               '90 %-perioden 2022:', size=8)
    for species, first, last, weeks in species_summary():
        page.write(f'{species}: {first} → {last} mil, vecka {weeks}',
                   size=8, indent=0.025, spacing=0.85)
    page.write(
        'Vilka arter verkar ha flyttat norrut? Samtliga arter har sin '
        'nordligaste observation längre norrut i slutet av perioden än i '
        'början. Tydligast är Sälgskimmerfjärilen.')
    page.write(
        'Är antalet observationer konstant? Nej, det ökar kraftigt för '
        'alla arter. Det beror troligen mer på att Artportalen fått fler '
        'användare än på att fjärilarna blivit fler – något att ha i '
        'åtanke även när man tolkar utbredningen.')
    page.write(
        'Finns det mönster i när fjärilarna är aktiva? Ja, och de skiljer '
        'sig mellan arterna. Grönsnabbvinge är en vårfjäril med en kort '
        'period i maj–juni, medan Amiral och Tistelfjäril, som flyger in '
        'söderifrån, syns sent och under betydligt längre tid. Sorgmantel '
        'har den längsta perioden eftersom den övervintrar som '
        'fullbildad.')
    page.close()


def main() -> None:
    """Skriv hela rapporten till report.pdf."""
    with PdfPages(OUT) as pdf:
        write_page_one(pdf)
        write_page_two(pdf)
        write_page_three(pdf)
    print(f'Skrev {OUT}')


if __name__ == '__main__':
    main()
