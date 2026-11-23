import pytest

from view.format import file_size, mm_ss, percent, seconds_text, signed, timecode


@pytest.mark.parametrize(
    ("seconds", "fps", "expected"),
    [
        (0, 24, "00:00:00:00"),
        (65.5, 24, "00:01:05:12"),
        (3600, 30, "01:00:00:00"),
        (1 / 30, 30, "00:00:00:01"),
        # 0,999 s à 24 i/s s'arrondit à 24 images, donc à la seconde suivante
        (0.999, 24, "00:00:01:00"),
    ],
)
def test_timecode(seconds, fps, expected):
    assert timecode(seconds, fps) == expected


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "00:00"), (58, "00:58"), (65.9, "01:05"), (600, "10:00")],
)
def test_mm_ss(seconds, expected):
    assert mm_ss(seconds) == expected


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(5.6, "5,6 s"), (0, "0,0 s"), (12.34, "12,3 s")],
)
def test_seconds_text(seconds, expected):
    assert seconds_text(seconds) == expected


def test_percent():
    assert percent(30) == "30 %"


@pytest.mark.parametrize(("value", "expected"), [(12, "+12"), (-5, "-5"), (0, "0")])
def test_signed(value, expected):
    assert signed(value) == expected


@pytest.mark.parametrize(
    ("size", "expected"),
    [(200, "1 Ko"), (850_000, "850 Ko"), (65_400_000, "65 Mo"), (1_240_000_000, "1,2 Go")],
)
def test_file_size(size, expected):
    assert file_size(size) == expected
