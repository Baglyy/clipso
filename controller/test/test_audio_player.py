import pytest
from PyQt6.QtMultimedia import QAudio

import controller.audio_player as audio_player
from controller.audio_player import AudioPlayer
from model.media import Media
from model.project import Project


class FakeSink:
    def __init__(self):
        self.written = bytearray()
        self.processed = 0
        self.volume = None
        self.fatal = False

    def start(self):
        return self

    def write(self, data):
        self.written += data

    def bytesFree(self):
        return max(0, 100_000 - len(self.written))

    def processedUSecs(self):
        return self.processed

    def error(self):
        return QAudio.Error.FatalError if self.fatal else QAudio.Error.NoError

    def setVolume(self, volume):
        self.volume = volume

    def reset(self):
        pass

    def deleteLater(self):
        pass


@pytest.fixture
def sinks(monkeypatch):
    created = []

    def create():
        created.append(FakeSink())
        return created[-1]

    monkeypatch.setattr(audio_player, "create_sink", create)
    return created


@pytest.fixture
def player(sinks):
    audio = AudioPlayer()
    yield audio
    audio.close()
    assert not audio.worker.isRunning()


@pytest.fixture
def project(media_files):
    project = Project()
    media = Media.from_file(media_files["audio"])
    project.add_media(media)
    project.place(media)
    return project


def test_sound_is_sent_to_sink(player, project, sinks, qtbot):
    player.set_project(project)
    player.play(0)
    qtbot.waitUntil(lambda: any(sinks[0].written), timeout=30_000)


def test_position_follows_sound_card(player, sinks):
    player.play(2.0)
    assert player.position() == 2.0
    sinks[0].processed = 500_000
    assert player.position() == 2.5
    player.play(10.0)
    assert len(sinks) == 2
    assert player.position() == 10.0


def test_mute_is_kept_for_next_playback(player, sinks):
    player.play(0)
    assert sinks[0].volume == 1.0
    player.set_muted(True)
    assert sinks[0].volume == 0.0
    player.play(0)
    assert sinks[1].volume == 0.0


def test_lost_device_falls_back_on_computer_clock(player, sinks, qtbot):
    player.play(1.0)
    sinks[0].processed = 500_000
    sinks[0].fatal = True
    qtbot.wait(50)
    first = player.position()
    qtbot.wait(50)
    assert 1.5 <= first < player.position()


def test_without_sound_card(player, monkeypatch, qtbot):
    monkeypatch.setattr(audio_player, "create_sink", lambda: None)
    player.play(3.0)
    qtbot.wait(50)
    assert 3.0 < player.position() < 10


def test_changes_during_playback_are_heard(player, project, sinks, qtbot):
    player.set_project(project)
    player.play(0)
    qtbot.waitUntil(lambda: len(player.worker.renderer.sounds) == 1, timeout=30_000)
    project.tracks[2].clips[0].audio.muted = True
    player.set_project(project)
    qtbot.waitUntil(lambda: player.worker.renderer.sounds == [], timeout=30_000)
