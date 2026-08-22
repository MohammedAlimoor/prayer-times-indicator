"""Tabular Hijri calendar conversion and formatting."""

from datetime import date, timedelta

from prayertimes import hijri


def test_known_conversion():
    assert hijri.to_hijri(date(2026, 8, 22)) == (1448, 3, 8)


def test_offset_shifts_the_day():
    plain = hijri.to_hijri(date(2026, 8, 22))
    shifted = hijri.to_hijri(date(2026, 8, 22), offset_days=1)
    assert shifted[2] == plain[2] + 1


def test_conversion_is_monotonic_over_a_year():
    previous = None
    day = date(2026, 1, 1)
    for _ in range(365):
        current = hijri.to_hijri(day)
        assert 1 <= current[1] <= 12
        assert 1 <= current[2] <= 30
        if previous is not None:
            assert current >= previous
        previous = current
        day += timedelta(days=1)


def test_formatting_is_arabic_and_non_empty():
    text = hijri.format_hijri(date(2026, 8, 22))
    assert "1448" in text and "هـ" in text
    assert hijri.format_gregorian(date(2026, 8, 22))


def test_ramadan_flag():
    ramadan_start = next(
        date(2027, 1, 1) + timedelta(days=n)
        for n in range(400)
        if hijri.to_hijri(date(2027, 1, 1) + timedelta(days=n))[1] == 9
    )
    assert hijri.is_ramadan(ramadan_start)
    assert not hijri.is_ramadan(ramadan_start - timedelta(days=2))
