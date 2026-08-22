"""Built-in city database and its search."""

from zoneinfo import ZoneInfo

import pytest

from prayertimes import cities
from prayertimes.calc import METHODS


def test_database_is_not_tiny():
    assert len(cities.CITIES) >= 100


@pytest.mark.parametrize("city", cities.CITIES, ids=lambda c: c[1])
def test_every_row_is_well_formed(city):
    name_ar, name_en, lat, lng, tz, method = city
    assert name_ar and name_en
    assert -90 <= lat <= 90
    assert -180 <= lng <= 180
    ZoneInfo(tz)                      # raises if the zone is unknown
    assert method in METHODS


def test_names_are_unique():
    names = [c[0] for c in cities.CITIES]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("query", ["مكة", "mecca", "MECCA", "مكه"])
def test_search_finds_mecca_however_it_is_typed(query):
    assert cities.search(query)[0][0] == "مكة المكرمة"


def test_search_normalises_arabic_diacritics_and_hamza():
    assert cities.search("عمان")[0][0] == "عمّان"


def test_search_respects_the_limit():
    assert len(cities.search("a", limit=5)) <= 5


def test_search_of_nonsense_is_empty():
    assert cities.search("zzzzzzzz") == []


def test_find_round_trips():
    row = cities.find("مكة المكرمة")
    assert row is not None and row[1] == "Mecca"
    assert cities.find("no such city") is None
