from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QImage, QPainter

from view.painting import draw_stripes, striped_pixmap, waveform_pixmap


def has_visible_pixel(image: QImage) -> bool:
    return any(image.pixelColor(x, y).alpha() > 0 for x in range(image.width()) for y in range(image.height()))


def test_waveform_size_and_content():
    pixmap = waveform_pixmap(80, 20, "#468A57")
    assert (pixmap.width(), pixmap.height()) == (80, 20)
    assert has_visible_pixel(pixmap.toImage())


def test_waveform_same_seed_same_drawing():
    assert waveform_pixmap(60, 20, "#000000", seed=4).toImage() == waveform_pixmap(60, 20, "#000000", seed=4).toImage()


def test_waveform_different_seed_different_drawing():
    assert waveform_pixmap(60, 20, "#000000", seed=1).toImage() != waveform_pixmap(60, 20, "#000000", seed=2).toImage()


def test_striped_pixmap_is_hidpi():
    pixmap = striped_pixmap(40, 30, "#6B665E", radius=4)
    assert pixmap.devicePixelRatio() == 2
    assert (pixmap.width(), pixmap.height()) == (80, 60)
    assert has_visible_pixel(pixmap.toImage())


def test_draw_stripes_restores_painter():
    image = QImage(50, 30, QImage.Format.Format_ARGB32)
    painter = QPainter(image)
    brush_before = painter.brush()
    draw_stripes(painter, QRectF(0, 0, 50, 30), QColor("#6B665E"), 4)
    assert painter.brush() == brush_before
    assert not painter.hasClipping()
    painter.end()
