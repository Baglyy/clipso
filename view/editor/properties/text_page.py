"""Onglet Texte : contenu, police, taille, couleur, alignement."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

from view.theme import GREEN
from view.ui_helpers import bind_value_label, check_value, checked_value, clickable, setup_button

FONTS = ["Nunito Black", "Nunito", "JetBrains Mono"]


class TextPage(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "text_page.ui", self)

        bind_value_label(self.textSizeSlider, self.textSizeValue, lambda v: f"{v} px")
        self.fontCombo.addItems(FONTS)

        self.colors = {
            self.colorWhiteButton: "#FFFFFF",
            self.colorBlackButton: "#2B2A28",
            self.colorYellowButton: "#F2C24B",
            self.colorOrangeButton: "#EC8866",
            self.colorBlueButton: "#7DB2E0",
            self.colorGreenButton: "#94CF8E",
        }
        for button, color in self.colors.items():
            self._paint_swatch(button, color)

        setup_button(self.alignLeftButton, "text-align-left")
        setup_button(self.alignCenterButton, "text-align-center")
        setup_button(self.alignRightButton, "text-align-right")
        self.aligns = {self.alignLeftButton: "left", self.alignCenterButton: "center", self.alignRightButton: "right"}
        self.animations = {
            self.animationNoneButton: "none",
            self.animationFadeButton: "fade",
            self.animationSlideButton: "slide",
            self.animationZoomButton: "zoom",
        }

        self.textContentEdit.textEdited.connect(self.changed)
        self.fontCombo.currentIndexChanged.connect(self.changed)
        self.textSizeSlider.valueChanged.connect(self.changed)
        for button in [*self.colors, *self.aligns, *self.animations]:
            button.clicked.connect(self.changed)

    @staticmethod
    def _paint_swatch(button, color: str):
        clickable(button)
        border = "#D6D2C9" if color == "#FFFFFF" else color
        button.setStyleSheet(
            f"QToolButton {{ background: {color}; border: 2px solid {border}; border-radius: 15px; }}"
            f"QToolButton:checked {{ border: 3px solid {GREEN}; }}"
        )

    def values(self) -> dict:
        return {
            "text": self.textContentEdit.text(),
            "font": self.fontCombo.currentText(),
            "size": self.textSizeSlider.value(),
            "color": checked_value(self.colors),
            "align": checked_value(self.aligns),
            "animation": checked_value(self.animations),
        }

    def set_values(self, values: dict):
        self.blockSignals(True)
        self.textContentEdit.setText(values["text"])
        self.fontCombo.setCurrentText(values["font"])
        self.textSizeSlider.setValue(values["size"])
        check_value(self.colors, values["color"])
        check_value(self.aligns, values["align"])
        check_value(self.animations, values["animation"])
        self.blockSignals(False)
