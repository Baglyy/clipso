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
