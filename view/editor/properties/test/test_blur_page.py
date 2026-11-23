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


BLUR_VALUES = {"kind": "motion", "intensity": 70, "feather": 10, "background": True}


def test_set_values_then_values(page, qtbot):
    with qtbot.assertNotEmitted(page.changed):
        page.set_values(BLUR_VALUES)
    assert page.values() == BLUR_VALUES


def test_user_changes_emit_changed(page, qtbot):
    with qtbot.waitSignal(page.changed):
        page.blurIntensitySlider.setValue(50)
    with qtbot.waitSignal(page.changed):
        qtbot.mouseClick(page.blurBackgroundToggle, Qt.MouseButton.LeftButton)


def test_feather_only_with_background(page):
    assert not page.blurFeatherSlider.isEnabled()
    page.set_values({"kind": "gaussian", "intensity": 10, "feather": 20, "background": True})
    assert page.blurFeatherSlider.isEnabled()
    page.blurBackgroundToggle.click()
    assert not page.blurFeatherSlider.isEnabled()
