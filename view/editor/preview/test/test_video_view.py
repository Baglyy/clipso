import pytest
from PyQt6.QtCore import QRectF

from view.editor.preview.video_view import ASPECT, VideoView


@pytest.fixture
def view(qtbot):
    widget = VideoView()
    qtbot.addWidget(widget)
    return widget


def test_minimum_size(view):
    assert (view.minimumWidth(), view.minimumHeight()) == (320, 180)


@pytest.mark.parametrize(
    ("width", "height", "expected"),
    [
        (640, 360, QRectF(0, 0, 640, 360)),  # pile au bon format
        (800, 360, QRectF(80, 0, 640, 360)),  # trop large : bandes à gauche et à droite
        (640, 500, QRectF(0, 70, 640, 360)),  # trop haut : bandes en haut et en bas
    ],
)
def test_frame_rect_keeps_16_9_centered(view, width, height, expected):
    view.resize(width, height)
    frame = view.frame_rect()
    assert frame == expected
    assert frame.width() / frame.height() == pytest.approx(ASPECT)


def test_show_frame_stores_layers(view):
    view.show_frame(color="#468A57", source="plage.mp4", text="Salut", logo=True, logo_selected=False)
    assert view._color == "#468A57"
    assert view._source == "plage.mp4"
    assert view._text == "Salut"
    assert view._logo
    assert not view._logo_selected


def test_show_frame_defaults(view):
    view.show_frame(color="#468A57", source="plage.mp4")
    assert view._text == ""
    assert not view._logo
    assert not view._logo_selected


@pytest.mark.parametrize(
    "layers",
    [
        {"color": "#AE7657", "source": "plage.mp4", "text": "Titre", "logo": True, "logo_selected": True},
        {"color": "#AE7657", "source": "plage.mp4", "logo": True, "logo_selected": False},
        {"color": "", "source": ""},  # aucune image : fond uni
    ],
)
def test_paint_event_does_not_crash(qtbot, view, layers):
    view.show()
    qtbot.waitExposed(view)
    view.show_frame(**layers)
    view.repaint()
