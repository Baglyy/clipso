from pathlib import Path

import pytest

from model.media import PEAKS, THUMBNAIL_HEIGHT, Media, kind_of


@pytest.mark.parametrize(
    ("name", "kind"),
    [("plage.mp4", "video"), ("film.MOV", "video"), ("voix.wav", "audio"), ("son.mp3", "audio"), ("logo.png", "image")],
)
def test_kind_from_extension(name, kind):
    assert kind_of(Path(name)) == kind


def test_unknown_extension_is_refused():
    with pytest.raises(ValueError, match="non pris en charge"):
        kind_of(Path("notes.txt"))


def test_read_video(media_files):
    media = Media.from_file(media_files["video"])
    assert media.kind == "video"
    assert media.name == "clip.mp4"
    assert media.duration == pytest.approx(1, abs=0.1)
    assert (media.width, media.height) == (160, 120)
    assert media.has_audio
    assert media.thumbnail.shape == (THUMBNAIL_HEIGHT, 160, 3)


def test_read_audio(media_files):
    media = Media.from_file(media_files["audio"])
    assert media.kind == "audio"
    assert media.duration == pytest.approx(0.5, abs=0.1)
    assert media.thumbnail is None
    assert len(media.peaks) == PEAKS
    assert max(media.peaks) == 1
    assert min(media.peaks) >= 0


def test_read_image(media_files):
    media = Media.from_file(media_files["image"])
    assert media.kind == "image"
    assert media.duration == 0
    assert (media.width, media.height) == (40, 20)
    assert media.thumbnail.shape == (THUMBNAIL_HEIGHT, 240, 3)
    # l'image de test est rouge
    assert tuple(media.thumbnail[0, 0]) == (255, 0, 0)


def test_unreadable_file(tmp_path):
    broken = tmp_path / "casse.mp4"
    broken.write_text("pas une vidéo")
    with pytest.raises(ValueError, match="casse.mp4"):
        Media.from_file(broken)


def test_unreadable_audio(tmp_path):
    broken = tmp_path / "casse.wav"
    broken.write_text("pas un son")
    with pytest.raises(ValueError, match="casse.wav"):
        Media.from_file(broken)
