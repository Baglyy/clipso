"""Dessins partagés : formes d'onde et fonds rayés."""

import random

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap, QPolygonF


def waveform_pixmap(width: int, height: int, color: str, bars: int = 40, seed: int = 1) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_waveform(painter, QRectF(0, 0, width, height), QColor(color), bars, seed)
    painter.end()
    return pixmap


def striped_pixmap(width: int, height: int, color: str, radius: int) -> QPixmap:
    """Vignette rayée en haute densité (2x) pour rester nette sur les écrans HiDPI."""
    pixmap = QPixmap(width * 2, height * 2)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_stripes(painter, QRectF(0, 0, width, height), QColor(color), radius)
    painter.end()
    return pixmap


# TODO: forme d'onde aléatoire, à remplacer par celle calculée depuis l'audio
def draw_waveform(painter: QPainter, rect: QRectF, color: QColor, bars: int, seed: int = 1):
    rng = random.Random(seed)
    step = rect.width() / bars
    bar_width = max(1.5, step * 0.55)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    for i in range(bars):
        level = 0.25 + 0.75 * abs(rng.gauss(0.45, 0.3))
        bar_height = min(rect.height(), rect.height() * level)
        x = rect.left() + i * step + (step - bar_width) / 2
        y = rect.center().y() - bar_height / 2
        painter.drawRoundedRect(QRectF(x, y, bar_width, bar_height), bar_width / 2, bar_width / 2)


def draw_stripes(painter: QPainter, rect: QRectF, color: QColor, radius: float):
    """Fond rayé qui remplace les images tant qu'aucune vidéo n'est décodée."""
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawRoundedRect(rect, radius, radius)
    painter.setClipRect(rect)
    painter.setBrush(QColor(255, 255, 255, 22))
    step = 26
    h = rect.height()
    x = rect.left() - h
    while x < rect.right():
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(x, rect.bottom()),
                    QPointF(x + 11, rect.bottom()),
                    QPointF(x + 11 + h, rect.top()),
                    QPointF(x + h, rect.top()),
                ]
            )
        )
        x += step
    painter.restore()
