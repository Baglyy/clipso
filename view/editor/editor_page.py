"""Page Éditeur : assemble les quatre panneaux et la barre du haut."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import QMenu, QWidget

from view.editor.preview.preview_panel import FPS
from view.theme import ASSETS, WHITE, icon
from view.ui_helpers import clickable, setup_button

Key = QKeySequence.StandardKey


class EditorPage(QWidget):
    home_requested = pyqtSignal()
    export_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi(Path(__file__).parent / "editor_page.ui", self)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.duration = 0.0

        # TODO: projectSavedLabel (« enregistré il y a 1 min ») est figé dans editor_page.ui
        self._setup_top_bar()
        self._setup_menus()
        self.panelsSplitter.setSizes([250, 830, 330])
        self.editorSplitter.setSizes([470, 330])
        self.editorSplitter.setStretchFactor(0, 1)

        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(1000 // FPS)
        self.playback_timer.timeout.connect(lambda: self.seek(self.timeline.position + 1 / FPS))

        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.previewPanel.toggle_play)
        self.previewPanel.play_toggled.connect(self._set_playing)
        self.previewPanel.step_requested.connect(lambda step: self.seek(self.timeline.position + step))
        self.previewPanel.jump_requested.connect(lambda where: self.seek(0 if where == "start" else self.duration))
        self.timeline.position_changed.connect(self._show_position)
        self.timeline.clip_selected.connect(self._on_clip_selected)

    @property
    def timeline(self):
        return self.timelinePanel.timelineView

    def _setup_top_bar(self):
        self.logoButton.setIcon(QIcon(str(ASSETS / "images" / "logo.png")))
        self.logoButton.setIconSize(QSize(34, 34))
        clickable(self.logoButton)
        self.logoButton.clicked.connect(self.home_requested)

        self.projectIconLabel.setPixmap(icon("film-strip").pixmap(18, 18))
        self.renameProjectButton.setIcon(icon("pencil-simple"))
        clickable(self.renameProjectButton)
        setup_button(self.undoButton, "arrow-counter-clockwise", size=22)
        setup_button(self.redoButton, "arrow-clockwise", size=22)
        setup_button(self.helpButton, "question", size=22)

        setup_button(self.exportButton, "caret-double-right-bold", color=WHITE)
        # icône à droite du texte
        self.exportButton.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.exportButton.clicked.connect(self.export_requested)

    def _setup_menus(self):
        zoom = self.timelinePanel
        # TODO: les entrées sans action (None) attendent le controller
        menus = {
            self.fileMenuButton: [
                ("Nouveau projet", Key.New, None),
                ("Ouvrir…", Key.Open, None),
                ("Enregistrer", Key.Save, None),
                None,
                ("Exporter…", "Ctrl+E", self.export_requested.emit),
                None,
                ("Retour à l'accueil", None, self.home_requested.emit),
            ],
            self.editMenuButton: [
                ("Annuler", Key.Undo, None),
                ("Rétablir", Key.Redo, None),
                None,
                ("Couper le clip", "C", None),
                ("Supprimer le clip", Key.Delete, None),
            ],
            self.viewMenuButton: [
                ("Zoom avant", Key.ZoomIn, zoom.zoomInButton.click),
                ("Zoom arrière", Key.ZoomOut, zoom.zoomOutButton.click),
                ("Ajuster la timeline", "Shift+Z", zoom.fitTimelineButton.click),
            ],
        }
        for button, entries in menus.items():
            menu = QMenu(self)
            for entry in entries:
                if entry is None:
                    menu.addSeparator()
                    continue
                label, shortcut, callback = entry
                action = menu.addAction(label)
                if shortcut is not None:
                    if isinstance(shortcut, Key):
                        # raccourci standard : toutes ses variantes (Rétablir = Ctrl+Y et Ctrl+Maj+Z)
                        action.setShortcuts(shortcut)
                    else:
                        action.setShortcut(QKeySequence(shortcut))
                    # un menu fermé ne reçoit pas les raccourcis : on les rattache aussi à la page
                    self.addAction(action)
                if callback is not None:
                    action.triggered.connect(callback)
            button.setMenu(menu)
            clickable(button)

    def load_project(self, name: str, media: list[dict], tracks: list[dict], duration: float, position: float):
        self.duration = duration
        self.projectNameLabel.setText(name)
        self.mediaPanel.set_media(media)
        self.timelinePanel.set_tracks(tracks, duration)
        self.seek(position)

    def select_clip(self, clip: dict, tab: str | None = None):
        track = next(t for t in self.timeline.tracks if any(c is clip for c in t["clips"]))
        self.timeline.select(track, clip)
        if tab:
            self.propertiesPanel.show_clip(track, clip, tab)

    def seek(self, seconds: float):
        self.timeline.set_position(seconds)
        self._show_position(self.timeline.position)
        if self.timeline.position >= self.duration and self.previewPanel.playing:
            self.previewPanel.set_playing(False)
            self._set_playing(False)

    def _set_playing(self, playing: bool):
        if not playing:
            self.playback_timer.stop()
            return
        if self.timeline.position >= self.duration:
            self.seek(0)
        self.playback_timer.start()

    def _show_position(self, seconds: float):
        self.previewPanel.set_time(seconds, self.duration)
        active = {clip["kind"]: clip for _, clip in self.timeline.clips_at(seconds)}
        video = active.get("video")
        image = active.get("image")
        text = active.get("text")
        self.previewPanel.show_frame(
            color=video["color"] if video else "",
            source=video["name"] if video else "",
            text=text["text"] if text else "",
            logo=image is not None,
            logo_selected=image is not None and image is self.timeline.selected,
        )

    def _on_clip_selected(self, track: dict, clip: dict):
        self.propertiesPanel.show_clip(track, clip)
        self._show_position(self.timeline.position)
