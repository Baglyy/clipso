import pytest
from PyQt6.QtCore import Qt

from view.editor.properties.text_page import FONTS, TextPage


@pytest.fixture
def page(qtbot):
    widget = TextPage()
    qtbot.addWidget(widget)
    return widget


def test_size_label_follows_slider(page):
    page.textSizeSlider.setValue(120)
    assert page.textSizeValue.text() == "120 px"


def test_fonts(page):
    assert [page.fontCombo.itemText(i) for i in range(page.fontCombo.count())] == FONTS


@pytest.mark.parametrize(
    ("button_name", "color"),
    [
        ("colorWhiteButton", "#FFFFFF"),
        ("colorBlackButton", "#2B2A28"),
        ("colorYellowButton", "#F2C24B"),
        ("colorOrangeButton", "#EC8866"),
        ("colorBlueButton", "#7DB2E0"),
        ("colorGreenButton", "#94CF8E"),
    ],
)
def test_swatch_painted(page, button_name, color):
    button = getattr(page, button_name)
    assert f"background: {color}" in button.styleSheet()
    assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_white_swatch_has_visible_border(page):
    # une bordure blanche sur fond clair ne se verrait pas
    assert "border: 2px solid #D6D2C9" in page.colorWhiteButton.styleSheet()


def test_align_buttons_have_icon_and_hand_cursor(page):
    for button in (page.alignLeftButton, page.alignCenterButton, page.alignRightButton):
        assert not button.icon().isNull(), button.objectName()
        assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor, button.objectName()
