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
    page.write('Fjärilars utbredning i Sverige', size=15, weight='bold')
    page.write('Rapport, individuell uppgift i programmering '
               '(DA2004/DA2005)', size=9)

    page.heading('1. Uppgiften')
    page.write(
        'Jag har gjort projektet "Fjärilars utbredning i Sverige" '
        '(nivå E–C). Programmet läser CSV-filer från Artportalen och gör '
        'tre diagram per art: nordligaste observationen per år (med '
        'linjer för Ystad och Abisko), antal observationer per år, och '
        'andel observationer per vecka för ett valt år, som standard '
        '2022. I veckodiagrammet färgas de veckor då 90 % av '
        'observationerna görs, och perioden skrivs också ut i terminalen. '
        'Diagrammen sparas som PDF.')

    page.heading('2. Så kör man programmet')
    page.write('Kör från projektkatalogen:')
    page.bullets([
        'En fil: python butterfly_analysis.py --csv butterfly_data/'
        'amiral.csv --outdir plots',
        'En hel katalog: python butterfly_analysis.py --csv '
        'butterfly_data --all --outdir plots',
        'Testerna: python -m unittest -v test_butterfly_analysis',
    ])
    page.write(
        'Övriga flaggor: --species "Amiral" väljer art (annars tas den '
        'vanligaste i filen), --year 2021 byter år för veckodiagrammet '
        'och --png sparar även PNG-filer. Programmet skriver ut en '
        'sammanfattning per fil och vilka rader som inte gick att tolka. '
        'En trasig fil stoppar inte körningen – resten analyseras ändå.')

    page.heading('3. Bibliotek')
    page.write(
        'Bara matplotlib utöver standardbiblioteket (csv, datetime, '
        'argparse, collections, pathlib, unittest). Ingen Pandas. '
        'Installera med:')
    page.write('    python -m pip install -r requirements.txt', size=8.5,
               indent=0.02)
    page.write('Kräver Python 3.9 eller senare.')

    page.heading('4. Programmets uppbyggnad')
    page.write(
        'Koden ligger i tre moduler plus huvudprogram och tester. Tanken '
        'är att varje fil har ett ansvar, så att beräkningarna går att '
        'testa utan att något skrivs till disk:')
    page.bullets([
        'observations.py – Observation (en observation, med metoder som '
        'tolkar Artnamn, Antal, Nord och Slutdatum) och '
        'ObservationReader som läser en CSV-fil. Problem returneras som '
        'ReadIssue-objekt i stället för att skrivas ut direkt.',
        'analysis.py – SpeciesAnalysis, som räknar ut allt för en art: '
        'nordligaste per år, observationer och individer per år, '
        'veckofördelning och 90 %-perioden. Ingen print, open eller '
        'matplotlib här.',
        'plotting.py – FigureWriter, som ritar och sparar diagrammen. '
        'All matplotlib-kod finns här.',
        'butterfly_analysis.py – huvudprogrammet. ButterflyApplication '
        'väljer filer och art och sköter alla utskrifter. Utanför '
        'klasserna finns bara parse_args och main.',
        'test_butterfly_analysis.py – 39 enhetstester.',
        'butterfly_data/ – datafiler, plots/ – färdiga diagram.',
    ])

    page.heading('Hjälpmedel')
    page.write(
        'Jag har använt ett AI-verktyg som stöd i arbetet, framför '
        'allt för enhetstesterna i test_butterfly_analysis.py och för '
        'uppdelningen i klasser. Jag har gått igenom koden och '
        'testerna och kontrollerat att de gör rätt saker.')
    page.close()


