import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QProgressDialog

from controller.app_controller import AppController, clip_peaks, to_qimage
from model.export import ExportSettings
from model.media import Media
from model.project import Clip
from view.dialogs.export_dialog import ExportDialog
from view.main_window import MainWindow


@pytest.fixture
def window(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    return win


@pytest.fixture
def controller(window):
    app_controller = AppController(window)
    yield app_controller
    app_controller.close()


@pytest.fixture
def messages(monkeypatch):
    shown = []
    monkeypatch.setattr(QMessageBox, "information", lambda parent, title, text: shown.append(("information", text)))
    monkeypatch.setattr(QMessageBox, "warning", lambda parent, title, text: shown.append(("warning", text)))
    return shown


def import_files(controller, qtbot, paths):
    controller.add_media([str(path) for path in paths])
    if controller.import_worker is not None:
        qtbot.waitUntil(lambda: controller.import_worker is None, timeout=30_000)


def view_clips(window):
    return {track["kind"]: [clip["name"] for clip in track["clips"]] for track in window.editor_page.timeline.tracks}


def test_create_project_with_chosen_format(controller, window, qtbot):
    qtbot.mouseClick(window.home_page.formatVerticalButton, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.home_page.createProjectButton, Qt.MouseButton.LeftButton)

    assert window.pages.currentWidget() is window.editor_page
    assert controller.project.aspect == "9:16"
    assert window.editor_page.previewPanel.previewInfoLabel.text() == "9:16 · 1080p · 30 ips"
    assert window.editor_page.mediaPanel.tiles == []


def test_import_goes_to_library_only(controller, window, media_files, qtbot):
    import_files(controller, qtbot, media_files.values())

    tiles = window.editor_page.mediaPanel.tiles
    assert [tile.media["name"] for tile in tiles] == ["clip.mp4", "son.wav", "logo.png"]
    assert not any(tile.media["used"] for tile in tiles)
    assert tiles[0].media["thumbnail"] is not None
    assert len(tiles[1].media["peaks"]) > 0
    assert view_clips(window) == {"overlay": [], "video": [], "audio": []}
    assert window.editor_page.mediaPanel.importButton.isEnabled()


def test_import_button_opens_file_dialog(controller, window, media_files, qtbot, monkeypatch):
    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *args: ([str(media_files["image"])], ""))
    window.editor_page.mediaPanel.importButton.click()
    qtbot.waitUntil(lambda: len(controller.project.media) == 1, timeout=30_000)


def test_import_cancelled(controller, monkeypatch):
    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *args: ([], ""))
    controller.import_media()
    assert controller.import_worker is None


def test_import_from_home_creates_project(controller, window, media_files, qtbot, monkeypatch):
    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *args: ([str(media_files["video"])], ""))
    window.home_page.importMediaButton.click()
    assert window.pages.currentWidget() is window.editor_page
    qtbot.waitUntil(lambda: len(controller.project.media) == 1, timeout=30_000)


def test_unreadable_and_duplicate_files_are_reported(controller, media_files, tmp_path, qtbot, messages):
    import_files(controller, qtbot, [media_files["image"]])
    broken = tmp_path / "casse.mp4"
    broken.write_text("pas une vidéo")
    import_files(controller, qtbot, [broken, tmp_path / "notes.txt", media_files["image"], media_files["audio"]])

    assert [media.name for media in controller.project.media] == ["logo.png", "son.wav"]
    ((kind, text),) = messages
    assert kind == "warning"
    assert "casse.mp4" in text and "notes.txt" in text and "logo.png est déjà importé" in text


def test_only_duplicates(controller, media_files, qtbot, messages):
    import_files(controller, qtbot, [media_files["image"]])
    import_files(controller, qtbot, [media_files["image"]])
    assert controller.import_worker is None
    assert "déjà importé" in messages[0][1]


def test_double_click_places_media(controller, window, media_files, qtbot):
    import_files(controller, qtbot, media_files.values())
    window.editor_page.mediaPanel.tiles[0].activated.emit(0)
    window.editor_page.mediaPanel.tiles[0].activated.emit(0)
    assert view_clips(window)["video"] == ["clip.mp4", "clip.mp4"]
    assert window.editor_page.mediaPanel.tiles[0].media["used"]


def test_drop_places_media_at_time(controller, window, media_files, qtbot):
    import_files(controller, qtbot, [media_files["image"]])
    window.editor_page.timeline.media_dropped.emit(0, 1, 2.5)
    clip = controller.project.tracks[1].clips[0]
    assert clip.start == 2.5
    assert view_clips(window)["video"] == ["logo.png"]


def test_drop_on_wrong_track(controller, media_files, qtbot, messages):
    import_files(controller, qtbot, [media_files["image"]])
    controller.drop_media(0, 2, 0)
    assert controller.project.duration == 0
    assert "Audio 1" in messages[0][1]


