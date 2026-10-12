import pytest
from PyQt6.QtCore import Qt

from view.editor.preview.preview_panel import FPS, PreviewPanel
from view.editor.preview.video_view import VideoView


@pytest.fixture
def panel(qtbot):
    widget = PreviewPanel()
    qtbot.addWidget(widget)
    return widget


def test_video_view_loaded_from_ui(panel):
    assert isinstance(panel.videoView, VideoView)


def test_buttons_have_icon_and_hand_cursor(panel):
    buttons = (
        panel.skipStartButton,
        panel.previousFrameButton,
        panel.playButton,
        panel.nextFrameButton,
        panel.skipEndButton,
        panel.volumeButton,
        panel.fullscreenButton,
        panel.fitPreviewButton,
    )
    for button in buttons:
        assert not button.icon().isNull(), button.objectName()
        assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor, button.objectName()


def test_initial_state_is_paused(panel):
    assert not panel.playing
    assert panel.playButton.toolTip() == "Lecture (Espace)"


def test_play_click_toggles_and_emits(qtbot, panel):
    with qtbot.waitSignal(panel.play_toggled, timeout=1000) as blocker:
        qtbot.mouseClick(panel.playButton, Qt.MouseButton.LeftButton)
    assert panel.playing
    assert blocker.args == [True]
    assert panel.playButton.toolTip() == "Pause (Espace)"

    with qtbot.waitSignal(panel.play_toggled, timeout=1000) as blocker:
        qtbot.mouseClick(panel.playButton, Qt.MouseButton.LeftButton)
    assert not panel.playing
    assert blocker.args == [False]


def test_set_playing_does_not_emit(qtbot, panel):
    # set_playing sert au contrôleur pour synchroniser l'affichage, sans renvoyer de signal
    with qtbot.assertNotEmitted(panel.play_toggled):
        panel.set_playing(True)
    assert panel.playing
    assert panel.playButton.toolTip() == "Pause (Espace)"


@pytest.mark.parametrize(
    ("button_name", "step"),
    [("previousFrameButton", -1 / FPS), ("nextFrameButton", 1 / FPS)],
)
def test_frame_buttons_emit_step(qtbot, panel, button_name, step):
    with qtbot.waitSignal(panel.step_requested, timeout=1000) as blocker:
        qtbot.mouseClick(getattr(panel, button_name), Qt.MouseButton.LeftButton)
    assert blocker.args == [pytest.approx(step)]


@pytest.mark.parametrize(("button_name", "target"), [("skipStartButton", "start"), ("skipEndButton", "end")])
def test_skip_buttons_emit_jump(qtbot, panel, button_name, target):
    with qtbot.waitSignal(panel.jump_requested, timeout=1000) as blocker:
        qtbot.mouseClick(getattr(panel, button_name), Qt.MouseButton.LeftButton)
    assert blocker.args == [target]


def test_volume_button_mutes(qtbot, panel):
    unmuted_icon = panel.volumeButton.icon().cacheKey()
    qtbot.mouseClick(panel.volumeButton, Qt.MouseButton.LeftButton)
    assert panel.volumeButton.isChecked()
    assert panel.volumeButton.icon().cacheKey() != unmuted_icon


def test_fit_menu_changes_button_text(panel):
    actions = panel.fitPreviewButton.menu().actions()
    assert [action.text() for action in actions] == ["Ajuster", "50 %", "100 %", "200 %"]

    actions[2].trigger()
    assert panel.fitPreviewButton.text() == "100 %"


def test_set_time(panel):
    panel.set_time(65.5, 120)
    assert panel.timecodeLabel.text() == "00:01:05:15 / 00:02:00:00"


def test_show_frame_forwarded_to_video_view(panel):
    panel.show_frame(color="#468A57", source="plage.mp4", text="Salut", logo=False)
    assert panel.videoView._source == "plage.mp4"
    assert panel.videoView._text == "Salut"
    assert not panel.videoView._logo
