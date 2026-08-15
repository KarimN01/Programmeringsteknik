"""Beräkningar på fjärilsobservationer.

Modulen innehåller klassen ``SpeciesAnalysis`` som svarar på uppgiftens
tre frågor för en art: hur den nordligaste observationen har flyttat
sig, hur många observationer som gjorts per år, och när på året arten
är aktiv.

Klassen innehåller medvetet inga anrop till ``print``, ``open`` eller
matplotlib. Alla metoder returnerar värden, vilket gör dem enkla att
testa med ``unittest`` och gör att samma beräkningar kan användas för
både diagram och textutskrifter.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from observations import Observation


# Nordkoordinater i RT 90 för två orter som uppgiften ber oss rita ut
# som referenslinjer i utbredningsdiagrammet. Värdena är konstanter
# hämtade ur uppgiftslydelsen och ändras aldrig under körningen.
YSTAD_NORTHING = 6164000
ABISKO_NORTHING = 7585000

# Antal veckor att redovisa i veckodiagrammet. ISO-kalendern har 52
# eller 53 veckor beroende på år, så platser för 53 veckor reserveras
# alltid.
WEEKS_PER_YEAR = 53


class SpeciesAnalysis:
    """Sammanställer observationer för en art.

    Vid skapandet plockas observationerna för den valda arten ut ur
    listan; jämförelsen av artnamn är skiftlägesoberoende.
    """

    def __init__(self, species: str, observations: list[Observation]):
        """Plocka ut observationerna av en art ur en lista."""
        self.species = species
        key = species.strip().lower()
        self.observations = [obs for obs in observations
                             if obs.species.lower() == key]

    def __len__(self) -> int:
        """Antalet observationer av arten."""
        return len(self.observations)

    @staticmethod
    def available_species(observations: list[Observation]) -> list[str]:
        """Artnamnen i materialet, vanligast först.

        Används för att kunna välja art automatiskt när användaren inte
        anger någon, och för att kunna visa vilka arter en fil
        innehåller.
        """
        counts = Counter(obs.species for obs in observations if obs.species)
        return [name for name, _ in counts.most_common()]

    def northernmost_per_year(self) -> dict[int, float]:
        """Nordligaste observationen (meter i RT 90) för varje år.

        År utan användbar nordkoordinat utelämnas ur resultatet.
        """
        northernmost: dict[int, float] = {}
        for obs in self.observations:
            if obs.northing is None:
                continue
            year = obs.year
            if year not in northernmost or obs.northing > northernmost[year]:
                northernmost[year] = obs.northing
        return northernmost

    def observations_per_year(self) -> dict[int, int]:
        """Antalet observationer per år.

        Här räknas rapporterade observationer, inte individer: en rad i
        datafilen är en observation oavsett hur många fjärilar som
        setts vid tillfället.
        """
        counts: dict[int, int] = defaultdict(int)
        for obs in self.observations:
            counts[obs.year] += 1
        return dict(counts)

    def individuals_per_year(self) -> dict[int, int]:
        """Antalet observerade individer per år.

        Summerar kolumnen Antal och kompletterar antalet observationer
        med ett mått på hur många fjärilar som faktiskt setts.
        """
        totals: dict[int, int] = defaultdict(int)
        for obs in self.observations:
            totals[obs.year] += obs.count
        return dict(totals)

    def years(self) -> list[int]:
        """Alla år som har minst en observation, i stigande ordning."""
        return sorted({obs.year for obs in self.observations})

    def weekly_counts(self, year: int) -> list[int]:
        """Antal observationer per ISO-vecka för ett år.

        Returnerar en lista med ``WEEKS_PER_YEAR`` element där index 0
        är vecka 1. Observationerna grupperas efter ISO-år, så att
        dagar kring nyår hamnar i den vecka de faktiskt tillhör.
        """
        counts = [0] * WEEKS_PER_YEAR
        for obs in self.observations:
            if obs.iso_year != year:
                continue
            week = obs.iso_week
            if 1 <= week <= WEEKS_PER_YEAR:
                counts[week - 1] += 1
        return counts

    def weekly_proportions(self, year: int) -> list[float]:
        """Andelen av årets observationer som gjorts varje vecka.

        Summan är 1 om året har några observationer, annars består
        listan av nollor.
        """
        counts = self.weekly_counts(year)
        total = sum(counts)
        if total == 0:
            return [0.0] * WEEKS_PER_YEAR
        return [count / total for count in counts]

    def active_period(self, year: int, lower: float = 0.05,
                      upper: float = 0.95) -> tuple[int, int] | None:
        """Veckorna då 90 % av årets observationer görs.

        Perioden bestäms av vid vilka veckonummer som de första 5 %
        respektive 95 % av observationerna har gjorts, enligt
        uppgiftslydelsen. Returnerar ``None`` om året saknar
        observationer.

        Gränserna ``lower`` och ``upper`` kan ändras för att räkna ut
        någon annan andel än 90 %.
        """
        counts = self.weekly_counts(year)
        total = sum(counts)
        if total == 0:
            return None
        first_week = last_week = None
        cumulative = 0
        for index, count in enumerate(counts):
            cumulative += count
            fraction = cumulative / total
            if first_week is None and fraction >= lower:
                first_week = index + 1
            if last_week is None and fraction >= upper:
                last_week = index + 1
        # Båda veckorna är satta här: den kumulativa andelen når alltid
        # 1.0 på sista veckan med observationer.
        return first_week, last_week
