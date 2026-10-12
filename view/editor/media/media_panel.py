"""Panneau Médias : import et bibliothèque du projet."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from view.editor.media.media_tile import MediaTile
from view.theme import WHITE, icon
from view.ui_helpers import clickable

COLUMNS = 2


class MediaPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "media_panel.ui", self)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.tiles: list[MediaTile] = []
        self._stretch_row = 0

        self.importButton.setIcon(icon("plus-bold", WHITE))
        clickable(self.importButton)

        self._filters = {
            self.filterAllButton: None,
            self.filterVideoButton: "video",
            self.filterAudioButton: "audio",
            self.filterImageButton: "image",
        }
        for button in self._filters:
            clickable(button)
            button.toggled.connect(self._refresh_grid)

    def set_media(self, media: list[dict]):
        for tile in self.tiles:
            self.mediaGrid.removeWidget(tile)
            tile.deleteLater()
        self.tiles = [MediaTile(item) for item in media]
        self.mediaCountLabel.setText(f"{len(media)} fichiers")
        self._refresh_grid()

    def _refresh_grid(self):
        kind = next((kind for button, kind in self._filters.items() if button.isChecked()), None)
        grid = self.mediaGrid
        for tile in self.tiles:
            grid.removeWidget(tile)
            tile.hide()
        visible = [tile for tile in self.tiles if kind is None or tile.media["kind"] == kind]
        for index, tile in enumerate(visible):
            grid.addWidget(tile, index // COLUMNS, index % COLUMNS, Qt.AlignmentFlag.AlignTop)
            tile.show()
        # la ligne vide sous les vignettes absorbe l'espace restant
        grid.setRowStretch(self._stretch_row, 0)
        self._stretch_row = len(visible) // COLUMNS + 1
        grid.setRowStretch(self._stretch_row, 1)
