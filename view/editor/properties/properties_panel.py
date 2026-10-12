"""Panneau Propriétés : en-tête du clip sélectionné et onglets de réglages.

Chaque onglet est une page à part (text_page, image_page, filters_page, blur_page, audio_page).
"""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QWidget

from view.format import mm_ss, seconds_text
from view.theme import CLIP_COLORS, FAINT, INK, KIND_ICONS, icon, mix
from view.ui_helpers import clickable

TABS = ("text", "image", "filters", "blur", "audio")
TAB_ICONS = {"text": "text-t", "image": "image", "filters": "sliders-horizontal", "blur": "drop", "audio": "waveform"}
EMPTY_PAGE = len(TABS)

AVAILABLE_TABS = {
    "text": {"text"},
    "image": {"image", "filters", "blur"},
    "video": {"filters", "blur", "audio"},
    "audio": {"audio"},
}
DEFAULT_TAB = {"text": "text", "image": "image", "video": "filters", "audio": "audio"}

# onglet indisponible pour le clip : (icône, titre, explication, bouton d'action éventuel)
EMPTY_STATES = {
    # TODO: le texte d'aide cite la piste « Vidéo 2 » en dur
    "text": (
        "text-t",
        "Pas de texte sur ce clip",
        "Ajoutez un titre dans la piste Vidéo 2 pour écrire par-dessus la vidéo.",
        "Ajouter un texte",
    ),
    "image": (
        "image",
        "Pas d'image sur ce clip",
        "Les réglages d'image s'appliquent aux images ajoutées en superposition.",
        None,
    ),
    "filters": (
        "sliders-horizontal",
        "Filtres indisponibles",
        "Les filtres couleur s'appliquent aux vidéos et aux images.",
        None,
    ),
    "blur": ("drop", "Flou indisponible", "Le flou s'applique aux vidéos et aux images.", None),
    "audio": (
        "waveform",
        "Pas de son sur ce clip",
        "Les réglages audio s'appliquent aux vidéos et aux pistes audio.",
        None,
    ),
}


class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "properties_panel.ui", self)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        # TODO: type de clip « image » par défaut ; selectionNameLabel et selectionMetaLabel sont figés dans le .ui
        self.clip_kind = "image"
        self.emptyActionButton.setIcon(icon("plus-bold"))

        self.tab_buttons = {
            "text": self.textTabButton,
            "image": self.imageTabButton,
            "filters": self.filtersTabButton,
            "blur": self.blurTabButton,
            "audio": self.audioTabButton,
        }
        for tab, button in self.tab_buttons.items():
            button.setIconSize(QSize(18, 18))
            clickable(button)
            button.toggled.connect(lambda checked, t=tab: self._on_tab_toggled(t, checked))

    def _on_tab_toggled(self, tab: str, checked: bool):
        if checked:
            self._show_tab(tab)

    def _show_tab(self, tab: str):
        if tab in AVAILABLE_TABS[self.clip_kind]:
            self.propertyStack.setCurrentIndex(TABS.index(tab))
            return
        icon_name, title, text, action = EMPTY_STATES[tab]
        self.emptyIconLabel.setPixmap(icon(icon_name).pixmap(28, 28))
        self.emptyTitleLabel.setText(title)
        self.emptyTextLabel.setText(text)
        self.emptyActionButton.setVisible(action is not None)
        if action:
            self.emptyActionButton.setText(action)
        self.propertyStack.setCurrentIndex(EMPTY_PAGE)

    def show_clip(self, track: dict, clip: dict, tab: str | None = None):
        """Met à jour l'en-tête et les onglets pour le clip sélectionné."""
        kind = clip["kind"]
        self.clip_kind = kind

        if kind == "video":
            background = mix(clip["color"], "#FFFFFF", 0.78).name()
        else:
            background = CLIP_COLORS[kind][0]
        self.selectionIconLabel.setStyleSheet(f"background: {background}; border-radius: 10px;")
        self.selectionIconLabel.setPixmap(icon(KIND_ICONS[kind]).pixmap(20, 20))
        self.selectionNameLabel.setText(clip["name"])
        start, end = clip["start"], clip["start"] + clip["duration"]
        self.selectionMetaLabel.setText(
            f"{track['name']} · {mm_ss(start)} → {mm_ss(end)} · {seconds_text(clip['duration'])}"
        )

        for name, button in self.tab_buttons.items():
            available = name in AVAILABLE_TABS[kind]
            button.setIcon(icon(TAB_ICONS[name], INK if available else FAINT))
            button.setProperty("unavailable", not available)
            # force Qt à réappliquer le QSS, qui dépend de la propriété « unavailable »
            button.style().unpolish(button)
            button.style().polish(button)

        tab = tab or DEFAULT_TAB[kind]
        if self.tab_buttons[tab].isChecked():
            self._show_tab(tab)
        else:
            self.tab_buttons[tab].setChecked(True)
