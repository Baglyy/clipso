"""Onglet Filtres : préréglages et réglages couleur."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QToolButton, QVBoxLayout, QWidget

from view.format import signed
from view.theme import GREEN, mix
from view.ui_helpers import bind_value_label, clickable, setup_button


class FiltersPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "filters_page.ui", self)

        self.sliders = {
            self.brightnessSlider: self.brightnessValue,
            self.contrastSlider: self.contrastValue,
            self.saturationSlider: self.saturationValue,
            self.temperatureSlider: self.temperatureValue,
        }
        for slider, label in self.sliders.items():
            bind_value_label(slider, label, signed)

        presets = {
            self.presetOriginalButton: ("Original", "#BCC7D5"),
            self.presetWarmButton: ("Chaud", "#E8C9A6"),
            self.presetCoolButton: ("Froid", "#B9CEDD"),
            self.presetMonoButton: ("N&B", "#B8B6B1"),
            self.presetVintageButton: ("Vintage", "#D9C7A8"),
            self.presetPastelButton: ("Pastel", "#E6D2DF"),
        }
        for button, (title, color) in presets.items():
            self._decorate_preset(button, title, color)

        setup_button(self.resetFiltersButton, "arrow-counter-clockwise-bold", size=14)
        self.resetFiltersButton.clicked.connect(self.reset)

    def reset(self):
        for slider in self.sliders:
            slider.setValue(0)
        self.presetOriginalButton.setChecked(True)

    @staticmethod
    def _decorate_preset(button: QToolButton, title: str, color: str):
        """Pastille de couleur + nom, dessinés à l'intérieur du bouton."""
        clickable(button)
        layout = QVBoxLayout(button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        swatch = QLabel()
        swatch.setFixedHeight(46)
        name = QLabel(title)
        name.setObjectName("presetName")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for label in (swatch, name):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(swatch)
        layout.addWidget(name)

        def refresh(checked: bool):
            border = GREEN if checked else mix(color, "#000000", 0.08).name()
            swatch.setStyleSheet(f"border: 2px solid {border}; border-radius: 10px; background: {color};")

        button.toggled.connect(refresh)
        refresh(button.isChecked())
