"""Tâches longues lancées dans un thread, pour que la fenêtre ne gèle pas."""

import copy
import threading

from proglog import ProgressBarLogger
from PyQt6.QtCore import QThread, pyqtSignal

from model.export import ExportCancelledError, ExportSettings, estimate_size, export
from model.media import Media
from model.preview import CHANNELS, SAMPLE_RATE, AudioRenderer, PreviewRenderer
from model.project import Project

BYTES_PER_SAMPLE = 2 * CHANNELS
AUDIO_CHUNK = SAMPLE_RATE // 20
# avance prise sur la lecture : assez pour ne pas couper, pas trop pour entendre vite un réglage modifié
AUDIO_AHEAD = SAMPLE_RATE // 4 * BYTES_PER_SAMPLE


class PreviewWorker(QThread):
    """Ne garde que la dernière demande : si on avance plus vite qu'il ne calcule, des images sont sautées."""

    frame_ready = pyqtSignal(object)  # image RGB (tableau NumPy) ou None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = PreviewRenderer()
        self._condition = threading.Condition()
        self._project = None
        self._time = None
        self._stopping = False

    def rebuild(self, project: Project):
        # une copie : le thread principal peut modifier le projet pendant qu'on l'assemble
        snapshot = copy.deepcopy(project)
        with self._condition:
            self._project = snapshot
            self._condition.notify()

    def request(self, time: float):
        with self._condition:
            self._time = time
            self._condition.notify()

    def stop(self):
        with self._condition:
            self._stopping = True
            self._condition.notify()
        self.wait()

    def run(self):
        while True:
            with self._condition:
                while not self._stopping and self._project is None and self._time is None:
                    self._condition.wait()
                if self._stopping:
                    break
                project, self._project = self._project, None
                time, self._time = self._time, None
            try:
                if project is not None:
                    self.renderer.rebuild(project)
                if time is not None:
                    self.frame_ready.emit(self.renderer.frame(time))
            except Exception:
                # fichier déplacé, vidéo abîmée… : sans ça le thread meurt et l'aperçu ne bouge plus
                self.renderer.close()
                self.frame_ready.emit(None)
        self.renderer.close()


class AudioWorker(QThread):
    """Prépare le son un peu en avance sur la lecture. AudioPlayer le récupère avec take()."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = AudioRenderer()
        self._condition = threading.Condition()
        self._project = None
        self._playing = False
        self._stopping = False
        self._next = 0  # prochain échantillon à calculer
        self._generation = 0  # change à chaque saut, pour jeter un morceau calculé avant
        self._buffer = bytearray()

    def rebuild(self, project: Project):
        snapshot = copy.deepcopy(project)
        with self._condition:
            self._project = snapshot
            self._condition.notify()

    def play(self, seconds: float):
        with self._condition:
            self._generation += 1
            self._next = round(seconds * SAMPLE_RATE)
            self._buffer.clear()
            self._playing = True
            self._condition.notify()

    def pause(self):
        with self._condition:
            self._generation += 1
            self._playing = False
            self._buffer.clear()

    def take(self, size: int) -> bytes:
        with self._condition:
            size = min(size, len(self._buffer))
            size -= size % BYTES_PER_SAMPLE
            data = bytes(self._buffer[:size])
            del self._buffer[:size]
            self._condition.notify()
        return data

    def stop(self):
        with self._condition:
            self._stopping = True
            self._condition.notify()
        self.wait()

    def _has_work(self) -> bool:
        return self._stopping or self._project is not None or (self._playing and len(self._buffer) < AUDIO_AHEAD)

    def run(self):
        while True:
            with self._condition:
                self._condition.wait_for(self._has_work)
                if self._stopping:
                    break
                project, self._project = self._project, None
                playing, first, generation = self._playing, self._next, self._generation
            if project is not None:
                self.renderer.rebuild(project)
            if not playing:
                continue
            data = self.renderer.samples(first, AUDIO_CHUNK).tobytes()
            with self._condition:
                if generation == self._generation:
                    self._buffer += data
                    self._next += AUDIO_CHUNK
        self.renderer.close()


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
