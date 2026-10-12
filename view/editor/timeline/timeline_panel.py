"""Panneau Timeline : barre d'outils, en-têtes de pistes et timeline."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QWidget

from view.editor.timeline.timeline_view import RULER_HEIGHT, TRACK_GAP, TRACK_HEIGHTS
from view.editor.timeline.track_header import TrackHeader
from view.theme import INK, WHITE, icon
from view.ui_helpers import clickable, setup_button

ZOOM_STEP = 50


class TimelinePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "timeline_panel.ui", self)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.headers: list[TrackHeader] = []

        setup_button(self.timelineUndoButton, "arrow-counter-clockwise")
        setup_button(self.timelineRedoButton, "arrow-clockwise")
        setup_button(self.cutButton, "scissors")
        setup_button(self.deleteButton, "trash")
        setup_button(self.zoomOutButton, "magnifying-glass-minus")
        setup_button(self.zoomInButton, "magnifying-glass-plus")
        setup_button(self.fitTimelineButton, "arrows-out-line-horizontal")
        setup_button(self.addTrackButton, "plus", size=14)
        self.selectionIcon.setPixmap(icon("cursor").pixmap(16, 16))

        self.magnetButton.setIconSize(QSize(18, 18))
        clickable(self.magnetButton)
        self.magnetButton.toggled.connect(self._update_magnet_icon)
        self._update_magnet_icon(self.magnetButton.isChecked())

        self.zoomSlider.valueChanged.connect(lambda v: self.timelineView.set_zoom(v / 100))
        self.zoomInButton.clicked.connect(lambda: self.zoomSlider.setValue(self.zoomSlider.value() + ZOOM_STEP))
        self.zoomOutButton.clicked.connect(lambda: self.zoomSlider.setValue(self.zoomSlider.value() - ZOOM_STEP))
        self.fitTimelineButton.clicked.connect(lambda: self.zoomSlider.setValue(100))
        self.timelineView.content_width_changed.connect(self._update_scrollbar)
        self.timelineScrollBar.valueChanged.connect(self.timelineView.set_offset)
        self.timelineView.clip_selected.connect(lambda track, clip: self.timelineSelectionLabel.setText(clip["name"]))

    def _update_magnet_icon(self, checked: bool):
        self.magnetButton.setIcon(icon("magnet", WHITE if checked else INK))

    def _update_scrollbar(self, content_width: int):
        overflow = max(0, content_width - self.timelineView.width())
        self.timelineScrollBar.setRange(0, overflow)
        self.timelineScrollBar.setPageStep(self.timelineView.width())
        self.timelineScrollBar.setEnabled(overflow > 0)

    def set_tracks(self, tracks: list[dict], duration: float):
        layout = self.trackHeadersLayout
        self.addTrackButton.setFixedHeight(RULER_HEIGHT)
        layout.setSpacing(TRACK_GAP)
        # vide les en-têtes du projet précédent, en gardant le bouton « Ajouter une piste » en tête
        while layout.count() > 1:
            item = layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        self.headers = []
        for track in tracks:
            header = TrackHeader(track, TRACK_HEIGHTS[track["kind"]])
            layout.addWidget(header)
            self.headers.append(header)
        layout.addStretch()
        self.timelineView.set_tracks(tracks, duration)
