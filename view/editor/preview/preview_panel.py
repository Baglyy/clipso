"""Panneau Aperçu : image courante et contrôles de lecture."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QMenu, QWidget

from view.format import timecode
from view.theme import WHITE, icon
from view.ui_helpers import clickable, setup_button

# TODO: 30 ips en dur, à lire depuis le projet
FPS = 30


class PreviewPanel(QWidget):
    play_toggled = pyqtSignal(bool)
    step_requested = pyqtSignal(float)
    jump_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "preview_panel.ui", self)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.playing = False
        # TODO: previewInfoLabel (« 16:9 · 1080p · 30 ips ») est figé dans preview_panel.ui

        setup_button(self.skipStartButton, "skip-back-fill", size=20)
        setup_button(self.previousFrameButton, "caret-left-bold", size=20)
        setup_button(self.nextFrameButton, "caret-right-bold", size=20)
        setup_button(self.skipEndButton, "skip-forward-fill", size=20)
        setup_button(self.volumeButton, "speaker-high", size=20)
        setup_button(self.fullscreenButton, "corners-out", size=20)
        self.playButton.setIconSize(QSize(22, 22))
        clickable(self.playButton)
        self._update_play_icon()

        setup_button(self.fitPreviewButton, "caret-down-bold", size=12)
        fit_menu = QMenu(self)
        for label in ("Ajuster", "50 %", "100 %", "200 %"):
            fit_menu.addAction(label, lambda text=label: self.fitPreviewButton.setText(text))
        self.fitPreviewButton.setMenu(fit_menu)

        self.volumeButton.setCheckable(True)
        self.volumeButton.toggled.connect(
            lambda muted: self.volumeButton.setIcon(icon("speaker-x" if muted else "speaker-high"))
        )

        self.playButton.clicked.connect(self.toggle_play)
        self.previousFrameButton.clicked.connect(lambda: self.step_requested.emit(-1 / FPS))
        self.nextFrameButton.clicked.connect(lambda: self.step_requested.emit(1 / FPS))
        self.skipStartButton.clicked.connect(lambda: self.jump_requested.emit("start"))
        self.skipEndButton.clicked.connect(lambda: self.jump_requested.emit("end"))

    def toggle_play(self):
        self.set_playing(not self.playing)
        self.play_toggled.emit(self.playing)

    def set_playing(self, playing: bool):
        self.playing = playing
        self._update_play_icon()

    def _update_play_icon(self):
        self.playButton.setIcon(icon("pause-fill" if self.playing else "play-fill", WHITE))
        self.playButton.setToolTip("Pause (Espace)" if self.playing else "Lecture (Espace)")

    def set_time(self, position: float, duration: float):
        self.timecodeLabel.setText(f"{timecode(position, FPS)} / {timecode(duration, FPS)}")

    def show_frame(self, **layers):
        """Transmet l'image à afficher à la zone vidéo (voir VideoView.show_frame)."""
        self.videoView.show_frame(**layers)
