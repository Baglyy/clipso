"""Onglet Audio : volume et fondus."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

from view.format import percent, seconds_text
from view.ui_helpers import bind_value_label


class AudioPage(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "audio_page.ui", self)

        bind_value_label(self.audioVolumeSlider, self.audioVolumeValue, percent)
        # les curseurs de fondu comptent en dixièmes de seconde
        bind_value_label(self.audioFadeInSlider, self.audioFadeInValue, lambda v: seconds_text(v / 10))
        bind_value_label(self.audioFadeOutSlider, self.audioFadeOutValue, lambda v: seconds_text(v / 10))

        self.audioVolumeSlider.valueChanged.connect(self.changed)
        self.audioFadeInSlider.valueChanged.connect(self.changed)
        self.audioFadeOutSlider.valueChanged.connect(self.changed)
        self.muteToggle.clicked.connect(self.changed)
        self.normalizeToggle.clicked.connect(self.changed)

    def values(self) -> dict:
        return {
            "volume": self.audioVolumeSlider.value(),
            "fade_in": self.audioFadeInSlider.value() / 10,
            "fade_out": self.audioFadeOutSlider.value() / 10,
            "muted": self.muteToggle.isChecked(),
            "normalize": self.normalizeToggle.isChecked(),
        }

    def set_values(self, values: dict):
        self.blockSignals(True)
        self.audioVolumeSlider.setValue(values["volume"])
        self.audioFadeInSlider.setValue(round(values["fade_in"] * 10))
        self.audioFadeOutSlider.setValue(round(values["fade_out"] * 10))
        self.muteToggle.setChecked(values["muted"])
        self.normalizeToggle.setChecked(values["normalize"])
        self.blockSignals(False)
