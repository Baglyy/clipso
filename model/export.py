"""Export du projet : moviepy assemble les clips, FFmpeg encode."""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    afx,
)

from model.effects import animate_text, apply_blur, apply_filters
from model.project import Clip, Project, even
from model.settings import AudioSettings

FORMATS = ("mp4", "mov", "webm", "gif")
CODECS = {"mp4": ("libx264", "aac"), "mov": ("libx264", "aac"), "webm": ("libvpx-vp9", "libvorbis")}
FONTS_FOLDER = Path(__file__).parent.parent / "assets" / "fonts"
FONT_FILES = {
    "Nunito Black": "Nunito-Black.ttf",
    "Nunito": "Nunito-Regular.ttf",
    "JetBrains Mono": "JetBrainsMono-Bold.ttf",
}
# au-delà, les navigateurs ralentissent les GIF
GIF_MAX_FPS = 25
TEXT_MARGIN = 0.05
TEXT_CENTER_Y = 0.76  # comme dans la preview
SAMPLES = 3
SAMPLE_DURATION = 1.0


class ExportCancelledError(Exception):
    pass


@dataclass
class ExportSettings:
    folder: Path
    file_name: str
    format: str = "mp4"
    resolution: int = 1080
    fps: int = 30
    quality: int = 80  # de 10 à 100

    @property
    def path(self) -> Path:
        name = self.file_name.strip() or "export"
        # « Vacances.mp4 » exporté en WebM → « Vacances.webm »
        if Path(name).suffix.lower().lstrip(".") in FORMATS:
            name = Path(name).stem
        return self.folder / f"{name}.{self.format}"

    @property
    def output_fps(self) -> int:
        return min(self.fps, GIF_MAX_FPS) if self.format == "gif" else self.fps


def crf(settings: ExportSettings) -> int:
    # CRF de FFmpeg : plus il est petit, meilleure est l'image
    if settings.format == "webm":
        return round(50 - settings.quality * 0.35)
    return round(38 - settings.quality * 0.2)


def gif_colors(settings: ExportSettings) -> int:
    return 16 + round(settings.quality * 2.4)


def export(project: Project, settings: ExportSettings, logger="bar") -> Path:
    if project.duration == 0:
        raise ValueError("Le projet est vide : ajoutez des médias avant d'exporter.")
    settings.folder.mkdir(parents=True, exist_ok=True)
    path = settings.path
    try:
        _render(project, settings, path, 0, project.duration, logger)
    except BaseException:
        # on ne laisse pas un fichier à moitié écrit
        path.unlink(missing_ok=True)
        raise
    return path


def estimate_size(project: Project, settings: ExportSettings, logger=None) -> int:
    """Estime la taille en octets en encodant quelques extraits d'une seconde."""
    duration = project.duration
    if duration == 0:
        return 0
    if duration <= SAMPLES * SAMPLE_DURATION:
        ranges = [(0, duration)]
    else:
        starts = [(i + 0.5) * duration / SAMPLES - SAMPLE_DURATION / 2 for i in range(SAMPLES)]
        ranges = [(start, start + SAMPLE_DURATION) for start in starts]
    total = 0
    with tempfile.TemporaryDirectory() as folder:
        for index, (start, end) in enumerate(ranges):
            sample = Path(folder) / f"extrait{index}.{settings.format}"
            _render(project, settings, sample, start, end, logger)
            total += sample.stat().st_size
    encoded = sum(end - start for start, end in ranges)
    return int(total * duration / encoded)


def preview_frame(project: Project, time: float, resolution: int = 120) -> np.ndarray:
    sources = []
    try:
        video = build_video(project, project.frame_size(resolution), sources)
        return video.get_frame(min(time, project.duration - 0.01)).astype(np.uint8)
    finally:
        close_sources(sources)


def _render(project: Project, settings: ExportSettings, path: Path, start: float, end: float, logger):
    sources = []  # fichiers ouverts à refermer
    try:
        video = build_video(project, project.frame_size(settings.resolution), sources)
        if (start, end) != (0, project.duration):
            video = video.subclipped(start, end)
        if settings.format == "gif":
            _write_gif(video, settings, path, logger)
            return
        codec, audio_codec = CODECS[settings.format]
        params = ["-crf", str(crf(settings))]
        if codec == "libvpx-vp9":
            # VP9 n'utilise le CRF que si on ne lui impose pas de débit
            params += ["-b:v", "0"]
        video.write_videofile(
            str(path),
            fps=settings.fps,
            codec=codec,
            audio_codec=audio_codec,
            ffmpeg_params=params,
            temp_audiofile_path=str(path.parent),
            logger=logger,
        )
    finally:
        close_sources(sources)


def _write_gif(video, settings: ExportSettings, path: Path, logger):
    # en deux passes : FFmpeg calcule une palette de couleurs, puis l'utilise (bien plus léger que moviepy)
    dither = "sierra2_4a" if settings.quality >= 70 else "bayer:bayer_scale=4"
    palette = (
        f"split[a][b];[a]palettegen=max_colors={gif_colors(settings)}:stats_mode=diff[p];"
        f"[b][p]paletteuse=dither={dither}"
    )
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "source.mp4"
        video.write_videofile(
            str(source),
            fps=settings.output_fps,
            codec="libx264",
            audio=False,
            ffmpeg_params=["-crf", "12"],
            logger=logger,
        )
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        command = [ffmpeg, "-y", "-loglevel", "error", "-i", str(source), "-vf", palette, str(path)]
        subprocess.run(command, check=True, capture_output=True)


