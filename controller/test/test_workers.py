import pytest

from controller.workers import EstimateWorker, ExportWorker, ImportWorker, ProgressLogger
from model.export import ExportCancelledError, ExportSettings
from model.media import Media
from model.project import Project


def test_progress_logger_reports_percent():
    received = []
    logger = ProgressLogger(received.append)
    for _ in logger.iter_bar(frame_index=range(4)):
        pass
    assert received[-1] == 100
    assert received == sorted(received)


def test_progress_logger_ignores_audio_bar():
    received = []
    logger = ProgressLogger(received.append)
    for _ in logger.iter_bar(chunk=range(4)):
        pass
    assert received == []


def test_progress_logger_cancel():
    logger = ProgressLogger()
    logger.cancelled = True
    with pytest.raises(ExportCancelledError):
        for _ in logger.iter_bar(frame_index=range(4)):
            pass


def test_import_worker(media_files, tmp_path):
    worker = ImportWorker([str(media_files["image"]), str(tmp_path / "notes.txt")])
    imported, failed, progress = [], [], []
    worker.imported.connect(imported.append)
    worker.failed.connect(failed.append)
    worker.progress.connect(lambda done, total: progress.append((done, total)))
    worker.run()
    assert [media.name for media in imported] == ["logo.png"]
    assert "notes.txt" in failed[0]
    assert progress == [(1, 2), (2, 2)]


@pytest.fixture
def project(media_files):
    project = Project()
    media = Media.from_file(media_files["video"])
    project.add_media(media)
    project.place(media)
    return project


def test_export_worker_success(project, tmp_path):
    worker = ExportWorker(project, ExportSettings(tmp_path, "film", resolution=90, fps=10))
    done, progress = [], []
    worker.succeeded.connect(done.append)
    worker.progress.connect(progress.append)
    worker.run()
    assert done == [str(tmp_path / "film.mp4")]
    assert progress[-1] >= 90


def test_export_worker_failure(tmp_path):
    worker = ExportWorker(Project(), ExportSettings(tmp_path, "film"))
    errors = []
    worker.failed.connect(errors.append)
    worker.run()
    assert "vide" in errors[0]


def test_export_worker_cancel(project, tmp_path):
    worker = ExportWorker(project, ExportSettings(tmp_path, "film", resolution=90, fps=10))
    cancelled = []
    worker.cancelled.connect(lambda: cancelled.append(True))
    worker.cancel()
    worker.run()
    assert cancelled == [True]
    assert not (tmp_path / "film.mp4").exists()


def test_estimate_worker(project, tmp_path):
    worker = EstimateWorker(project, ExportSettings(tmp_path, "film", resolution=90, fps=10))
    sizes = []
    worker.estimated.connect(sizes.append)
    worker.run()
    assert sizes[0] > 0


def test_estimate_worker_cancelled_says_nothing(project, tmp_path):
    worker = EstimateWorker(project, ExportSettings(tmp_path, "film", resolution=90, fps=10))
    sizes = []
    worker.estimated.connect(sizes.append)
    worker.cancel()
    worker.run()
    assert sizes == []
