"""Onglet Audio : volume et fondus."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget

from view.format import percent, seconds_text
from view.ui_helpers import bind_value_label


class AudioPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "audio_page.ui", self)

        bind_value_label(self.audioVolumeSlider, self.audioVolumeValue, percent)
        # les curseurs de fondu comptent en dixièmes de seconde
        bind_value_label(self.audioFadeInSlider, self.audioFadeInValue, lambda v: seconds_text(v / 10))
        bind_value_label(self.audioFadeOutSlider, self.audioFadeOutValue, lambda v: seconds_text(v / 10))
