import pytest
from PyQt6.QtCore import Qt

from view.editor.properties.properties_panel import AVAILABLE_TABS, EMPTY_PAGE, TABS, PropertiesPanel
from view.theme import CLIP_COLORS, mix

TRACK = {"name": "Vidéo 1"}


def clip(kind, name="clip", start=31, duration=10, color="#AE7657"):
    return {"kind": kind, "name": name, "start": start, "duration": duration, "color": color}


@pytest.fixture
def panel(qtbot):
    widget = PropertiesPanel()
    qtbot.addWidget(widget)
    return widget


def test_tab_buttons_have_hand_cursor(panel):
    for button in panel.tab_buttons.values():
        assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor, button.objectName()


def test_show_clip_header(panel):
    panel.show_clip(TRACK, clip("image", name="logo.png", start=31, duration=10))
    assert panel.selectionNameLabel.text() == "logo.png"
    assert panel.selectionMetaLabel.text() == "Vidéo 1 · 00:31 → 00:41 · 10,0 s"
    assert not panel.selectionIconLabel.pixmap().isNull()
    assert CLIP_COLORS["image"][0] in panel.selectionIconLabel.styleSheet()


def test_video_header_uses_clip_color(panel):
    panel.show_clip(TRACK, clip("video", color="#468A57"))
    expected = mix("#468A57", "#FFFFFF", 0.78).name()
    assert expected in panel.selectionIconLabel.styleSheet()


@pytest.mark.parametrize(
    ("kind", "default_tab"),
    [("text", "text"), ("image", "image"), ("video", "filters"), ("audio", "audio")],
)
def test_show_clip_opens_default_tab(panel, kind, default_tab):
    panel.show_clip(TRACK, clip(kind))
    assert panel.tab_buttons[default_tab].isChecked()
    assert panel.propertyStack.currentIndex() == TABS.index(default_tab)


@pytest.mark.parametrize("kind", ["text", "image", "video", "audio"])
def test_unavailable_tabs_marked(panel, kind):
    panel.show_clip(TRACK, clip(kind))
    for name, button in panel.tab_buttons.items():
        assert button.property("unavailable") == (name not in AVAILABLE_TABS[kind]), name


def test_show_clip_with_requested_tab(panel):
    panel.show_clip(TRACK, clip("video"), tab="blur")
    assert panel.blurTabButton.isChecked()
    assert panel.propertyStack.currentIndex() == TABS.index("blur")


def test_click_on_available_tab(qtbot, panel):
    panel.show_clip(TRACK, clip("video"))
    qtbot.mouseClick(panel.audioTabButton, Qt.MouseButton.LeftButton)
    assert panel.propertyStack.currentIndex() == TABS.index("audio")


def test_click_on_unavailable_tab_shows_empty_page(qtbot, panel):
    panel.show_clip(TRACK, clip("text"))
    qtbot.mouseClick(panel.imageTabButton, Qt.MouseButton.LeftButton)
    assert panel.propertyStack.currentIndex() == EMPTY_PAGE
    assert panel.emptyTitleLabel.text() == "Pas d'image sur ce clip"
    assert not panel.emptyIconLabel.pixmap().isNull()
    assert panel.emptyActionButton.isHidden()


def test_empty_text_tab_has_action_button(qtbot, panel):
    panel.show_clip(TRACK, clip("audio"))
    qtbot.mouseClick(panel.textTabButton, Qt.MouseButton.LeftButton)
    assert panel.propertyStack.currentIndex() == EMPTY_PAGE
    assert panel.emptyTitleLabel.text() == "Pas de texte sur ce clip"
    assert not panel.emptyActionButton.isHidden()
    assert panel.emptyActionButton.text() == "Ajouter un texte"


def test_same_tab_refreshed_when_clip_changes(panel):
    # l'onglet Audio est déjà coché : il faut quand même passer sur la page vide pour un clip texte
    panel.show_clip(TRACK, clip("audio"))
    panel.show_clip(TRACK, clip("text"), tab="audio")
    assert panel.audioTabButton.isChecked()
    assert panel.propertyStack.currentIndex() == EMPTY_PAGE
    assert panel.emptyTitleLabel.text() == "Pas de son sur ce clip"
