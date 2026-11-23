import pytest

from view.editor.properties.image_page import BLEND_MODES, ImagePage


@pytest.fixture
def page(qtbot):
    widget = ImagePage()
    qtbot.addWidget(widget)
    return widget


@pytest.mark.parametrize(
    ("slider_name", "label_name", "value", "expected"),
    [
        ("imageScaleSlider", "imageScaleValue", 120, "120 %"),
        ("imageOpacitySlider", "imageOpacityValue", 45, "45 %"),
        ("imageRotationSlider", "imageRotationValue", -90, "-90°"),
    ],
)
def test_label_follows_slider(page, slider_name, label_name, value, expected):
    getattr(page, slider_name).setValue(value)
    assert getattr(page, label_name).text() == expected


def test_blend_modes(page):
    assert [page.blendCombo.itemText(i) for i in range(page.blendCombo.count())] == BLEND_MODES


def test_thumbnail_loaded(page):
    assert not page.imageThumbLabel.pixmap().isNull()


IMAGE_VALUES = {"x": 10, "y": 90, "scale": 150, "opacity": 40, "rotation": -45, "blend": "screen"}


def test_set_values_then_values(page, qtbot):
    with qtbot.assertNotEmitted(page.changed):
        page.set_values(IMAGE_VALUES)
    assert page.values() == IMAGE_VALUES
    assert page.blendCombo.currentText() == BLEND_MODES[2]


def test_user_changes_emit_changed(page, qtbot):
    with qtbot.waitSignal(page.changed):
        page.imageXFieldSpin.setValue(20)
    with qtbot.waitSignal(page.changed):
        page.blendCombo.setCurrentIndex(1)


def test_set_image(page):
    from PyQt6.QtGui import QImage

    image = QImage(80, 40, QImage.Format.Format_RGB888)
    page.set_image("logo.png", "PNG · 80 × 40", image)
    assert page.imageNameLabel.text() == "logo.png"
    assert page.imageInfoLabel.text() == "PNG · 80 × 40"
    assert page.imageThumbLabel.pixmap().width() == 44
