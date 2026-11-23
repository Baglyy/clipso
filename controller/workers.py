"""Tâches longues lancées dans un thread, pour que la fenêtre ne gèle pas."""

from proglog import ProgressBarLogger
from PyQt6.QtCore import QThread, pyqtSignal

from model.export import ExportCancelledError, ExportSettings, estimate_size, export
from model.media import Media
from model.project import Project


class ImportWorker(QThread):
    imported = pyqtSignal(object)  # Media
    failed = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # fichiers lus, total

    def __init__(self, paths: list[str], parent=None):
        super().__init__(parent)
        self.paths = paths

    def run(self):
        for index, path in enumerate(self.paths):
            try:
                self.imported.emit(Media.from_file(path))
            except ValueError as error:
                self.failed.emit(str(error))
            self.progress.emit(index + 1, len(self.paths))


class ExportWorker(QThread):
    progress = pyqtSignal(int)  # de 0 à 100
    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, project: Project, settings: ExportSettings, parent=None):
        super().__init__(parent)
        self.project = project
        self.settings = settings
        self.logger = ProgressLogger(self.progress.emit)

    def cancel(self):
        self.logger.cancelled = True

    def run(self):
        try:
            path = export(self.project, self.settings, logger=self.logger)
        except ExportCancelledError:
            self.cancelled.emit()
        except Exception as error:
            self.failed.emit(str(error))
        else:
            self.succeeded.emit(str(path))


class EstimateWorker(QThread):
    estimated = pyqtSignal(int)

    def __init__(self, project: Project, settings: ExportSettings, parent=None):
        super().__init__(parent)
        self.project = project
        self.settings = settings
        self.logger = ProgressLogger()

    def cancel(self):
        self.logger.cancelled = True

    def run(self):
        try:
            self.estimated.emit(estimate_size(self.project, self.settings, logger=self.logger))
        except Exception:
            # pas grave : la taille reste « calcul… »
            pass


class ProgressLogger(ProgressBarLogger):
    """Reçoit l'avancement de moviepy. Si cancelled passe à True, l'export s'arrête à l'image suivante."""

    def __init__(self, on_progress=None):
        super().__init__()
        self.on_progress = on_progress
        self.cancelled = False

    def bars_callback(self, bar, attr, value, old_value=None):
        if self.cancelled:
            raise ExportCancelledError()
        if bar == "frame_index" and attr == "index" and self.on_progress:
            total = self.bars[bar]["total"]
            if total:
                self.on_progress(int(100 * value / total))
