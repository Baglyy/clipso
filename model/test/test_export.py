import imageio_ffmpeg
import numpy as np
import pytest
from proglog import ProgressBarLogger

from model.export import (
    ExportCancelledError,
    ExportSettings,
    crf,
    estimate_size,
    export,
    gif_colors,
    image_box,
    image_factor,
    preview_frame,
)
from model.media import Media
from model.project import Clip, Project


@pytest.fixture
def project(media_files):
    project = Project(name="Test")
    for path in media_files.values():
        media = Media.from_file(path)
        project.add_media(media)
        project.place(media)
    text = Clip(0.2, 0.5, text="Salut")
    text.text_style.align = "left"
    project.tracks[0].clips.append(text)
    return project


def settings(folder, file_name="Test", **changes) -> ExportSettings:
    # petite résolution pour que les tests restent rapides
    values = {"resolution": 90, "fps": 10}
    values.update(changes)
    return ExportSettings(folder, file_name, **values)


def frame_of(path, time):
    reader = imageio_ffmpeg.read_frames(str(path))
    infos = next(reader)
    frames = list(reader)
    width, height = infos["size"]
    index = min(int(time * infos["fps"]), len(frames) - 1)
    return np.frombuffer(frames[index], dtype=np.uint8).reshape(height, width, 3)


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [("Vacances", "Vacances.webm"), ("Vacances.mp4", "Vacances.webm"), ("v1.2", "v1.2.webm"), ("  ", "export.webm")],
)
def test_path_uses_chosen_format(tmp_path, file_name, expected):
    assert ExportSettings(tmp_path, file_name, "webm").path == tmp_path / expected


def test_better_quality_means_lower_crf(tmp_path):
    assert crf(settings(tmp_path, quality=100)) < crf(settings(tmp_path, quality=10))
    assert crf(settings(tmp_path, quality=100)) == 18


def test_gif_colors_and_fps(tmp_path):
    assert gif_colors(settings(tmp_path, quality=100)) == 256
    assert gif_colors(settings(tmp_path, quality=10)) == 40
    assert settings(tmp_path, format="gif", fps=60).output_fps == 25
    assert settings(tmp_path, format="mp4", fps=60).output_fps == 60


def test_empty_project_is_refused(tmp_path):
    with pytest.raises(ValueError, match="vide"):
        export(Project(), settings(tmp_path))


@pytest.mark.parametrize("file_format", ["mp4", "mov", "webm", "gif"])
def test_export_creates_file(project, tmp_path, file_format):
    path = export(project, settings(tmp_path / "sortie", format=file_format), logger=None)
    assert path == tmp_path / "sortie" / f"Test.{file_format}"
    assert path.stat().st_size > 0


def test_exported_video_has_project_size_and_duration(project, tmp_path):
    path = export(project, settings(tmp_path), logger=None)
    reader = imageio_ffmpeg.read_frames(str(path))
    infos = next(reader)
    reader.close()
    assert tuple(infos["size"]) == (160, 90)
    assert infos["duration"] == pytest.approx(project.duration, abs=0.2)


def test_gif_quality_changes_size(project, tmp_path):
    low = export(project, settings(tmp_path, file_name="bas", format="gif", quality=10, resolution=360), logger=None)
    high = export(project, settings(tmp_path, file_name="haut", format="gif", quality=100, resolution=360), logger=None)
    assert low.stat().st_size < high.stat().st_size


def test_hidden_overlay_track_is_not_exported(project, tmp_path):
    logo = project.tracks[0].clips[0]
    logo.image.scale = 1000  # le logo rouge remplit toute l'image
    red = frame_of(export(project, settings(tmp_path, file_name="avec"), logger=None), 0.5)
    project.tracks[0].hidden = True
    without = frame_of(export(project, settings(tmp_path, file_name="sans"), logger=None), 0.5)
    assert red[45, 80, 0] > 200 and red[45, 80, 1] < 60
    assert not (without[45, 80, 0] > 200 and without[45, 80, 1] < 60)


def test_image_position(project, tmp_path):
    project.tracks[0].clips.pop()  # sans le texte
    logo = project.tracks[0].clips[0]
    logo.image.x, logo.image.y = 10, 10
    # même résolution que l'aperçu, sinon le logo de 40 × 20 ne fait plus que 3 pixels
    project.resolution = 90
    frame = preview_frame(project, 0.5, 90)
    assert frame[9, 16, 0] > 200 and frame[9, 16, 1] < 60
    assert not (frame[80, 150, 0] > 200 and frame[80, 150, 1] < 60)


