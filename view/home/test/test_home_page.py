import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from view.home.home_page import HomePage, _format_pixmap


@pytest.fixture
def page(qtbot):
    widget = HomePage()
    qtbot.addWidget(widget)
    return widget


def test_images_loaded(page):
    assert not page.logoLabel.pixmap().isNull()
    assert not page.mascotLabel.pixmap().isNull()
    assert not page.newProjectIconLabel.pixmap().isNull()


def test_buttons_have_icon_and_hand_cursor(page):
    buttons = (
        page.helpButton,
        page.settingsButton,
        page.createProjectButton,
        page.openProjectButton,
        page.importMediaButton,
    )
    for button in buttons:
        assert not button.icon().isNull(), button.objectName()
        assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor, button.objectName()


def test_create_button_icon_on_the_right(page):
    assert page.createProjectButton.layoutDirection() == Qt.LayoutDirection.RightToLeft


def test_search_has_magnifying_glass(page):
    assert len(page.searchProjectEdit.actions()) == 1


@pytest.mark.parametrize(
    ("button_name", "title", "subtitle"),
    [
        ("formatLandscapeButton", "Paysage", "16:9 · YouTube"),
        ("formatVerticalButton", "Vertical", "9:16 · Réseaux"),
        ("formatSquareButton", "Carré", "1:1 · Publication"),
    ],
)
def test_format_button_content(page, button_name, title, subtitle):
    button = getattr(page, button_name)
    shape = button.findChild(QLabel, "formatShape")
    assert not shape.pixmap().isNull()
    assert button.findChild(QLabel, "formatTitle").text() == title
    assert button.findChild(QLabel, "formatSubtitle").text() == subtitle
    assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_format_labels_let_clicks_through(page):
    # sinon un clic sur le texte ne cocherait pas le bouton
    for label in page.formatSquareButton.findChildren(QLabel):
        assert label.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


def test_only_one_format_checked(qtbot, page):
    assert page.formatLandscapeButton.isChecked()
    qtbot.mouseClick(page.formatVerticalButton, Qt.MouseButton.LeftButton)
    assert page.formatVerticalButton.isChecked()
    assert not page.formatLandscapeButton.isChecked()
    assert not page.formatSquareButton.isChecked()


@pytest.mark.parametrize(("width", "height"), [(70, 38), (32, 56), (46, 46)])
def test_format_pixmap(width, height):
    image = _format_pixmap(width, height).toImage()
    left = (76 - width) // 2
    assert (image.width(), image.height()) == (76, 60)
    assert image.pixelColor(left, 30).alpha() > 0  # bord gauche du rectangle
    assert image.pixelColor(38, 30).alpha() == 0  # intérieur vide
    assert image.pixelColor(0, 0).alpha() == 0


def test_add_recent_project_keeps_spacer_last(page):
    layout = page.recentProjectsLayout
    first = page.add_recent_project("Vacances", "Modifié hier", "02:15", "#468A57")
    second = page.add_recent_project("Anniversaire", "Modifié il y a 3 jours", "00:58", "#9A5C7A")

    assert layout.indexOf(first) == 0
    assert layout.indexOf(second) == 1
    assert layout.itemAt(layout.count() - 1).spacerItem() is not None
