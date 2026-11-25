import pytest

from model.media import Media
from model.preview import PreviewRenderer
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
