"""Onglet Image : position, échelle, opacité, rotation, fusion."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget

from view.format import percent
from view.painting import striped_pixmap
from view.ui_helpers import bind_value_label

BLEND_MODES = ["Fusion : Normal", "Fusion : Produit", "Fusion : Écran", "Fusion : Incrustation"]


class ImagePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "image_page.ui", self)

        bind_value_label(self.imageScaleSlider, self.imageScaleValue, percent)
        bind_value_label(self.imageOpacitySlider, self.imageOpacityValue, percent)
        bind_value_label(self.imageRotationSlider, self.imageRotationValue, lambda v: f"{v}°")
        self.blendCombo.addItems(BLEND_MODES)

        # TODO: vignette rayée de couleur fixe au lieu de l'image du clip ; imageNameLabel et imageInfoLabel
        # (« logo_club.png », « PNG · 800 × 800 ») sont figés dans image_page.ui
        self.imageThumbLabel.setPixmap(striped_pixmap(44, 44, "#E3C3D3", 10))
