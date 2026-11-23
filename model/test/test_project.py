from pathlib import Path

import pytest

from model.media import Media
from model.project import IMAGE_DURATION, Clip, Project


def media(kind: str, duration: float = 0.0, name: str = "fichier") -> Media:
    return Media(Path(f"{name}.{kind}"), kind, duration)


def test_new_project_is_empty():
    project = Project()
    assert project.duration == 0
    assert [track.kind for track in project.tracks] == ["overlay", "video", "audio"]


@pytest.mark.parametrize(
    ("aspect", "resolution", "size"),
    [("16:9", 1080, (1920, 1080)), ("16:9", 720, (1280, 720)), ("9:16", 1080, (1080, 1920)), ("1:1", 720, (720, 720))],
)
def test_frame_size(aspect, resolution, size):
    assert Project(aspect=aspect).frame_size(resolution) == size


def test_frame_size_is_even():
    width, height = Project().frame_size(90)
    assert width % 2 == 0 and height % 2 == 0


def test_add_media_only_goes_to_library():
    project = Project()
    video = media("video", 4)
    project.add_media(video)
    assert project.media == [video]
    assert project.duration == 0
    assert not project.is_used(video)


def test_has_media(tmp_path):
    project = Project()
    project.add_media(Media(tmp_path / "a.mp4", "video", 1))
    assert project.has_media(tmp_path / "a.mp4")
    assert project.has_media(str(tmp_path / "dossier" / ".." / "a.mp4"))
    assert not project.has_media(tmp_path / "b.mp4")


def test_place_at_end_of_default_track():
    project = Project()
    first = project.place(media("video", 4))
    second = project.place(media("video", 3))
    sound = project.place(media("audio", 10))
    logo = project.place(media("image"))

    assert project.tracks[1].clips == [first, second]
    assert second.start == 4
    assert project.tracks[2].clips == [sound]
    assert project.tracks[0].clips == [logo]
    assert logo.duration == IMAGE_DURATION
    assert project.duration == 10


def test_place_at_chosen_time():
    project = Project()
    clip = project.place(media("video", 2), project.tracks[1], 7.5)
    assert clip.start == 7.5


def test_place_is_shifted_when_taken():
    project = Project()
    track = project.tracks[1]
    project.place(media("video", 4), track, 0)
    project.place(media("video", 2), track, 6)
    # 3 s ne tiennent ni à 1 s (pris jusqu'à 4) ni à 4 s (le clip suivant commence à 6)
    clip = project.place(media("video", 3), track, 1)
    assert clip.start == 8


def test_video_can_go_on_overlay_but_not_on_audio():
    project = Project()
    assert project.place(media("video", 1), project.tracks[0]).start == 0
    with pytest.raises(ValueError, match="Audio 1"):
        project.place(media("video", 1), project.tracks[2])


def test_locked_track_is_refused():
    project = Project()
    project.tracks[1].locked = True
    with pytest.raises(ValueError, match="verrouillée"):
        project.place(media("video", 1))


def test_text_clip():
    clip = Clip(1, 2, text="Été 2026")
    assert clip.kind == "text"
    assert clip.name == "Titre « Été 2026 »"
    assert clip.end == 3


def test_each_clip_has_its_own_settings():
    a, b = Clip(0, 1), Clip(0, 1)
    a.audio.volume = 50
    assert b.audio.volume == 100
