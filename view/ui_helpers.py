"""Réglages répétitifs des widgets : icône, curseur main, valeur affichée à côté d'un curseur."""

from collections.abc import Callable

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QAbstractButton, QLabel, QSlider, QWidget

from view.theme import INK, icon


def clickable(*widgets: QWidget):
    """Curseur « main » au survol."""
    for widget in widgets:
        widget.setCursor(Qt.CursorShape.PointingHandCursor)


def setup_button(button: QAbstractButton, icon_name: str, size: int = 18, color: str = INK):
    button.setIcon(icon(icon_name, color))
    button.setIconSize(QSize(size, size))
    clickable(button)


def bind_value_label(slider: QSlider, label: QLabel, fmt: Callable[[int], str]):
    """Affiche la valeur du curseur dans le label, mise en forme par fmt."""
    slider.valueChanged.connect(lambda value: label.setText(fmt(value)))
    clickable(slider)
