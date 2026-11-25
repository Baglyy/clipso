"""Onglet Flou : type, intensité, bords."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

from view.format import percent
from view.ui_helpers import bind_value_label, check_value, checked_value


class BlurPage(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "blur_page.ui", self)

        bind_value_label(self.blurIntensitySlider, self.blurIntensityValue, percent)
        bind_value_label(self.blurFeatherSlider, self.blurFeatherValue, percent)
        self.kinds = {
            self.blurGaussianButton: "gaussian",
            self.blurMotionButton: "motion",
            self.blurRadialButton: "radial",
        }

        self.blurFeatherSlider.setEnabled(False)
        self.blurBackgroundToggle.toggled.connect(self.blurFeatherSlider.setEnabled)

        self.blurIntensitySlider.valueChanged.connect(self.changed)
        self.blurFeatherSlider.valueChanged.connect(self.changed)
        self.blurBackgroundToggle.clicked.connect(self.changed)
        for button in self.kinds:
            button.clicked.connect(self.changed)

    def values(self) -> dict:
        return {
            "kind": checked_value(self.kinds),
            "intensity": self.blurIntensitySlider.value(),
            "feather": self.blurFeatherSlider.value(),
            "background": self.blurBackgroundToggle.isChecked(),
        }

    def set_values(self, values: dict):
        self.blockSignals(True)
        check_value(self.kinds, values["kind"])
        self.blurIntensitySlider.setValue(values["intensity"])
        self.blurFeatherSlider.setValue(values["feather"])
        self.blurBackgroundToggle.setChecked(values["background"])
        self.blockSignals(False)
