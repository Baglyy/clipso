import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QToolButton

from view.home.recent_project_item import RecentProjectItem


@pytest.fixture
def item(qtbot):
    widget = RecentProjectItem("Vacances", "Modifié hier", "02:15", "#468A57")
    qtbot.addWidget(widget)
    return widget


def test_texts(item):
    assert item.findChild(QLabel, "projectTitle").text() == "Vacances"
    assert item.findChild(QLabel, "projectMeta").text() == "Modifié hier"
    assert item.findChild(QLabel, "projectDuration").text() == "02:15"


def test_thumbnail_uses_project_color(item):
    assert "#468A57" in item.findChild(QLabel, "projectThumbnail").styleSheet()


def test_hand_cursor_and_fixed_height(item):
    assert item.cursor().shape() == Qt.CursorShape.PointingHandCursor
    assert item.height() == 92


@pytest.mark.parametrize(
    ("name", "tooltip"),
    [("projectMoreButton", "Plus d'actions"), ("projectOpenButton", "Ouvrir")],
)
def test_buttons(item, name, tooltip):
    button = item.findChild(QToolButton, name)
    assert not button.icon().isNull()
    assert button.toolTip() == tooltip


def test_open_button_emits_open(qtbot, item):
    with qtbot.waitSignal(item.open_requested), qtbot.assertNotEmitted(item.more_requested):
        qtbot.mouseClick(item.findChild(QToolButton, "projectOpenButton"), Qt.MouseButton.LeftButton)


def test_more_button_emits_more_only(qtbot, item):
    # le clic sur « … » ne doit pas aussi ouvrir le projet
    with qtbot.waitSignal(item.more_requested), qtbot.assertNotEmitted(item.open_requested):
        qtbot.mouseClick(item.findChild(QToolButton, "projectMoreButton"), Qt.MouseButton.LeftButton)


def test_click_on_row_opens_project(qtbot, item):
    with qtbot.waitSignal(item.open_requested):
        qtbot.mouseClick(item, Qt.MouseButton.LeftButton)


def test_right_click_does_not_open(qtbot, item):
    with qtbot.assertNotEmitted(item.open_requested):
        qtbot.mouseClick(item, Qt.MouseButton.RightButton)
