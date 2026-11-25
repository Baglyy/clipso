"""Lecture du son de l'aperçu sur la carte son."""

import time

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtMultimedia import QAudio, QAudioFormat, QAudioSink, QMediaDevices

from controller.workers import BYTES_PER_SAMPLE, AudioWorker
from model.preview import CHANNELS, SAMPLE_RATE
from model.project import Project

FEED_INTERVAL = 20  # en millisecondes
SINK_BUFFER = SAMPLE_RATE // 5 * BYTES_PER_SAMPLE


class AudioPlayer(QObject):
    """Sert aussi d'horloge à la lecture : l'image suit le son, sinon ils se décalent peu à peu.
    Sans carte son, c'est l'horloge de l'ordinateur qui est utilisée."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = AudioWorker()
        self.playing = False
        self.muted = False
        self._project = None
        self._changed = False
        self._sink = None
        self._device = None
        self._start = 0.0
        self._started_at = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(FEED_INTERVAL)
        self._timer.timeout.connect(self._feed)
        self.worker.start()

    def set_project(self, project: Project):
        """À appeler à chaque modification du projet."""
        self._project = project
        self._changed = True
        # en pause, inutile de rouvrir les fichiers à chaque réglage : on attend la lecture
        if self.playing:
            self._rebuild()

    def play(self, seconds: float):
        self._close_sink()
        if self._changed:
            self._rebuild()
        self.playing = True
        self._start = seconds
        self._started_at = time.monotonic()
        self._sink = create_sink()
        if self._sink is not None:
            self._sink.setVolume(0.0 if self.muted else 1.0)
            self._device = self._sink.start()
            self.worker.play(seconds)
            self._timer.start()

    def pause(self):
        self.playing = False
        self.worker.pause()
        self._close_sink()

    def position(self) -> float:
        if self._sink is not None and self._sink.error() == QAudio.Error.FatalError:
            self._use_computer_clock()
        if self._sink is not None:
            return self._start + self._sink.processedUSecs() / 1_000_000
        return self._start + time.monotonic() - self._started_at

    def set_muted(self, muted: bool):
        self.muted = muted
        if self._sink is not None:
            self._sink.setVolume(0.0 if muted else 1.0)

    def close(self):
        self.pause()
        self.worker.stop()

    def _rebuild(self):
        self._changed = False
        self.worker.rebuild(self._project)

    def _feed(self):
        if self._device is None:
            return
        data = self.worker.take(self._sink.bytesFree())
        if data:
            self._device.write(data)

    def _use_computer_clock(self):
        # casque débranché… : l'image continue là où le son s'est arrêté
        self._start += self._sink.processedUSecs() / 1_000_000
        self._started_at = time.monotonic()
        self.worker.pause()
        self._close_sink()

    def _close_sink(self):
        self._timer.stop()
        self._device = None
        if self._sink is not None:
            # reset() coupe tout de suite, stop() jouerait d'abord la fin du tampon
            self._sink.reset()
            self._sink.deleteLater()
            self._sink = None


def create_sink() -> QAudioSink | None:
    audio_format = QAudioFormat()
    audio_format.setSampleRate(SAMPLE_RATE)
    audio_format.setChannelCount(CHANNELS)
    audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
    output = QMediaDevices.defaultAudioOutput()
    if output.isNull() or not output.isFormatSupported(audio_format):
        return None
    sink = QAudioSink(output, audio_format)
    sink.setBufferSize(SINK_BUFFER)
    return sink
