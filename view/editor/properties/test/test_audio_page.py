import pytest

from view.editor.properties.audio_page import AudioPage


@pytest.fixture
def page(qtbot):
    widget = AudioPage()
    qtbot.addWidget(widget)
    return widget


def test_volume_label_follows_slider(page):
    page.audioVolumeSlider.setValue(150)
    assert page.audioVolumeValue.text() == "150 %"


@pytest.mark.parametrize(
    ("slider_name", "label_name"),
    [("audioFadeInSlider", "audioFadeInValue"), ("audioFadeOutSlider", "audioFadeOutValue")],
)
def test_fade_label_in_tenths_of_second(page, slider_name, label_name):
    # le curseur compte en dixièmes : 25 → 2,5 s
    getattr(page, slider_name).setValue(25)
    assert getattr(page, label_name).text() == "2,5 s"


def test_toggles_loaded_from_ui(page):
    assert not page.muteToggle.isChecked()
    assert not page.normalizeToggle.isChecked()


AUDIO_VALUES = {"volume": 150, "fade_in": 1.5, "fade_out": 0.3, "muted": True, "normalize": True}


def test_set_values_then_values(page, qtbot):
    with qtbot.assertNotEmitted(page.changed):
        page.set_values(AUDIO_VALUES)
    assert page.values() == AUDIO_VALUES
    assert page.audioFadeInSlider.value() == 15


def test_user_changes_emit_changed(page, qtbot):
    with qtbot.waitSignal(page.changed):
        page.audioVolumeSlider.setValue(20)
    with qtbot.waitSignal(page.changed):
        page.muteToggle.click()
