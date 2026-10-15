"""Couleurs, icônes et chemins partagés par toutes les vues."""

from pathlib import Path

import qtawesome as qta
from PyQt6.QtGui import QColor, QIcon

from view.painting import waveform_pixmap

ASSETS = Path(__file__).resolve().parent.parent / "assets"

INK = "#2B2A28"
MUTED = "#6B665E"
FAINT = "#A8A39A"
WHITE = "#FFFFFF"
GREEN = "#468A57"
PAGE = "#F6F4EF"
PANEL = "#ECE9E3"
SUBTLE = "#E0DDD6"
ROW = "#E5E2DB"

# couleurs des clips par type : (fond, bordure, accent)
CLIP_COLORS = {
    "text": ("#F2E7C7", "#D5BC76", "#8A6D1F"),
    "image": ("#F0E0E8", "#D9B8C8", "#9A5C7A"),
    "audio": ("#E5E1F1", "#C9C0E0", "#8E82B6"),
}

KIND_ICONS = {
    "video": "film-strip",
    "audio": "waveform",
    "image": "image",
    "text": "text-t",
    "overlay": "stack",
}


def icon(name: str, color: str = INK) -> QIcon:
    """Icône Phosphor."""
    if name == "waveform":
        return QIcon(waveform_pixmap(48, 48, color, bars=7, seed=3))
    return qta.icon("ph." + name, color=color)


def mix(color: str, other: str, amount: float) -> QColor:
    """Mélange deux couleurs."""
    a, b = QColor(color), QColor(other)
    return QColor(
        round(a.red() + (b.red() - a.red()) * amount),
        round(a.green() + (b.green() - a.green()) * amount),
        round(a.blue() + (b.blue() - a.blue()) * amount),
    )
