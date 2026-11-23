"""Controller principal : relie la fenêtre (view) au projet (model)."""

from dataclasses import asdict
from pathlib import Path

from PyQt6.QtCore import QStandardPaths, Qt, QTimer
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QProgressDialog

from controller.workers import EstimateWorker, ExportWorker, ImportWorker
from model.export import ExportSettings, preview_frame
from model.media import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from model.project import Project
from model.settings import AudioSettings, Blur, Filters, ImageSettings, TextStyle
from view.dialogs.export_dialog import ExportDialog
from view.format import mm_ss
from view.main_window import MainWindow

EXTENSIONS = sorted(VIDEO_EXTENSIONS | AUDIO_EXTENSIONS | IMAGE_EXTENSIONS)
MEDIA_FILTER = "Médias (" + " ".join("*" + extension for extension in EXTENSIONS) + ")"
MEDIA_COLORS = ["#5B7898", "#AE7657", "#4E8885", "#6A8A5A", "#76604F", "#C9A27E", "#D9B8C8"]
SETTINGS_CLASSES = {"image": ImageSettings, "filters": Filters, "blur": Blur, "audio": AudioSettings}


class AppController:
    def __init__(self, window: MainWindow):
        self.window = window
        self.editor = window.editor_page
        self.project = Project()
        self.selected_clip = None
        self.selected_view_clip = None
        # pour retrouver le clip du model à partir du dict affiché dans la timeline
        self.view_clips = {}
        self.import_errors = []
        self.import_worker = None
        self.export_worker = None
        self.estimate_worker = None

        home = window.home_page
        self.aspect_buttons = {
            home.formatLandscapeButton: "16:9",
            home.formatVerticalButton: "9:16",
            home.formatSquareButton: "1:1",
        }
        home.createProjectButton.clicked.connect(self.new_project)
        home.importMediaButton.clicked.connect(self.new_project_from_media)
        # TODO: openProjectButton et projets récents, quand les projets seront enregistrés en .json

        self.editor.mediaPanel.importButton.clicked.connect(self.import_media)
        self.editor.mediaPanel.media_activated.connect(self.place_media)
        self.editor.timeline.media_dropped.connect(self.drop_media)
        self.editor.timeline.clip_selected.connect(self.select_clip)
        self.editor.timelinePanel.track_hidden_toggled.connect(self.set_track_hidden)
        self.editor.timelinePanel.track_locked_toggled.connect(self.set_track_locked)
        self.editor.propertiesPanel.settings_changed.connect(self.change_settings)
        self.editor.export_requested.connect(self.show_export)

    # Projet

    def new_project(self):
        aspect = "16:9"
        for button, value in self.aspect_buttons.items():
            if button.isChecked():
                aspect = value
        self.project = Project(aspect=aspect)
        self.selected_clip = None
        self.refresh()
        self.window.show_editor()

    def new_project_from_media(self):
        self.new_project()
        self.import_media()

    def refresh(self):
        project = self.project
        thumbnails = {}
        media_list = []
        for index, media in enumerate(project.media):
            thumbnails[id(media)] = to_qimage(media.thumbnail)
            media_list.append(
                {
                    "index": index,
                    "name": media.name,
                    "kind": media.kind,
                    "duration": "" if media.kind == "image" else mm_ss(media.duration),
                    "color": MEDIA_COLORS[index % len(MEDIA_COLORS)],
                    "thumbnail": thumbnails[id(media)],
                    "peaks": media.peaks,
                    "used": project.is_used(media),
                }
            )

        self.view_clips = {}
        selected_view_clip = None
        tracks = []
        for track in project.tracks:
            clips = []
            for clip in track.clips:
                view_clip = {
                    "kind": clip.kind,
                    "name": clip.name,
                    "start": clip.start,
                    "duration": clip.duration,
                    "text": clip.text,
                }
                if clip.media:
                    view_clip["color"] = MEDIA_COLORS[project.media.index(clip.media) % len(MEDIA_COLORS)]
                    view_clip["thumbnail"] = thumbnails[id(clip.media)]
                    view_clip["peaks"] = clip_peaks(clip)
                clips.append(view_clip)
                self.view_clips[id(view_clip)] = clip
                if clip is self.selected_clip:
                    selected_view_clip = view_clip
            tracks.append(
                {"name": track.name, "kind": track.kind, "hidden": track.hidden, "locked": track.locked, "clips": clips}
            )

        self.editor.load_project(project.name, media_list, tracks, project.duration, self.editor.timeline.position)
        self.editor.previewPanel.set_format(project.aspect, project.resolution, project.fps)
        if selected_view_clip:
            self.editor.select_clip(selected_view_clip)

    # Import

    def import_media(self):
        paths, _ = QFileDialog.getOpenFileNames(self.window, "Importer des médias", str(Path.home()), MEDIA_FILTER)
        if paths:
            self.add_media(paths)

    def add_media(self, paths: list[str]):
        self.import_errors = []
        new_paths = []
        for path in paths:
            if self.project.has_media(path) or path in new_paths:
                self.import_errors.append(f"{Path(path).name} est déjà importé")
            else:
                new_paths.append(path)
        if not new_paths:
            self.show_import_errors()
            return

        worker = ImportWorker(new_paths, self.window)
        worker.imported.connect(self.media_imported)
        worker.failed.connect(self.import_errors.append)
        worker.progress.connect(self.editor.mediaPanel.set_importing)
        worker.finished.connect(self.import_finished)
        self.import_worker = worker
        self.editor.mediaPanel.set_importing(0, len(new_paths))
        worker.start()

    def media_imported(self, media):
        self.project.add_media(media)
        self.refresh()

    def import_finished(self):
        self.import_worker.deleteLater()
        self.import_worker = None
        self.show_import_errors()

    def show_import_errors(self):
        if self.import_errors:
            message = "Certains fichiers n'ont pas été importés :\n\n" + "\n".join(self.import_errors)
            QMessageBox.warning(self.window, "Import", message)

    # Timeline

    def place_media(self, index: int):
        self.try_place(index, None, None)

    def drop_media(self, index: int, track_index: int, seconds: float):
        self.try_place(index, self.project.tracks[track_index], seconds)

    def try_place(self, index, track, start):
        try:
            self.project.place(self.project.media[index], track, start)
        except ValueError as error:
            QMessageBox.warning(self.window, "Timeline", str(error))
            return
        self.refresh()

    def set_track_hidden(self, index: int, hidden: bool):
        self.project.tracks[index].hidden = hidden

    def set_track_locked(self, index: int, locked: bool):
        self.project.tracks[index].locked = locked

    # Propriétés

    def select_clip(self, view_track: dict, view_clip: dict):
        clip = self.view_clips.get(id(view_clip))
        if clip is None:
            return
        self.selected_clip = clip
        self.selected_view_clip = view_clip
        text_values = asdict(clip.text_style)
        text_values["text"] = clip.text
        panel = self.editor.propertiesPanel
        panel.set_values(
            {
                "text": text_values,
                "image": asdict(clip.image),
                "filters": asdict(clip.filters),
                "blur": asdict(clip.blur),
                "audio": asdict(clip.audio),
            }
        )
        if clip.kind == "image":
            media = clip.media
            info = f"{media.path.suffix[1:].upper()} · {media.width} × {media.height}"
            panel.imagePage.set_image(media.name, info, to_qimage(media.thumbnail))

    def change_settings(self, tab: str, values: dict):
        clip = self.selected_clip
        if clip is None:
            return
        if tab == "text":
            clip.text = values.pop("text")
            clip.text_style = TextStyle(**values)
            # on met à jour juste le clip affiché, sinon le curseur de la zone de texte sauterait
            self.selected_view_clip["text"] = clip.text
            self.selected_view_clip["name"] = clip.name
            self.editor.timeline.update()
            self.editor.seek(self.editor.timeline.position)
        else:
            setattr(clip, tab, SETTINGS_CLASSES[tab](**values))

    # Export

    def show_export(self):
        project = self.project
        if project.duration == 0:
            QMessageBox.information(self.window, "Export", "Le projet est vide : importez des médias avant d'exporter.")
            return

        dialog = ExportDialog(self.window)
        dialog.set_project(
            project.name, project.duration, project.aspect, project.resolution, project.fps, str(default_folder())
        )
        dialog.set_thumbnail(to_qimage(preview_frame(project, project.duration / 2)))

        # on attend que l'utilisateur ait fini de bouger le curseur avant de relancer le calcul
        timer = QTimer(dialog)
        timer.setSingleShot(True)
        timer.setInterval(400)
        timer.timeout.connect(lambda: self.start_estimate(dialog))
        dialog.settings_changed.connect(timer.start)
        self.start_estimate(dialog)

        accepted = dialog.exec()
        timer.stop()
        self.stop_estimate()
        if accepted:
            self.start_export(settings_from(dialog))

    def start_estimate(self, dialog: ExportDialog):
        self.stop_estimate()
        dialog.set_estimated_size(None)
        worker = EstimateWorker(self.project, settings_from(dialog), self.window)
        worker.estimated.connect(dialog.set_estimated_size)
        self.estimate_worker = worker
        worker.start()

    def stop_estimate(self):
        if self.estimate_worker is not None:
            self.estimate_worker.cancel()
            # le thread s'arrête à la prochaine image : on l'attend pour ne pas le détruire en marche
            self.estimate_worker.wait()
            self.estimate_worker.deleteLater()
            self.estimate_worker = None

    def start_export(self, settings: ExportSettings):
        if settings.path.exists():
            answer = QMessageBox.question(self.window, "Export", f"{settings.path.name} existe déjà. Le remplacer ?")
            if answer != QMessageBox.StandardButton.Yes:
                return

        progress = QProgressDialog("Export en cours…", "Annuler", 0, 100, self.window)
        progress.setWindowTitle("Export")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        worker = ExportWorker(self.project, settings, self.window)
        worker.progress.connect(progress.setValue)
        progress.canceled.connect(worker.cancel)
        worker.succeeded.connect(lambda path: self.export_done(progress, f"Vidéo exportée :\n{path}"))
        worker.failed.connect(lambda error: self.export_done(progress, f"L'export a échoué :\n{error}", True))
        worker.cancelled.connect(lambda: self.export_done(progress, "Export annulé."))
        worker.finished.connect(worker.deleteLater)
        self.export_worker = worker
        worker.start()

    def export_done(self, progress: QProgressDialog, message: str, failed: bool = False):
        progress.close()
        self.export_worker = None
        if failed:
            QMessageBox.warning(self.window, "Export", message)
        else:
            QMessageBox.information(self.window, "Export", message)


def settings_from(dialog: ExportDialog) -> ExportSettings:
    values = dialog.settings()
    values["folder"] = Path(values["folder"]).expanduser()
    return ExportSettings(**values)


def default_folder() -> Path:
    movies = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MoviesLocation)
    return Path(movies or Path.home()) / "Clipso"


def to_qimage(frame) -> QImage | None:
    if frame is None:
        return None
    height, width, _ = frame.shape
    # copy() : sinon la QImage dépend du tableau NumPy, qui peut être supprimé
    return QImage(frame.data, width, height, 3 * width, QImage.Format.Format_RGB888).copy()


def clip_peaks(clip) -> list[float]:
    """Partie de la forme d'onde du média qui correspond au clip."""
    peaks = clip.media.peaks
    if not peaks or not clip.media.duration:
        return peaks
    start = int(clip.in_point / clip.media.duration * len(peaks))
    end = int((clip.in_point + clip.duration) / clip.media.duration * len(peaks))
    return peaks[start : max(end, start + 1)]
