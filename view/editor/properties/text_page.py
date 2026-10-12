"""Onglet Texte : contenu, police, taille, couleur, alignement."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget

from view.theme import GREEN
from view.ui_helpers import bind_value_label, clickable, setup_button

FONTS = ["Nunito Black", "Nunito", "JetBrains Mono"]


class TextPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "text_page.ui", self)

        # TODO: textContentEdit (« Été 2026 ») est figé dans text_page.ui
        bind_value_label(self.textSizeSlider, self.textSizeValue, lambda v: f"{v} px")
        self.fontCombo.addItems(FONTS)

        swatches = {
            self.colorWhiteButton: "#FFFFFF",
            self.colorBlackButton: "#2B2A28",
            self.colorYellowButton: "#F2C24B",
            self.colorOrangeButton: "#EC8866",
            self.colorBlueButton: "#7DB2E0",
            self.colorGreenButton: "#94CF8E",
        }
        for button, color in swatches.items():
            self._paint_swatch(button, color)

        setup_button(self.alignLeftButton, "text-align-left")
        setup_button(self.alignCenterButton, "text-align-center")
        setup_button(self.alignRightButton, "text-align-right")

    @staticmethod
    def _paint_swatch(button, color: str):
        clickable(button)
        border = "#D6D2C9" if color == "#FFFFFF" else color
        button.setStyleSheet(
            f"QToolButton {{ background: {color}; border: 2px solid {border}; border-radius: 15px; }}"
            f"QToolButton:checked {{ border: 3px solid {GREEN}; }}"
        )