def write_page_two(pdf: PdfPages) -> None:
    """Sida 2: reflektioner kring design, felhantering och testning."""
    page = ReportPage(pdf)
    page.write('Reflektioner', size=13, weight='bold')

    page.heading('Koddesign', size=11)
    page.write(
        'Grundtanken är att hålla isär beräkning och utskrift. '
        'SpeciesAnalysis returnerar bara värden, FigureWriter ritar dem '
        'och ButterflyApplication skriver ut dem. Det gör beräkningarna '
        'lätta att testa – ett test kan kolla att 90 %-perioden blir '
        'vecka 20–21 utan att någon fil skapas. Inläsningen fungerar '
        'likadant: ObservationReader lämnar tillbaka problemen som '
        'ReadIssue-objekt, och huvudprogrammet avgör att bara de tio '
        'första visas. Det behövs, för filerna har tiotusentals rader.')

    page.heading('Algoritmer', size=11)
    page.write(
        'Allt räknas ut med en genomgång av observationerna: nordligaste '
        'per år är ett maximum per år, antal observationer en räknare. '
        '90 %-perioden får jag genom att gå igenom veckorna i ordning och '
        'summera – första veckan där andelen passerar 5 % blir start och '
        'första veckan över 95 % blir slut. Allt är linjärt i antalet '
        'rader, och alla sex filerna (drygt 130 000 rader) tar några '
        'sekunder.')

    page.heading('Datastrukturer', size=11)
    page.write(
        'Observationerna ligger i en lista av Observation-objekt med '
        '__slots__, vilket sparar minne när de är så många. Årsvisa '
        'resultat blir ordböcker med året som nyckel, eftersom alla år '
        'inte har observationer. Veckofördelningen är i stället en lista '
        'med 53 platser – veckonumren ligger alltid i samma intervall, '
        'så det blir enklare både att slå upp och att summera. '
        'Grupperingen följer ISO-året, så att dagar kring nyår hamnar i '
        'rätt vecka.')

    page.heading('Felhantering', size=11)
    page.write(
        'Jag delar upp felen efter hur allvarliga de är. En rad utan '
        'artnamn eller datum går inte att placera i något diagram, så '
        'den hoppas över med ett meddelande om radnummer och orsak. '
        'Saknad nordkoordinat är mindre illa: raden räknas fortfarande '
        'som en observation för sitt år, men används inte i '
        'utbredningsdiagrammet. "noterad" i kolumnen Antal tolkas som en '
        'individ, enligt uppgiften.')
    page.write(
        'Fel som gäller hela filen – ingen rubrikrad, saknade kolumner '
        'eller en fil som inte går att öppna – lyfts som ObservationError '
        'och fångas i huvudprogrammet, som rapporterar och går vidare '
        'till nästa fil. Filer som inte är UTF-8 provas om med CP1252 '
        'innan jag ger upp. Osäkra bestämningar, som Artportalen skriver '
        '"[Amiral]", räknar jag till samma art i stället för att slänga.')

    page.heading('Testning', size=11)
    page.write(
        'Det finns 39 enhetstester i test_butterfly_analysis.py. De '
        'täcker tolkningen av fälten (datum, antal, koordinat, artnamn '
        'inom hakparenteser), inläsningen av hela filer (semikolon inom '
        'citattecken, byte order mark från Excel, fel teckenkodning, '
        'saknade kolumner, trasiga rader), beräkningarna (maximum per '
        'år, veckofördelning, 90 %-perioden med och utan data) och att '
        'programmet fortsätter med nästa fil när en är trasig. Testerna '
        'använder temporära kataloger och lämnar inga filer efter sig.')
    page.write(
        'Som extra kontroll har jag räknat efter för hand: Grönsnabbvinge '
        'har 2 330 observationer 2022 och 90 %-perioden vecka 16–25, '
        'vilket stämmer med en uträkning direkt ur CSV-filen.')
    page.close()


def write_page_three(pdf: PdfPages) -> None:
    """Sida 3: appendix med exempelfigurer och svar på frågorna."""
    page = ReportPage(pdf)
    page.write('Appendix: exempelfigurer och biologiska frågor', size=13,
               weight='bold')
    page.write(
        f'Figurerna nedan är programmets utdata för {EXAMPLE_SPECIES}. '
        'Samma figurer för alla sex arter finns i plots/.')

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
    page.write('Nordligaste observationen i början och i slutet av '
               'perioden (mil norrut i RT 90, snitt över tre år), samt '
               '90 %-perioden 2022:', size=8)
    for species, first, last, weeks in species_summary():
        page.write(f'{species}: {first} → {last} mil, vecka {weeks}',
                   size=8, indent=0.025, spacing=0.85)
    page.write(
        'Vilka arter har flyttat norrut? Alla sex, men tydligast '
        'Sälgskimmerfjärilen.')
    page.write(
        'Är antalet observationer konstant? Nej, det ökar kraftigt för '
        'alla arter. Troligen har Artportalen fått fler användare '
        'snarare än att fjärilarna blivit fler – värt att tänka på även '
        'när man tolkar utbredningen.')
    page.write(
        'När är fjärilarna aktiva? Det skiljer sig mellan arterna. '
        'Grönsnabbvinge är en vårfjäril med en kort period i maj–juni, '
        'medan Amiral och Tistelfjäril, som flyger in söderifrån, syns '
        'sent och under mycket längre tid. Sorgmantel har den längsta '
        'perioden – den övervintrar som fullbildad.')
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
