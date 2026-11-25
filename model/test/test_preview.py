import numpy as np
import pytest

from model.media import Media
from model.preview import SAMPLE_RATE, AudioRenderer, PreviewRenderer
from model.project import Project


@pytest.fixture
def renderer():
    preview = PreviewRenderer(resolution=90)
    yield preview
    preview.close()


@pytest.fixture
def logo_project(media_files):
    # même résolution que l'aperçu, sinon le logo de 40 × 20 ne fait plus que 3 pixels
    project = Project(resolution=90)
    media = Media.from_file(media_files["image"])
    project.add_media(media)
    project.place(media)
    return project


def test_empty_project_has_no_frame(renderer):
    renderer.rebuild(Project())
    assert renderer.frame(0) is None


def test_frame_has_preview_size(renderer, logo_project):
    renderer.rebuild(logo_project)
    frame = renderer.frame(1.0)
    assert frame.shape == (90, 160, 3)
    assert frame[45, 80, 0] > 200 and frame[45, 80, 1] < 60
    assert frame[5, 5].max() < 30


@pytest.mark.parametrize("time", [-1.0, 5.0, 99.0])
def test_frame_outside_project_is_clamped(renderer, logo_project, time):
    renderer.rebuild(logo_project)
    assert renderer.frame(time).shape == (90, 160, 3)


def test_rebuild_takes_changes_into_account(renderer, logo_project):
    renderer.rebuild(logo_project)
    assert renderer.frame(1.0)[45, 80, 0] > 200
    logo_project.tracks[0].hidden = True
    # sans rebuild, l'ancien montage reste affiché
    assert renderer.frame(1.0)[45, 80, 0] > 200
    renderer.rebuild(logo_project)
    assert renderer.frame(1.0)[45, 80, 0] < 30


def test_close_releases_files(renderer, media_files):
    project = Project()
    media = Media.from_file(media_files["video"])
    project.add_media(media)
    project.place(media)
    renderer.rebuild(project)
    assert renderer.sources
    renderer.close()
    assert renderer.sources == [] and renderer.video is None


@pytest.fixture
def audio():
    renderer = AudioRenderer()
    yield renderer
    renderer.close()


@pytest.fixture
def sound_project(media_files):
    project = Project()
    media = Media.from_file(media_files["audio"])
    project.add_media(media)
    project.place(media, start=1.0)
    return project


def test_audio_starts_with_clip_and_ends_in_silence(audio, sound_project):
    audio.rebuild(sound_project)
    samples = audio.samples(0, 2 * SAMPLE_RATE)
    assert samples.shape == (2 * SAMPLE_RATE, 2) and samples.dtype == np.int16
    assert not samples[:SAMPLE_RATE].any()
    assert abs(samples[SAMPLE_RATE : SAMPLE_RATE + 20_000]).max() > 1000
    assert not samples[round(1.51 * SAMPLE_RATE) :].any()


def test_audio_chunks_are_continuous(audio, media_files):
    project = Project()
    media = Media.from_file(media_files["video"])
    project.add_media(media)
    project.place(media)
    audio.rebuild(project)
    chunks = np.concatenate([audio.samples(first, 2205) for first in range(0, 35_280, 2205)])
    assert np.array_equal(chunks, audio.samples(0, 35_280))


def test_audio_follows_settings(audio, sound_project):
    track = sound_project.tracks[2]
    audio.rebuild(sound_project)
    loud = abs(audio.samples(SAMPLE_RATE, 4410)).max()
    track.clips[0].audio.volume = 50
    audio.rebuild(sound_project)
    assert abs(audio.samples(SAMPLE_RATE, 4410)).max() == pytest.approx(loud / 2, rel=0.02)
    track.clips[0].audio.muted = True
    audio.rebuild(sound_project)
    assert not audio.samples(SAMPLE_RATE, 4410).any()
    track.clips[0].audio.muted = False
    track.hidden = True
    audio.rebuild(sound_project)
    assert not audio.samples(SAMPLE_RATE, 4410).any()


def test_audio_missing_file_keeps_other_sounds(audio, sound_project, media_files, tmp_path):
    video = Media.from_file(media_files["video"])
    sound_project.place(video)
    video.path = tmp_path / "disparu.mp4"
    audio.rebuild(sound_project)
    assert len(audio.sounds) == 1
    assert audio.samples(SAMPLE_RATE, 4410).any()