def build_video(project: Project, size: tuple[int, int], sources: list) -> CompositeVideoClip:
    """Les fichiers ouverts sont ajoutés à sources : à refermer avec close_sources()."""
    layers = [ColorClip(size, color=(0, 0, 0), duration=project.duration)]
    reference = project.frame_size()
    sounds = []
    # la première piste est au-dessus, donc on empile à partir de la dernière
    for track in reversed(project.tracks):
        for clip in track.clips:
            # une piste vidéo masquée garde son son
            if clip.kind != "audio" and not track.hidden:
                layers.append(_picture(clip, size, reference, sources))
            if clip.kind in ("audio", "video") and not (track.hidden and track.kind == "audio"):
                sound = _sound(clip, sources)
                if sound is not None:
                    sounds.append(sound)

    video = CompositeVideoClip(layers, size=size).with_duration(project.duration)
    if sounds:
        video = video.with_audio(CompositeAudioClip(sounds).with_duration(project.duration))
    return video


def _picture(clip: Clip, size: tuple[int, int], reference: tuple[int, int], sources: list):
    if clip.kind == "text":
        layer = animate_text(_text(clip, size), clip.text_style.animation)
        return layer.with_duration(clip.duration).with_start(clip.start)

    if clip.kind == "video":
        media = clip.media
        # FFmpeg redimensionne pendant le décodage : 4 fois plus rapide que de réduire du 1080p après coup
        target = None
        if media.width and media.height:
            factor = min(size[0] / media.width, size[1] / media.height)
            target = (even(media.width * factor), even(media.height * factor))
        source = VideoFileClip(str(media.path), audio=False, target_resolution=target)
        sources.append(source)
        layer = source.subclipped(clip.in_point, clip.in_point + clip.duration)
        position = "center"
    else:
        settings = clip.image
        layer = ImageClip(str(clip.media.path))
        factor = image_factor(layer.w, layer.h, clip, size, reference)
        if factor != 1:
            layer = layer.resized(factor)
        if settings.rotation:
            if layer.mask is None:
                # sinon les coins ajoutés par la rotation sont noirs
                layer = layer.with_mask()
            # angle positif = sens des aiguilles d'une montre
            layer = layer.rotated(-settings.rotation, expand=True)
        if settings.opacity < 100:
            layer = layer.with_opacity(settings.opacity / 100)
        # TODO: issue « Modes de fusion » : appliquer settings.blend (produit, écran, incrustation)
        position = (size[0] * settings.x / 100 - layer.w / 2, size[1] * settings.y / 100 - layer.h / 2)

    if not clip.filters.is_neutral or clip.blur.intensity:
        filters, blur = clip.filters, clip.blur
        layer = layer.image_transform(lambda frame: apply_blur(apply_filters(frame, filters), blur))
    return layer.with_duration(clip.duration).with_start(clip.start).with_position(position)


def _text(clip: Clip, size: tuple[int, int]):
    style = clip.text_style
    font_size = max(8, round(style.size * min(size) / 1080))
    layer = TextClip(
        font=str(FONTS_FOLDER / FONT_FILES.get(style.font, FONT_FILES["Nunito Black"])),
        text=clip.text,
        font_size=font_size,
        color=style.color,
        stroke_color="black",
        stroke_width=max(1, font_size // 40),
        text_align=style.align,
        # sans cette marge, moviepy coupe le bas des lettres (g, p, q…)
        margin=(10, font_size // 3),
    )
    margin = size[0] * TEXT_MARGIN
    x = {"left": margin, "right": size[0] - margin - layer.w}.get(style.align, (size[0] - layer.w) / 2)
    return layer.with_position((x, size[1] * TEXT_CENTER_Y - layer.h / 2))


def _sound(clip: Clip, sources: list):
    if clip.audio.muted or not clip.media.has_audio:
        return None
    source = AudioFileClip(str(clip.media.path))
    sources.append(source)
    sound = source.subclipped(clip.in_point, clip.in_point + clip.duration)
    return _apply_audio(sound, clip.audio, clip.media.max_volume, clip.duration).with_start(clip.start)


def _apply_audio(sound, settings: AudioSettings, max_volume: float, duration: float):
    effects = []
    volume = settings.volume / 100
    if settings.normalize:
        volume = volume / max_volume
    if volume != 1:
        effects.append(afx.MultiplyVolume(volume))
    if settings.fade_in:
        effects.append(afx.AudioFadeIn(min(settings.fade_in, duration)))
    if settings.fade_out:
        effects.append(afx.AudioFadeOut(min(settings.fade_out, duration)))
    return sound.with_effects(effects) if effects else sound


def image_factor(width: int, height: int, clip: Clip, size: tuple[int, int], reference: tuple[int, int]) -> float:
    """Calculé dans l'image du projet (reference) puis ramené à size, pour qu'un logo occupe
    la même place en 360p (aperçu) qu'en 1080p (export)."""
    fit = min(reference[0] / width, reference[1] / height, 1)
    return fit * clip.image.scale / 100 * size[0] / reference[0]


def close_sources(sources: list):
    for source in sources:
        source.close()
