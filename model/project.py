"""Projet de montage : ses médias et ses pistes de clips."""

from dataclasses import dataclass, field
from pathlib import Path

from model.media import Media
from model.settings import AudioSettings, Blur, Filters, ImageSettings, TextStyle

ASPECTS = {"16:9": (16, 9), "9:16": (9, 16), "1:1": (1, 1)}
IMAGE_DURATION = 5.0
# pistes acceptées pour chaque type de média, la première est celle par défaut
TRACKS_FOR_MEDIA = {"video": ("video", "overlay"), "image": ("overlay", "video"), "audio": ("audio",)}


@dataclass
class Clip:
    start: float
    duration: float
    media: Media | None = None  # None pour un clip texte
    in_point: float = 0.0  # début du clip dans le fichier source
    text: str = ""
    text_style: TextStyle = field(default_factory=TextStyle)
    image: ImageSettings = field(default_factory=ImageSettings)
    filters: Filters = field(default_factory=Filters)
    blur: Blur = field(default_factory=Blur)
    audio: AudioSettings = field(default_factory=AudioSettings)

    @property
    def kind(self) -> str:
        return self.media.kind if self.media else "text"

    @property
    def name(self) -> str:
        return self.media.name if self.media else f"Titre « {self.text} »"

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass
class Track:
    name: str
    kind: str  # "overlay", "video" ou "audio"
    clips: list[Clip] = field(default_factory=list)
    hidden: bool = False
    locked: bool = False

    @property
    def end(self) -> float:
        return max((clip.end for clip in self.clips), default=0.0)

    def free_start(self, start: float, duration: float) -> float:
        """Premier moment à partir de start où le clip tient sans chevaucher les autres."""
        for clip in sorted(self.clips, key=lambda c: c.start):
            if clip.end <= start:
                continue
            if clip.start >= start + duration:
                break
            start = clip.end
        return start


@dataclass
class Project:
    name: str = "Projet sans titre"
    aspect: str = "16:9"
    resolution: int = 1080  # petit côté de l'image
    fps: int = 30
    media: list[Media] = field(default_factory=list)
    tracks: list[Track] = field(
        default_factory=lambda: [Track("Vidéo 2", "overlay"), Track("Vidéo 1", "video"), Track("Audio 1", "audio")]
    )

    @property
    def duration(self) -> float:
        return max((track.end for track in self.tracks), default=0.0)

    def frame_size(self, resolution: int | None = None) -> tuple[int, int]:
        # les codecs vidéo veulent des dimensions paires
        short_side = resolution or self.resolution
        width, height = ASPECTS[self.aspect]
        scale = short_side / min(width, height)
        return _even(width * scale), _even(height * scale)

    def is_used(self, media: Media) -> bool:
        return any(clip.media is media for track in self.tracks for clip in track.clips)

    def has_media(self, path: str | Path) -> bool:
        path = Path(path).resolve()
        return any(media.path.resolve() == path for media in self.media)

    def add_media(self, media: Media):
        self.media.append(media)

    def place(self, media: Media, track: Track | None = None, start: float | None = None) -> Clip:
        """Pose le média sur une piste (par défaut à la fin de sa piste). Si la place est prise, le clip est décalé."""
        accepted = TRACKS_FOR_MEDIA[media.kind]
        if track is None:
            track = next(track for track in self.tracks if track.kind == accepted[0])
        if track.kind not in accepted:
            raise ValueError(f"{media.name} ne peut pas aller sur la piste {track.name}.")
        if track.locked:
            raise ValueError(f"La piste {track.name} est verrouillée.")
        duration = media.duration or IMAGE_DURATION
        start = track.end if start is None else max(0.0, start)
        clip = Clip(track.free_start(start, duration), duration, media)
        track.clips.append(clip)
        return clip


def _even(value: float) -> int:
    return int(round(value / 2)) * 2
