import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from view.editor.properties.filters_page import FiltersPage
from view.theme import GREEN

PRESETS = [
    ("presetOriginalButton", "Original"),
    ("presetWarmButton", "Chaud"),
    ("presetCoolButton", "Froid"),
    ("presetMonoButton", "N&B"),
    ("presetVintageButton", "Vintage"),
    ("presetPastelButton", "Pastel"),
]


@pytest.fixture
def page(qtbot):
    widget = FiltersPage()
    qtbot.addWidget(widget)
    return widget


def swatch(button):
    return [label for label in button.findChildren(QLabel) if label.objectName() != "presetName"][0]


@pytest.mark.parametrize(("value", "expected"), [(25, "+25"), (-40, "-40"), (0, "0")])
def test_labels_follow_sliders(page, value, expected):
    for slider, label in page.sliders.items():
        slider.setValue(value)
        assert label.text() == expected, slider.objectName()


@pytest.mark.parametrize(("button_name", "title"), PRESETS)
def test_preset_content(page, button_name, title):
    button = getattr(page, button_name)
    assert button.findChild(QLabel, "presetName").text() == title
    assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_preset_labels_let_clicks_through(page):
    # sinon un clic sur la pastille ne cocherait pas le bouton
    for label in page.presetWarmButton.findChildren(QLabel):
        assert label.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


def test_checked_preset_has_green_border(qtbot, page):
    assert GREEN in swatch(page.presetOriginalButton).styleSheet()
    assert GREEN not in swatch(page.presetWarmButton).styleSheet()

    qtbot.mouseClick(page.presetWarmButton, Qt.MouseButton.LeftButton)
    assert page.presetWarmButton.isChecked()
    assert not page.presetOriginalButton.isChecked()
    assert GREEN in swatch(page.presetWarmButton).styleSheet()
    assert GREEN not in swatch(page.presetOriginalButton).styleSheet()


def test_reset_button(qtbot, page):
    page.presetVintageButton.setChecked(True)
    for slider in page.sliders:
        slider.setValue(50)

    assert not page.resetFiltersButton.icon().isNull()
    qtbot.mouseClick(page.resetFiltersButton, Qt.MouseButton.LeftButton)

    assert all(slider.value() == 0 for slider in page.sliders)
    assert page.presetOriginalButton.isChecked()
    assert not page.presetVintageButton.isChecked()
