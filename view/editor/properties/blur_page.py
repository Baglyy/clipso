"""Onglet Flou : type, intensité, bords."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget

from view.format import percent
from view.ui_helpers import bind_value_label


class BlurPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "blur_page.ui", self)

        bind_value_label(self.blurIntensitySlider, self.blurIntensityValue, percent)
        bind_value_label(self.blurFeatherSlider, self.blurFeatherValue, percent)