def test_track_buttons_update_model(controller, window, media_files, qtbot):
    controller.new_project()
    panel = window.editor_page.timelinePanel
    panel.headers[0].visibility_button.click()
    panel.headers[2].lock_button.click()
    assert controller.project.tracks[0].hidden
    assert controller.project.tracks[2].locked
    controller.refresh()
    assert panel.headers[0].visibility_button.isChecked()


def test_select_clip_shows_its_settings(controller, window, media_files, qtbot):
    import_files(controller, qtbot, [media_files["audio"], media_files["image"]])
    sound = controller.project.place(controller.project.media[0])
    sound.audio.volume = 42
    logo = controller.project.place(controller.project.media[1])
    logo.image.rotation = 90
    controller.refresh()

    editor = window.editor_page
    editor.select_clip(editor.timeline.tracks[2]["clips"][0])
    assert controller.selected_clip is sound
    assert editor.propertiesPanel.audioPage.audioVolumeSlider.value() == 42

    editor.select_clip(editor.timeline.tracks[0]["clips"][0])
    assert editor.propertiesPanel.imagePage.imageRotationSlider.value() == 90
    assert editor.propertiesPanel.imagePage.imageInfoLabel.text() == "PNG · 40 × 20"


def test_settings_are_saved_in_model(controller, window, media_files, qtbot):
    import_files(controller, qtbot, [media_files["video"]])
    clip = controller.project.place(controller.project.media[0])
    controller.refresh()
    editor = window.editor_page
    editor.select_clip(editor.timeline.tracks[1]["clips"][0])

    editor.propertiesPanel.filtersPage.brightnessSlider.setValue(25)
    editor.propertiesPanel.blurPage.blurIntensitySlider.setValue(60)
    editor.propertiesPanel.audioPage.muteToggle.click()
    assert clip.filters.brightness == 25
    assert clip.blur.intensity == 60
    assert clip.audio.muted


def test_text_changes_update_timeline(controller, window, qtbot):
    controller.new_project()
    text = Clip(0, 3, text="Avant")
    controller.project.tracks[0].clips.append(text)
    controller.refresh()
    editor = window.editor_page
    editor.select_clip(editor.timeline.tracks[0]["clips"][0])

    page = editor.propertiesPanel.textPage
    page.textContentEdit.clear()
    qtbot.keyClicks(page.textContentEdit, "Fin")
    qtbot.mouseClick(page.colorYellowButton, Qt.MouseButton.LeftButton)
    assert text.text == "Fin"
    assert text.text_style.color == "#F2C24B"
    assert editor.timeline.tracks[0]["clips"][0]["name"] == "Titre « Fin »"


def test_settings_without_selection_are_ignored(controller):
    controller.change_settings("audio", {"volume": 10})
    assert controller.selected_clip is None


def test_export_of_empty_project_is_refused(controller, window, messages, monkeypatch):
    monkeypatch.setattr(ExportDialog, "exec", lambda self: pytest.fail("la fenêtre ne doit pas s'ouvrir"))
    window.editor_page.export_requested.emit()
    assert "vide" in messages[0][1]


def test_export_dialog_shows_project(controller, window, media_files, qtbot, monkeypatch):
    import_files(controller, qtbot, [media_files["video"]])
    controller.place_media(0)
    opened = []

    def fake_exec(dialog):
        opened.append(dialog)
        qtbot.waitUntil(lambda: "≈" in dialog.summarySizeLabel.text(), timeout=30_000)
        return 0

    monkeypatch.setattr(ExportDialog, "exec", fake_exec)
    window.editor_page.export_requested.emit()

    (dialog,) = opened
    assert dialog.summaryNameLabel.text() == "Projet sans titre"
    assert dialog.fileNameEdit.text() == "Projet sans titre"
    assert dialog.summaryThumbLabel.pixmap().height() == 66
    assert controller.estimate_worker is None
    assert controller.export_worker is None


def test_estimate_restarts_when_settings_change(controller, media_files, qtbot):
    import_files(controller, qtbot, [media_files["video"]])
    controller.place_media(0)
    dialog = ExportDialog(controller.window)
    dialog.set_project("Test", 1, "16:9", 1080, 30, "/tmp")
    controller.start_estimate(dialog)
    first = controller.estimate_worker
    controller.start_estimate(dialog)
    assert controller.estimate_worker is not first
    assert first.logger.cancelled
    controller.stop_estimate()


def test_export_runs_in_background(controller, window, media_files, tmp_path, qtbot, messages, monkeypatch):
    import_files(controller, qtbot, [media_files["video"]])
    controller.place_media(0)

    def fake_exec(dialog):
        dialog.folderEdit.setText(str(tmp_path))
        dialog.fileNameEdit.setText("Mon film")
        dialog.resolution720Button.click()
        return 1

    monkeypatch.setattr(ExportDialog, "exec", fake_exec)
    window.editor_page.export_requested.emit()

    qtbot.waitUntil(lambda: len(messages) > 0, timeout=60_000)
    assert messages[0][0] == "information", messages
    assert (tmp_path / "Mon film.mp4").stat().st_size > 0
    assert controller.export_worker is None


