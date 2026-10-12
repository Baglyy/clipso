import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QWidget

from view.dialogs.export_dialog import ExportDialog


@pytest.fixture
def parent(qtbot):
    widget = QWidget()
    widget.resize(900, 600)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def dialog(parent):
    return ExportDialog(parent)


def test_frameless_and_translucent(dialog):
    assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_buttons_have_hand_cursor(dialog):
    for button in (dialog.closeButton, dialog.confirmExportButton, dialog.cancelButton, dialog.browseButton):
        assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor, button.objectName()
    assert not dialog.closeButton.icon().isNull()
    assert not dialog.confirmExportButton.icon().isNull()


def test_thumbnail_and_folder_icon(dialog):
    assert not dialog.summaryThumbLabel.pixmap().isNull()
    assert len(dialog.folderEdit.actions()) == 1


def test_initial_quality(dialog):
    assert dialog.qualityValue.text() == "Haute · 80 %"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (10, "Basse · 10 %"),
        (39, "Basse · 39 %"),
        (40, "Moyenne · 40 %"),
        (70, "Haute · 70 %"),
        (90, "Maximale · 90 %"),
        (100, "Maximale · 100 %"),
    ],
)
def test_quality_label_follows_slider(dialog, value, expected):
    dialog.qualitySlider.setValue(value)
    assert dialog.qualityValue.text() == expected


@pytest.mark.parametrize(
    "buttons",
    [
        ("formatMp4Button", "formatMovButton", "formatWebmButton", "formatGifButton"),
        ("resolution720Button", "resolution1080Button"),
        ("fps24Button", "fps30Button", "fps60Button"),
    ],
)
def test_only_one_choice_checked_per_group(qtbot, dialog, buttons):
    for name in buttons:
        qtbot.mouseClick(getattr(dialog, name), Qt.MouseButton.LeftButton)
        assert [getattr(dialog, other).isChecked() for other in buttons] == [other == name for other in buttons]


def test_default_choices(dialog):
    assert dialog.formatMp4Button.isChecked()
    assert dialog.resolution1080Button.isChecked()
    assert dialog.fps30Button.isChecked()


@pytest.mark.parametrize(
    ("button_name", "result"),
    [
        ("closeButton", ExportDialog.DialogCode.Rejected),
        ("cancelButton", ExportDialog.DialogCode.Rejected),
        ("confirmExportButton", ExportDialog.DialogCode.Accepted),
    ],
)
def test_footer_buttons_close_dialog(qtbot, dialog, button_name, result):
    dialog.show()
    with qtbot.waitSignal(dialog.finished, timeout=1000) as blocker:
        qtbot.mouseClick(getattr(dialog, button_name), Qt.MouseButton.LeftButton)
    assert blocker.args == [result.value]
    assert not dialog.isVisible()


def test_browse_sets_folder(qtbot, monkeypatch, dialog):
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: "/home/lea/Exports")
    qtbot.mouseClick(dialog.browseButton, Qt.MouseButton.LeftButton)
    assert dialog.folderEdit.text() == "/home/lea/Exports"


def test_browse_cancelled_keeps_folder(qtbot, monkeypatch, dialog):
    before = dialog.folderEdit.text()
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: "")
    qtbot.mouseClick(dialog.browseButton, Qt.MouseButton.LeftButton)
    assert dialog.folderEdit.text() == before


def test_show_covers_parent_window(qtbot, parent, dialog):
    parent.show()
    qtbot.waitExposed(parent)
    dialog.show()
    qtbot.waitExposed(dialog)
    assert dialog.geometry() == parent.window().geometry()
    dialog.repaint()
