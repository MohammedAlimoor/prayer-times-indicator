"""Astronomical prayer-time calculation."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from prayertimes.calc import (
    METHODS,
    PRAYERS,
    PrayerCalculator,
    julian_date,
    next_prayer,
    sun_position,
)

MECCA = dict(lat=21.3891, lng=39.8579, tz="Asia/Riyadh")
DAY = date(2026, 8, 22)

# Umm al-Qura reference for Mecca, 22 Aug 2026. The algorithm is accurate to
# a couple of minutes, so every assertion below allows +/- 3 min.
EXPECTED = {
    "fajr": "04:41",
    "sunrise": "06:01",
    "dhuhr": "12:23",
    "asr": "15:46",
    "maghrib": "18:45",
    "isha": "20:15",
}


def minutes(dt):
    return dt.hour * 60 + dt.minute


def test_julian_date_matches_known_epoch():
    # 2000-01-01 12:00 UT == JD 2451545.0; julian_date() returns the 00:00 value.
    assert julian_date(2000, 1, 1) == pytest.approx(2451544.5, abs=1e-6)


def test_sun_position_is_in_range():
    decl, eqt = sun_position(julian_date(2026, 6, 21))
    assert 23.0 < decl < 23.6          # near the summer solstice
    assert -0.6 < eqt < 0.6            # equation of time, in hours


@pytest.mark.parametrize("prayer,expected", sorted(EXPECTED.items()))
def test_mecca_times_match_reference(prayer, expected):
    calc = PrayerCalculator(MECCA["lat"], MECCA["lng"], method="Makkah")
    got = calc.datetimes_for(DAY, MECCA["tz"])[prayer]
    want = datetime.strptime(expected, "%H:%M")
    assert abs(minutes(got) - minutes(want)) <= 3, f"{prayer}: got {got:%H:%M}"


def test_times_are_in_chronological_order():
    calc = PrayerCalculator(MECCA["lat"], MECCA["lng"], method="Makkah")
    times = calc.datetimes_for(DAY, MECCA["tz"])
    ordered = [times[p] for p in PRAYERS]
    assert ordered == sorted(ordered)


@pytest.mark.parametrize("method", sorted(METHODS))
def test_every_method_produces_a_full_ordered_day(method):
    calc = PrayerCalculator(MECCA["lat"], MECCA["lng"], method=method)
    times = calc.datetimes_for(DAY, MECCA["tz"])
    values = [times[p] for p in PRAYERS]
    assert all(v is not None for v in values), f"{method} left a prayer unset"
    assert values == sorted(values), f"{method} produced out-of-order times"


def test_hanafi_asr_is_later_than_standard():
    common = dict(lat=MECCA["lat"], lng=MECCA["lng"], method="Karachi")
    standard = PrayerCalculator(**common, params={"asr": "Standard"})
    hanafi = PrayerCalculator(**common, params={"asr": "Hanafi"})
    assert (hanafi.datetimes_for(DAY, MECCA["tz"])["asr"]
            > standard.datetimes_for(DAY, MECCA["tz"])["asr"])


def test_manual_offsets_shift_the_result():
    base = PrayerCalculator(MECCA["lat"], MECCA["lng"], method="Makkah")
    tuned = PrayerCalculator(MECCA["lat"], MECCA["lng"], method="Makkah",
                             offsets={"fajr": -7, "isha": 12})
    day = lambda c: c.datetimes_for(DAY, MECCA["tz"])
    assert day(tuned)["fajr"] == day(base)["fajr"] - timedelta(minutes=7)
    assert day(tuned)["isha"] == day(base)["isha"] + timedelta(minutes=12)


def test_high_latitude_summer_still_returns_every_prayer():
    """Tromso in June has no true nightfall; the high-latitude rule must fill in."""
    calc = PrayerCalculator(69.6496, 18.9560, method="MWL",
                            params={"highLats": "NightMiddle"})
    times = calc.datetimes_for(date(2026, 6, 21), "Europe/Oslo")
    assert all(times[p] is not None for p in PRAYERS)


def test_elevation_moves_sunrise_earlier():
    low = PrayerCalculator(MECCA["lat"], MECCA["lng"], elevation=0, method="MWL")
    high = PrayerCalculator(MECCA["lat"], MECCA["lng"], elevation=2000, method="MWL")
    assert (high.datetimes_for(DAY, MECCA["tz"])["sunrise"]
            < low.datetimes_for(DAY, MECCA["tz"])["sunrise"])


def test_next_prayer_picks_the_upcoming_one():
    calc = PrayerCalculator(MECCA["lat"], MECCA["lng"], method="Makkah")
    tz = ZoneInfo(MECCA["tz"])
    now = datetime(2026, 8, 22, 13, 0, tzinfo=tz)
    name, when = next_prayer(calc, MECCA["tz"], now=now)
    assert name == "asr"
    assert when > now


def test_next_prayer_rolls_over_to_tomorrow_after_isha():
    calc = PrayerCalculator(MECCA["lat"], MECCA["lng"], method="Makkah")
    tz = ZoneInfo(MECCA["tz"])
    now = datetime(2026, 8, 22, 23, 30, tzinfo=tz)
    name, when = next_prayer(calc, MECCA["tz"], now=now)
    assert name == "fajr"
    assert when.date() == date(2026, 8, 23)
