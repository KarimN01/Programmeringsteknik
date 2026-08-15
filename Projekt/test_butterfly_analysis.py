#!/usr/bin/env python3
"""Enhetstester för fjärilsanalysen.

Körs med::

    python -m unittest -v test_butterfly_analysis

Testerna täcker inläsningen (inklusive trasiga rader och fält med
semikolon), beräkningarna och att diagramfilerna faktiskt skapas.
"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from analysis import SpeciesAnalysis, WEEKS_PER_YEAR
from observations import (Observation, ObservationError, ObservationReader)


HEADER = ('Artnamn;Antal;Lokalnamn;Ost;Nord;Startdatum;Slutdatum\n')


def make_row(species='Amiral', count='1', locality='Flen',
             northing='6548800', end_date='2022-07-01') -> str:
    """Bygg en rad i samma format som Artportalens export."""
    return (f'{species};{count};{locality};1544610;{northing};'
            f'{end_date};{end_date}\n')


def observation(species='Amiral', count=1, northing=6548800.0,
                end_date=(2022, 7, 1)) -> Observation:
    """Skapa en observation utan att gå via en fil."""
    return Observation(species, count, northing, date(*end_date))


class TemporaryCsvTestCase(unittest.TestCase):
    """Bastestfall som kan skriva CSV-filer i en temporär katalog."""

    def setUp(self):
        """Skapa en temporär katalog för testets filer."""
        self._tempdir = tempfile.TemporaryDirectory()
        self.tempdir = Path(self._tempdir.name)
        self.addCleanup(self._tempdir.cleanup)

    def write_csv(self, text: str, name: str = 'data.csv',
                  encoding: str = 'utf-8') -> Path:
        """Skriv en CSV-fil och returnera sökvägen till den."""
        path = self.tempdir / name
        path.write_text(text, encoding=encoding)
        return path


class TestFieldParsing(unittest.TestCase):
    """Tester för tolkningen av enskilda fält."""

    def test_count_accepts_numbers(self):
        """Ett tal i kolumnen Antal läses som heltal."""
        self.assertEqual(Observation.parse_count('12'), 12)

    def test_count_treats_noted_as_one(self):
        """Texten 'noterad' tolkas som en individ enligt uppgiften."""
        self.assertEqual(Observation.parse_count('noterad'), 1)
        self.assertEqual(Observation.parse_count('Noterad'), 1)

    def test_count_treats_empty_as_one(self):
        """Tomt antal tolkas som en individ."""
        self.assertEqual(Observation.parse_count('   '), 1)

    def test_count_rejects_nonsense(self):
        """Ett otolkbart antal ger ObservationError."""
        with self.assertRaises(ObservationError):
            Observation.parse_count('många')

    def test_northing_is_parsed_as_float(self):
        """Nordkoordinaten läses som flyttal."""
        self.assertEqual(Observation.parse_northing(' 6548800 '), 6548800.0)

    def test_northing_requires_a_value(self):
        """Saknad eller felaktig Nord ger fel."""
        with self.assertRaises(ObservationError):
            Observation.parse_northing('')
        with self.assertRaises(ObservationError):
            Observation.parse_northing('okänd')

    def test_date_is_parsed_from_iso_format(self):
        """Datum på ISO-form läses korrekt."""
        self.assertEqual(Observation.parse_date('2023-06-01'),
                         date(2023, 6, 1))

    def test_date_ignores_time_of_day(self):
        """Klockslag efter datumet ignoreras."""
        self.assertEqual(Observation.parse_date('2023-06-01 15:45'),
                         date(2023, 6, 1))

    def test_date_rejects_invalid_values(self):
        """Ogiltiga datum ger ObservationError."""
        for text in ('', 'i somras', '2023-13-01'):
            with self.assertRaises(ObservationError):
                Observation.parse_date(text)

    def test_species_brackets_are_removed(self):
        """Hakparenteser kring artnamn tas bort.

        Artportalen skriver osäkra bestämningar som "[Amiral]".
        """
        self.assertEqual(Observation.normalize_species('[Amiral] '), 'Amiral')
        self.assertEqual(Observation.normalize_species('Amiral'), 'Amiral')

    def test_week_and_year_follow_the_iso_calendar(self):
        """År och veckonummer följer ISO-kalendern."""
        obs = observation(end_date=(2022, 7, 1))
        self.assertEqual(obs.year, 2022)
        self.assertEqual(obs.iso_week, 26)
        self.assertEqual(obs.iso_year, 2022)


class TestObservationReader(TemporaryCsvTestCase):
    """Tester för inläsningen av hela filer."""

    def test_reads_all_rows(self):
        """Alla rader i en riktig fil läses in."""
        path = self.write_csv(HEADER + make_row() + make_row(count='3'))
        observations, issues = ObservationReader().read(path)
        self.assertEqual(len(observations), 2)
        self.assertEqual(issues, [])
        self.assertEqual([obs.count for obs in observations], [1, 3])

    def test_semicolon_inside_quoted_field_is_kept(self):
        """Semikolon inom citattecken delar inte raden."""
        locality = '"Skottsundslätten; Njurunda"'
        path = self.write_csv(HEADER + make_row(locality=locality))
        observations, issues = ObservationReader().read(path)
        self.assertEqual(issues, [])
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].northing, 6548800.0)

    def test_broken_row_is_reported_but_reading_continues(self):
        """En trasig rad rapporteras men stoppar inte inläsningen."""
        path = self.write_csv(HEADER
                              + make_row(end_date='inte-ett-datum')
                              + make_row())
        observations, issues = ObservationReader().read(path)
        self.assertEqual(len(observations), 1)
        self.assertEqual(len(issues), 1)
        self.assertIn('Slutdatum', str(issues[0]))

    def test_missing_northing_keeps_the_observation(self):
        """Observation utan koordinat behålls men rapporteras."""
        path = self.write_csv(HEADER + make_row(northing=''))
        observations, issues = ObservationReader().read(path)
        self.assertEqual(len(observations), 1)
        self.assertIsNone(observations[0].northing)
        self.assertEqual(len(issues), 1)

    def test_missing_column_raises(self):
        """Saknad kolumn ger ett tydligt fel."""
        path = self.write_csv('Artnamn;Antal\nAmiral;1\n')
        with self.assertRaises(ObservationError) as caught:
            ObservationReader().read(path)
        self.assertIn('Nord', str(caught.exception))

    def test_missing_file_raises(self):
        """En fil som inte finns ger ObservationError."""
        with self.assertRaises(ObservationError):
            ObservationReader().read(self.tempdir / 'finns-inte.csv')

    def test_byte_order_mark_is_ignored(self):
        """Excels byte order mark i filens början stör inte."""
        path = self.write_csv(HEADER + make_row(), encoding='utf-8-sig')
        observations, _ = ObservationReader().read(path)
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].species, 'Amiral')

    def test_non_utf8_file_is_read_with_fallback_encoding(self):
        """En fil som inte är UTF-8 läses om med CP1252."""
        path = self.write_csv(HEADER + make_row(species='Sälgskimmerfjäril'),
                              encoding='cp1252')
        observations, _ = ObservationReader().read(path)
        self.assertEqual(observations[0].species, 'Sälgskimmerfjäril')


class TestSpeciesAnalysis(unittest.TestCase):
    """Tester för beräkningarna."""

    def setUp(self):
        """Skapa några observationer att räkna på."""
        self.observations = [
            observation(northing=6200000.0, end_date=(2020, 5, 4)),
            observation(northing=6400000.0, end_date=(2020, 6, 8)),
            observation(northing=6300000.0, end_date=(2021, 6, 7), count=5),
            observation(species='Sorgmantel', northing=7000000.0,
                        end_date=(2021, 6, 7)),
        ]
        self.analysis = SpeciesAnalysis('Amiral', self.observations)

    def test_only_the_chosen_species_is_analysed(self):
        """Bara den valda artens observationer används."""
        self.assertEqual(len(self.analysis), 3)

    def test_species_matching_ignores_case(self):
        """Artnamn jämförs skiftlägesoberoende."""
        self.assertEqual(len(SpeciesAnalysis('amiral', self.observations)), 3)

    def test_northernmost_per_year_takes_the_maximum(self):
        """Nordligaste observationen per år är årets maximum."""
        self.assertEqual(self.analysis.northernmost_per_year(),
                         {2020: 6400000.0, 2021: 6300000.0})

    def test_northernmost_skips_observations_without_coordinate(self):
        """År utan koordinater utelämnas ur utbredningen."""
        analysis = SpeciesAnalysis('Amiral', [
            observation(northing=None, end_date=(2019, 6, 1)),
            observation(northing=6100000.0, end_date=(2020, 6, 1)),
        ])
        self.assertEqual(analysis.northernmost_per_year(), {2020: 6100000.0})

    def test_observations_per_year_counts_rows(self):
        """Observationer per år räknar rader, inte individer."""
        self.assertEqual(self.analysis.observations_per_year(),
                         {2020: 2, 2021: 1})

    def test_individuals_per_year_sums_the_count_column(self):
        """Individer per år summerar kolumnen Antal."""
        self.assertEqual(self.analysis.individuals_per_year(),
                         {2020: 2, 2021: 5})

    def test_available_species_lists_the_most_common_first(self):
        """Arterna listas med den vanligaste först."""
        self.assertEqual(SpeciesAnalysis.available_species(self.observations),
                         ['Amiral', 'Sorgmantel'])

    def test_years_are_sorted(self):
        """Årtalen returneras i stigande ordning."""
        self.assertEqual(self.analysis.years(), [2020, 2021])


class TestWeeklyDistribution(unittest.TestCase):
    """Tester för veckofördelningen och 90 %-perioden."""

    def build(self, weeks_with_counts: dict[int, int],
              year: int = 2022) -> SpeciesAnalysis:
        """Skapa en analys med ett givet antal observationer per vecka."""
        observations = []
        for week, count in weeks_with_counts.items():
            day = date.fromisocalendar(year, week, 1)
            for _ in range(count):
                observations.append(observation(
                    end_date=(day.year, day.month, day.day)))
        return SpeciesAnalysis('Amiral', observations)

    def test_counts_are_placed_in_the_right_week(self):
        """Observationerna hamnar i rätt vecka."""
        counts = self.build({10: 2, 20: 3}).weekly_counts(2022)
        self.assertEqual(len(counts), WEEKS_PER_YEAR)
        self.assertEqual(counts[9], 2)
        self.assertEqual(counts[19], 3)
        self.assertEqual(sum(counts), 5)

    def test_proportions_sum_to_one(self):
        """Veckoandelarna summerar till ett."""
        proportions = self.build({10: 2, 20: 3}).weekly_proportions(2022)
        self.assertAlmostEqual(sum(proportions), 1.0)
        self.assertAlmostEqual(proportions[9], 0.4)

    def test_other_years_are_not_counted(self):
        """Andra år räknas inte med."""
        analysis = self.build({10: 4}, year=2021)
        self.assertEqual(sum(analysis.weekly_counts(2022)), 0)
        self.assertEqual(sum(analysis.weekly_counts(2021)), 4)

    def test_active_period_covers_ninety_percent(self):
        """90 %-perioden täcker rätt veckor vid jämn fördelning."""
        # 100 observationer jämnt fördelade över veckorna 1-10: de
        # första 5 % är nådda i vecka 1 och 95 % i vecka 10.
        analysis = self.build({week: 10 for week in range(1, 11)})
        self.assertEqual(analysis.active_period(2022), (1, 10))

    def test_active_period_ignores_thin_tails(self):
        """Enstaka observationer i kanterna hamnar utanför perioden."""
        # En enstaka observation i vecka 1 och en i vecka 50 utgör
        # mindre än 5 % vardera och ska hamna utanför perioden.
        counts = {1: 1, 20: 50, 21: 50, 50: 1}
        self.assertEqual(self.build(counts).active_period(2022), (20, 21))

    def test_active_period_is_none_without_observations(self):
        """Ett år utan observationer saknar period."""
        self.assertIsNone(self.build({}).active_period(2022))

    def test_proportions_are_zero_without_observations(self):
        """Utan observationer blir alla veckoandelar noll."""
        proportions = self.build({}).weekly_proportions(2022)
        self.assertEqual(proportions, [0.0] * WEEKS_PER_YEAR)

    def test_bounds_can_be_changed(self):
        """Gränserna för perioden går att ändra."""
        analysis = self.build({week: 10 for week in range(1, 11)})
        self.assertEqual(analysis.active_period(2022, 0.25, 0.75), (3, 8))


class TestFigureWriter(TemporaryCsvTestCase):
    """Tester som kontrollerar att diagramfilerna skapas."""

    def test_all_three_figures_are_written_as_pdf(self):
        """Alla tre diagram skapas som PDF-filer."""
        from plotting import FigureWriter

        analysis = SpeciesAnalysis('Amiral', [
            observation(northing=6200000.0, end_date=(2021, 6, 7)),
            observation(northing=6400000.0, end_date=(2022, 6, 8)),
        ])
        writer = FigureWriter(self.tempdir, 'Amiral')
        written = writer.plot_northernmost(analysis.northernmost_per_year())
        written += writer.plot_observations_per_year(
            analysis.observations_per_year())
        written += writer.plot_weekly(analysis.weekly_proportions(2022), 2022,
                                      analysis.active_period(2022))
        self.assertEqual(len(written), 3)
        for path in written:
            self.assertTrue(path.exists(), f'{path} skapades inte')
            self.assertEqual(path.suffix, '.pdf')
            self.assertGreater(path.stat().st_size, 0)


class TestApplication(TemporaryCsvTestCase):
    """Tester för programmets styrning av flera filer."""

    def run_app(self, csv_path, **kwargs):
        """Kör programmet med utskrifterna fångade i minnet."""
        import io

        from butterfly_analysis import ButterflyApplication

        out, err = io.StringIO(), io.StringIO()
        app = ButterflyApplication(self.tempdir / 'ut', stream=out,
                                   error_stream=err, **kwargs)
        analysed = app.run(Path(csv_path), process_all=True)
        return analysed, out.getvalue(), err.getvalue()

    def test_a_broken_file_does_not_stop_the_other_files(self):
        """En trasig fil hindrar inte de övriga från att analyseras."""
        data = self.tempdir / 'data'
        data.mkdir()
        (data / 'a.csv').write_text(HEADER + make_row(), encoding='utf-8')
        # Filen saknar de kolumner som behövs och kan inte analyseras.
        (data / 'b.csv').write_text('Artnamn;Antal\nAmiral;1\n',
                                    encoding='utf-8')
        (data / 'c.csv').write_text(HEADER + make_row(species='Sorgmantel'),
                                    encoding='utf-8')

        analysed, output, errors = self.run_app(data)

        self.assertEqual(analysed, 2)
        self.assertIn('b.csv', errors)
        self.assertIn('Sorgmantel', output)

    def test_missing_species_in_one_file_is_reported(self):
        """En fil utan den valda arten rapporteras och hoppas över."""
        data = self.tempdir / 'data'
        data.mkdir()
        (data / 'a.csv').write_text(HEADER + make_row(), encoding='utf-8')
        (data / 'b.csv').write_text(HEADER + make_row(species='Sorgmantel'),
                                    encoding='utf-8')

        analysed, _, errors = self.run_app(data, species='Amiral')

        self.assertEqual(analysed, 1)
        self.assertIn('inga observationer av Amiral', errors)

    def test_directory_without_csv_files_raises(self):
        """En katalog utan CSV-filer ger ObservationError."""
        empty = self.tempdir / 'tom'
        empty.mkdir()
        with self.assertRaises(ObservationError):
            self.run_app(empty)


if __name__ == '__main__':
    unittest.main()
