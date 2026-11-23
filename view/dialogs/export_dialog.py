"""Fenêtre d'export, affichée par-dessus l'éditeur assombri."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QDialog, QFileDialog, QLineEdit

from view.format import file_size, mm_ss
from view.painting import striped_pixmap
from view.theme import MUTED, WHITE, icon
from view.ui_helpers import checked_value, clickable, setup_button

QUALITY_NAMES = ((40, "Basse"), (70, "Moyenne"), (90, "Haute"), (101, "Maximale"))


class ExportDialog(QDialog):
    settings_changed = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "export_dialog.ui", self)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.exportCard.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

        setup_button(self.closeButton, "x-bold")
        setup_button(self.confirmExportButton, "caret-double-right-bold", color=WHITE)
        clickable(self.cancelButton, self.browseButton)
        self.closeButton.clicked.connect(self.reject)
        self.cancelButton.clicked.connect(self.reject)
        self.confirmExportButton.clicked.connect(self.accept)

        thumb_size = self.summaryThumbLabel.size()
        self.summaryThumbLabel.setPixmap(striped_pixmap(thumb_size.width(), thumb_size.height(), "#5B7898", 8))
        self.folderEdit.addAction(icon("folder-simple", MUTED), QLineEdit.ActionPosition.LeadingPosition)
        self.browseButton.clicked.connect(self._browse)
        self.qualitySlider.valueChanged.connect(self._update_quality)
        self._update_quality(self.qualitySlider.value())

        self.formats = {
            self.formatMp4Button: "mp4",
            self.formatMovButton: "mov",
            self.formatWebmButton: "webm",
            self.formatGifButton: "gif",
        }
        self.resolutions = {self.resolution720Button: 720, self.resolution1080Button: 1080}
        self.frame_rates = {self.fps24Button: 24, self.fps30Button: 30, self.fps60Button: 60}
        for button in [*self.formats, *self.resolutions, *self.frame_rates]:
            button.clicked.connect(self.settings_changed)
        self.qualitySlider.valueChanged.connect(self.settings_changed)

    def set_project(self, name: str, duration: float, aspect: str, resolution: int, fps: int, folder: str):
        self.summaryNameLabel.setText(name)
        self.summaryMetaLabel.setText(f"{mm_ss(duration)} · {aspect} · {resolution}p · {fps} ips")
        self.fileNameEdit.setText(name)
        self.folderEdit.setText(folder)

    def set_estimated_size(self, size: int | None):
        if size is None:
            self.summarySizeLabel.setText("Taille estimée : calcul…")
        else:
            self.summarySizeLabel.setText(f"Taille estimée ≈ {file_size(size)}")

    def set_thumbnail(self, image: QImage):
        size = self.summaryThumbLabel.size()
        pixmap = QPixmap.fromImage(image).scaled(
            size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.summaryThumbLabel.setPixmap(pixmap)
        self.summaryThumbLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def settings(self) -> dict:
        return {
            "folder": self.folderEdit.text(),
            "file_name": self.fileNameEdit.text(),
            "format": checked_value(self.formats),
            "resolution": checked_value(self.resolutions),
            "fps": checked_value(self.frame_rates),
            "quality": self.qualitySlider.value(),
        }

    def _update_quality(self, value: int):
        name = next(label for limit, label in QUALITY_NAMES if value < limit)
        self.qualityValue.setText(f"{name} · {value} %")

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Dossier d'export")
        if folder:
            self.folderEdit.setText(folder)

    def showEvent(self, event):
        """Recouvre toute la fenêtre parente pour l'assombrir."""
        self.setGeometry(self.parent().window().geometry())
        super().showEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(43, 42, 40, 110))