def test_export_can_be_cancelled(controller, media_files, tmp_path, qtbot, messages):
    import_files(controller, qtbot, [media_files["video"]])
    controller.place_media(0)
    controller.start_export(ExportSettings(tmp_path, "film", resolution=720))
    controller.export_worker.cancel()
    qtbot.waitUntil(lambda: len(messages) > 0, timeout=60_000)
    assert messages == [("information", "Export annulé.")]
    assert not (tmp_path / "film.mp4").exists()


def test_existing_file_kept_when_user_says_no(controller, tmp_path, monkeypatch):
    existing = tmp_path / "film.mp4"
    existing.write_text("ancien")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    controller.start_export(ExportSettings(tmp_path, "film"))
    assert controller.export_worker is None
    assert existing.read_text() == "ancien"


def test_export_failure_is_reported(controller, messages):
    controller.export_done(QProgressDialog(), "L'export a échoué", failed=True)
    assert messages == [("warning", "L'export a échoué")]


def test_to_qimage():
    import numpy as np

    frame = np.zeros((4, 6, 3), dtype=np.uint8)
    frame[:, :, 0] = 255
    image = to_qimage(frame)
    assert (image.width(), image.height()) == (6, 4)
    assert image.pixelColor(0, 0).red() == 255
    assert to_qimage(None) is None


def test_clip_peaks_follow_clip(tmp_path):
    media = Media(tmp_path / "son.wav", "audio", 10, peaks=[float(i) for i in range(100)])
    clip = Clip(0, 5, media, in_point=2)
    assert clip_peaks(clip) == [float(i) for i in range(20, 70)]


def preview_pixel(window, x, y):
    image = window.editor_page.previewPanel.videoView._image
    return image.pixelColor(x, y) if image is not None else QColor("black")


def test_preview_shows_real_frame(controller, window, media_files, qtbot):
    controller.new_project()
    import_files(controller, qtbot, [media_files["image"]])
    controller.place_media(0)
    view = window.editor_page.previewPanel.videoView
    qtbot.waitUntil(lambda: view._image is not None, timeout=30_000)

    assert (view._image.width(), view._image.height()) == (640, 360)
    qtbot.waitUntil(lambda: preview_pixel(window, 320, 180).red() > 200, timeout=30_000)
    assert preview_pixel(window, 20, 20).red() < 30


def test_preview_follows_settings_and_hidden_track(controller, window, media_files, qtbot):
    controller.new_project()
    import_files(controller, qtbot, [media_files["image"]])
    controller.place_media(0)
    editor = window.editor_page
    editor.select_clip(editor.timeline.tracks[0]["clips"][0])
    qtbot.waitUntil(lambda: preview_pixel(window, 320, 180).red() > 200, timeout=30_000)

    editor.propertiesPanel.imagePage.imageXFieldSpin.setValue(5)
    editor.propertiesPanel.imagePage.imageYFieldSpin.setValue(5)
    qtbot.waitUntil(lambda: preview_pixel(window, 320, 180).red() < 30, timeout=30_000)
    assert preview_pixel(window, 32, 18).red() > 200

    controller.set_track_hidden(0, True)
    qtbot.waitUntil(lambda: preview_pixel(window, 32, 18).red() < 30, timeout=30_000)


def test_preview_uses_project_aspect(controller, window, media_files, qtbot):
    qtbot.mouseClick(window.home_page.formatVerticalButton, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.home_page.createProjectButton, Qt.MouseButton.LeftButton)
    import_files(controller, qtbot, [media_files["video"]])
    controller.place_media(0)
    view = window.editor_page.previewPanel.videoView
    qtbot.waitUntil(lambda: view._image is not None, timeout=30_000)
    assert view.aspect == pytest.approx(9 / 16)
    assert (view._image.width(), view._image.height()) == (360, 640)


def test_selection_box_only_for_visible_image(controller, window, media_files, qtbot):
    controller.new_project()
    import_files(controller, qtbot, [media_files["image"]])
    controller.place_media(0)
    editor = window.editor_page
    view = editor.previewPanel.videoView
    editor.select_clip(editor.timeline.tracks[0]["clips"][0])

    box = view._selection
    assert box.center().x() == pytest.approx(0.5)
    assert box.center().y() == pytest.approx(0.5)
    assert box.width() == pytest.approx(40 / 1920)
    assert box.height() == pytest.approx(20 / 1080)

    # un clip image dure 5 s
    editor.seek(10)
    assert view._selection is None
