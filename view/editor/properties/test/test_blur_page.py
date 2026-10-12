import pytest
from PyQt6.QtCore import Qt

from view.editor.properties.blur_page import BlurPage


@pytest.fixture
def page(qtbot):
    widget = BlurPage()
    qtbot.addWidget(widget)
    return widget


@pytest.mark.parametrize(
    ("slider_name", "label_name"),
    [("blurIntensitySlider", "blurIntensityValue"), ("blurFeatherSlider", "blurFeatherValue")],
)
def test_label_follows_slider(page, slider_name, label_name):
    getattr(page, slider_name).setValue(42)
    assert getattr(page, label_name).text() == "42 %"


def test_only_one_blur_type_checked(qtbot, page):
    assert page.blurGaussianButton.isChecked()
    qtbot.mouseClick(page.blurRadialButton, Qt.MouseButton.LeftButton)
    assert page.blurRadialButton.isChecked()
    assert not page.blurGaussianButton.isChecked()
    assert not page.blurMotionButton.isChecked()
