import pytest
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QImage

from view.editor.preview.video_view import DEFAULT_ASPECT, VideoView


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
    assert frame.width() / frame.height() == pytest.approx(DEFAULT_ASPECT)


@pytest.mark.parametrize(
    ("aspect", "expected"), [(9 / 16, QRectF(219.0625, 0, 151.875, 270)), (1, QRectF(160, 0, 270, 270))]
)
def test_frame_rect_follows_project_aspect(view, aspect, expected):
    view.resize(590, 270)
    view.set_aspect(aspect)
    assert view.frame_rect() == expected


def test_show_image_and_selection_are_stored(view):
    image = QImage(16, 9, QImage.Format.Format_RGB888)
    view.show_image(image)
    view.set_selection(QRectF(0.1, 0.1, 0.2, 0.2))
    assert view._image is image
    assert view._selection == QRectF(0.1, 0.1, 0.2, 0.2)


def test_image_is_drawn_in_frame(qtbot, view):
    view.resize(640, 360)
    image = QImage(64, 36, QImage.Format.Format_RGB888)
    image.fill(QColor("red"))
    view.show_image(image)
    screenshot = view.grab().toImage()
    assert screenshot.pixelColor(320, 180) == QColor("red")


@pytest.mark.parametrize(
    ("image", "selection"),
    [
        (QImage(16, 9, QImage.Format.Format_RGB888), QRectF(0.4, 0.4, 0.2, 0.2)),
        (QImage(16, 9, QImage.Format.Format_RGB888), None),
        (None, None),  # pas encore d'image : fond uni
    ],
)
def test_paint_event_does_not_crash(qtbot, view, image, selection):
    view.show()
    qtbot.waitExposed(view)
    view.show_image(image)
    view.set_selection(selection)
    view.repaint()
