"""Onglet Image : position, échelle, opacité, rotation, fusion."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QWidget

from view.format import percent
from view.painting import striped_pixmap
from view.ui_helpers import bind_value_label

BLEND_MODES = ["Fusion : Normal", "Fusion : Produit", "Fusion : Écran", "Fusion : Incrustation"]
BLEND_VALUES = ["normal", "multiply", "screen", "overlay"]


class ImagePage(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent / "image_page.ui", self)

        bind_value_label(self.imageScaleSlider, self.imageScaleValue, percent)
        bind_value_label(self.imageOpacitySlider, self.imageOpacityValue, percent)
        bind_value_label(self.imageRotationSlider, self.imageRotationValue, lambda v: f"{v}°")
        self.blendCombo.addItems(BLEND_MODES)
        self.imageThumbLabel.setPixmap(striped_pixmap(44, 44, "#E3C3D3", 10))

        for widget in (
            self.imageXFieldSpin,
            self.imageYFieldSpin,
            self.imageScaleSlider,
            self.imageOpacitySlider,
            self.imageRotationSlider,
        ):
            widget.valueChanged.connect(self.changed)
        self.blendCombo.currentIndexChanged.connect(self.changed)

    def set_image(self, name: str, info: str, thumbnail: QImage | None):
        self.imageNameLabel.setText(name)
        self.imageInfoLabel.setText(info)
        if thumbnail is not None:
            pixmap = QPixmap.fromImage(thumbnail).scaled(
                44, 44, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
            )
            # on garde le carré du milieu
            x = (pixmap.width() - 44) // 2
            y = (pixmap.height() - 44) // 2
            self.imageThumbLabel.setPixmap(pixmap.copy(x, y, 44, 44))

    def values(self) -> dict:
        return {
            "x": self.imageXFieldSpin.value(),
            "y": self.imageYFieldSpin.value(),
            "scale": self.imageScaleSlider.value(),
            "opacity": self.imageOpacitySlider.value(),
            "rotation": self.imageRotationSlider.value(),
            "blend": BLEND_VALUES[self.blendCombo.currentIndex()],
        }

    def set_values(self, values: dict):
        self.blockSignals(True)
        self.imageXFieldSpin.setValue(values["x"])
        self.imageYFieldSpin.setValue(values["y"])
        self.imageScaleSlider.setValue(values["scale"])
        self.imageOpacitySlider.setValue(values["opacity"])
        self.imageRotationSlider.setValue(values["rotation"])
        self.blendCombo.setCurrentIndex(BLEND_VALUES.index(values["blend"]))
        self.blockSignals(False)
