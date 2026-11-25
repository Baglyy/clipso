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
    position_shown = pyqtSignal(float)
    # aussi émis quand on saute ailleurs pendant la lecture
    playback_started = pyqtSignal(float)
    playback_stopped = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi(Path(__file__).parent / "editor_page.ui", self)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.duration = 0.0
        # fonction qui donne la position de lecture (fournie par le controller)
        self.playback_clock = None

        # TODO: projectSavedLabel (« enregistré il y a 1 min ») est figé dans editor_page.ui
        self._setup_top_bar()
        self._setup_menus()
        self.panelsSplitter.setSizes([250, 830, 330])
        self.editorSplitter.setSizes([470, 330])
        self.editorSplitter.setStretchFactor(0, 1)

        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(1000 // FPS)
        self.playback_timer.timeout.connect(self._advance)

        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.previewPanel.toggle_play)
        self.previewPanel.play_toggled.connect(self._set_playing)
        self.previewPanel.step_requested.connect(lambda step: self._jump(self.timeline.position + step))
        self.previewPanel.jump_requested.connect(lambda where: self._jump(0 if where == "start" else self.duration))
        self.timeline.position_changed.connect(self._on_scrub)
        self.timeline.clip_selected.connect(self._on_clip_selected)

    @property
    def timeline(self):
        return self.timelinePanel.timelineView

    def _setup_top_bar(self):
        self.logoButton.setIcon(QIcon(str(ASSETS / "images" / "logo.png")))
        self.logoButton.setIconSize(QSize(34, 34))
        clickable(self.logoButton)
        self.logoButton.clicked.connect(self.home_requested)
        self.home_requested.connect(self.pause)

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
            self.pause()

    def pause(self):
        if self.previewPanel.playing:
            self.previewPanel.set_playing(False)
            self._set_playing(False)

    def _advance(self):
        if self.playback_clock is not None:
            self.seek(self.playback_clock())
        else:
            self.seek(self.timeline.position + 1 / FPS)

    def _jump(self, seconds: float):
        self.seek(seconds)
        self._restart_playback()

    def _on_scrub(self, seconds: float):
        self._show_position(seconds)
        self._restart_playback()

    def _restart_playback(self):
        if self.playback_timer.isActive():
            self.playback_started.emit(self.timeline.position)

    def _set_playing(self, playing: bool):
        if not playing:
            self.playback_timer.stop()
            self.playback_stopped.emit()
            return
        if self.timeline.position >= self.duration:
            self.seek(0)
        self.playback_timer.start()
        self.playback_started.emit(self.timeline.position)

    def _show_position(self, seconds: float):
        self.previewPanel.set_time(seconds, self.duration)
        self.position_shown.emit(seconds)

    def _on_clip_selected(self, track: dict, clip: dict):
        self.propertiesPanel.show_clip(track, clip)
