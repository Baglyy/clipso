"""Fenêtre d'export, affichée par-dessus l'éditeur assombri."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QDialog, QFileDialog, QLineEdit

from view.painting import striped_pixmap
from view.theme import MUTED, WHITE, icon
from view.ui_helpers import clickable, setup_button

QUALITY_NAMES = ((40, "Basse"), (70, "Moyenne"), (90, "Haute"), (101, "Maximale"))


class ExportDialog(QDialog):
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

        # TODO: miniature de couleur fixe ; summaryNameLabel, summaryMetaLabel, summarySizeLabel, fileNameEdit
        # et folderEdit (« Vacances à Biarritz », « ≈ 65 Mo », « ~/Vidéos/Clipso »…) sont figés dans export_dialog.ui
        thumb_size = self.summaryThumbLabel.size()
        self.summaryThumbLabel.setPixmap(striped_pixmap(thumb_size.width(), thumb_size.height(), "#5B7898", 8))
        self.folderEdit.addAction(icon("folder-simple", MUTED), QLineEdit.ActionPosition.LeadingPosition)
        self.browseButton.clicked.connect(self._browse)
        self.qualitySlider.valueChanged.connect(self._update_quality)
        self._update_quality(self.qualitySlider.value())

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