def has_audio_stream(path) -> bool:
    media = Media.from_file(path)
    return media.has_audio


def test_muted_clip_has_no_sound(media_files, tmp_path):
    project = Project()
    sound = Media.from_file(media_files["audio"])
    project.add_media(sound)
    clip = project.place(sound)
    assert has_audio_stream(export(project, settings(tmp_path, file_name="son"), logger=None))
    clip.audio.muted = True
    assert not has_audio_stream(export(project, settings(tmp_path, file_name="muet"), logger=None))


def test_muted_audio_track_has_no_sound(media_files, tmp_path):
    project = Project()
    sound = Media.from_file(media_files["audio"])
    project.add_media(sound)
    project.place(sound)
    project.tracks[2].hidden = True
    assert not has_audio_stream(export(project, settings(tmp_path), logger=None))


def test_audio_settings_do_not_crash(project, tmp_path):
    sound = project.tracks[2].clips[0]
    sound.audio.volume = 150
    sound.audio.fade_in = 0.2
    sound.audio.fade_out = 2.0
    sound.audio.normalize = True
    image = project.tracks[0].clips[0]
    image.image.rotation = 45
    image.image.opacity = 50
    image.filters.brightness = 20
    assert export(project, settings(tmp_path), logger=None).exists()


def test_estimated_size_is_close(project, tmp_path):
    estimate = estimate_size(project, settings(tmp_path))
    real = export(project, settings(tmp_path), logger=None).stat().st_size
    assert real / 2 < estimate < real * 2


def test_cancel_removes_partial_file(project, tmp_path):
    class CancelLogger(ProgressBarLogger):
        def bars_callback(self, bar, attr, value, old_value=None):
            if bar == "frame_index" and value > 2:
                raise ExportCancelledError()

    with pytest.raises(ExportCancelledError):
        export(project, settings(tmp_path), logger=CancelLogger())
    assert not (tmp_path / "Test.mp4").exists()


def test_preview_frame(project):
    frame = preview_frame(project, 0.5, 90)
    assert frame.shape == (90, 160, 3)
    assert frame.dtype == np.uint8


def test_filters_are_exported(project):
    video = project.tracks[1].clips[0]
    before = preview_frame(project, 0.1, 90)
    video.filters.preset = "mono"
    after = preview_frame(project, 0.1, 90)
    assert not np.array_equal(before, after)
    assert np.ptp(after[85, 30].astype(int)) == 0


def test_blur_is_exported(project):
    before = preview_frame(project, 0.1, 90)
    project.tracks[1].clips[0].blur.intensity = 100
    assert not np.array_equal(before, preview_frame(project, 0.1, 90))


@pytest.mark.parametrize("animation", ["none", "fade", "slide", "zoom"])
def test_text_animations(animation):
    project = Project()
    project.add_text(0).text_style.animation = animation
    start = preview_frame(project, 0, 180)
    middle = preview_frame(project, 0.25, 180)
    end = preview_frame(project, 1, 180)
    assert end.max() > 0
    if animation == "none":
        assert np.array_equal(start, end)
    else:
        assert start.sum() < end.sum()
        assert not np.array_equal(middle, start)
        assert not np.array_equal(middle, end)


def test_empty_text_is_not_exported():
    project = Project()
    project.add_text(0, "  ")
    assert preview_frame(project, 1, 90).max() == 0


def logo_clip(width, height, **image):
    clip = Clip(0, 5, Media("logo.png", "image", width=width, height=height))
    for name, value in image.items():
        setattr(clip.image, name, value)
    return clip


def test_image_keeps_same_place_at_every_resolution():
    clip = logo_clip(800, 800)
    full = image_factor(800, 800, clip, (1920, 1080), (1920, 1080))
    small = image_factor(800, 800, clip, (640, 360), (1920, 1080))
    assert full == 1
    assert small == pytest.approx(1 / 3)


def test_big_image_fits_in_frame():
    clip = logo_clip(3840, 2160, scale=50)
    assert image_factor(3840, 2160, clip, (1920, 1080), (1920, 1080)) == pytest.approx(0.25)


def test_image_box_position_and_rotation():
    size = (1920, 1080)
    assert image_box(logo_clip(200, 100, x=25, y=50), size, size) == (380, 490, 200, 100)
    x, y, width, height = image_box(logo_clip(200, 100, rotation=90), size, size)
    assert (width, height) == (pytest.approx(100), pytest.approx(200))
    assert (x + width / 2, y + height / 2) == (pytest.approx(960), pytest.approx(540))
