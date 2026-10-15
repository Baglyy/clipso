"""Interrupteur on/off (une QCheckBox dessinée à la main)."""

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QCheckBox

from view.theme import GREEN, WHITE

TRACK_OFF = "#D6D2C9"


class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(40, 22)

    def sizeHint(self):
        return QSize(40, 22)

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(GREEN if self.isChecked() else TRACK_OFF))
        painter.drawRoundedRect(QRectF(self.rect()), 11, 11)
        knob_x = self.width() - 20 if self.isChecked() else 2
        painter.setBrush(QColor(WHITE))
        painter.drawEllipse(QRectF(knob_x, 2, 18, 18))
