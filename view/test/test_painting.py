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


def test_waveform_with_peaks():
    from view.painting import _resample, draw_waveform

    assert _resample([0.1, 0.9, 0.2, 0.3], 2) == [0.9, 0.3]
    assert _resample([0.5], 3) == [0.5, 0.5, 0.5]
    image = QImage(40, 20, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    draw_waveform(painter, QRectF(0, 0, 40, 20), QColor("#000000"), 4, peaks=[0.0, 0.0, 1.0, 1.0])
    painter.end()
    # la barre du début (silence) est plus petite que celle de la fin
    assert image.pixelColor(4, 2).alpha() == 0
    assert image.pixelColor(34, 2).alpha() > 0


def test_draw_image_fills_rect():
    from view.painting import draw_image

    source = QImage(10, 10, QImage.Format.Format_RGB888)
    source.fill(QColor("#0000FF"))
    image = QImage(40, 20, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    draw_image(painter, QRectF(0, 0, 40, 20), source, 0)
    painter.end()
    assert image.pixelColor(20, 10).blue() == 255
    assert image.pixelColor(1, 1).blue() == 255
