from PyQt6.QtGui import QColor

from view.theme import ASSETS, CLIP_COLORS, KIND_ICONS, WHITE, icon, mix


def test_mix_extremes():
    assert mix("#000000", WHITE, 0) == QColor("#000000")
    assert mix("#000000", WHITE, 1) == QColor(WHITE)


def test_mix_middle():
    assert mix("#000000", "#C86432", 0.5) == QColor(100, 50, 25)


def test_icon_phosphor():
    assert not icon("film-strip").isNull()


def test_icon_waveform():
    assert not icon("waveform", WHITE).isNull()


def test_kind_icons_exist():
    for name in KIND_ICONS.values():
        assert not icon(name).isNull()


def test_clip_colors_are_valid():
    for colors in CLIP_COLORS.values():
        assert len(colors) == 3
        assert all(QColor(c).isValid() for c in colors)


def test_assets_at_project_root():
    assert ASSETS.name == "assets"
    assert (ASSETS.parent / "view").is_dir()
