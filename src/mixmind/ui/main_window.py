"""MixMind AI desktop UI: local library, preview player and DJ-friendly controls."""

from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QUrl
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """Single-deck preview player; full multi-deck mixing remains a future milestone."""

    AUDIO_FILTER = (
        "Fichiers audio (*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus);;"
        "Tous les fichiers (*.*)"
    )

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MixMind AI — Studio DJ")
        self.resize(1180, 760)
        self.setMinimumSize(850, 560)
        self.settings = QSettings("MixMind AI", "MixMind")

        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(float(self.settings.value("volume", 0.75)))
        self._shuffle = False
        self._repeat = False
        self._seeking = False

        self.library = QListWidget()
        self.library.setObjectName("trackLibrary")
        self.library.itemDoubleClicked.connect(self._preview_selected)

        title = QLabel("MixMind AI")
        title.setObjectName("title")
        subtitle = QLabel("Ton studio DJ local · Gratuit · Open source")
        subtitle.setObjectName("subtitle")
        self.status = QLabel("Prêt — importe tes morceaux pour commencer.")
        self.status.setObjectName("status")

        import_button = QPushButton("＋ Importer")
        import_button.clicked.connect(self._import_tracks)
        folder_button = QPushButton("📁 Scanner un dossier")
        folder_button.clicked.connect(self._scan_folder)
        self.play_button = QPushButton("▶ Lire")
        self.play_button.clicked.connect(self._toggle_play)
        self.stop_button = QPushButton("■ Stop")
        self.stop_button.clicked.connect(self._player.stop)
        self.previous_button = QPushButton("⏮ Précédent")
        self.previous_button.clicked.connect(lambda: self._step_track(-1))
        self.next_button = QPushButton("Suivant ⏭")
        self.next_button.clicked.connect(lambda: self._step_track(1))
        self.shuffle_button = QPushButton("🔀 Aléatoire : OFF")
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.toggled.connect(self._set_shuffle)
        self.repeat_button = QPushButton("🔁 Répéter : OFF")
        self.repeat_button.setCheckable(True)
        self.repeat_button.toggled.connect(self._set_repeat)
        self.remove_button = QPushButton("✕ Retirer")
        self.remove_button.clicked.connect(self._remove_selected)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un morceau par son nom…")
        self.search.textChanged.connect(self._filter_library)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(round(self._audio_output.volume() * 100))
        self.volume.setToolTip("Volume de préécoute")
        self.volume.valueChanged.connect(self._set_volume)

        self.now_playing = QLabel("Aucun morceau en lecture")
        self.now_playing.setObjectName("nowPlaying")
        self.time_label = QLabel("00:00 / 00:00")
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 0)
        self.seek.setToolTip("Cliquer ou faire glisser pour se déplacer dans le morceau")
        self.seek.sliderPressed.connect(self._begin_seek)
        self.seek.sliderReleased.connect(self._finish_seek)

        header = QVBoxLayout()
        header.addWidget(title)
        header.addWidget(subtitle)

        transport = QHBoxLayout()
        for widget in (
            self.previous_button, self.play_button, self.stop_button, self.next_button,
            self.shuffle_button, self.repeat_button,
        ):
            transport.addWidget(widget)

        file_controls = QHBoxLayout()
        file_controls.addWidget(import_button)
        file_controls.addWidget(folder_button)
        file_controls.addWidget(self.remove_button)
        file_controls.addStretch(1)
        file_controls.addWidget(QLabel("Volume"))
        file_controls.addWidget(self.volume)

        seek_row = QHBoxLayout()
        seek_row.addWidget(self.seek, 1)
        seek_row.addWidget(self.time_label)

        content = QVBoxLayout()
        content.addLayout(header)
        content.addSpacing(12)
        content.addLayout(transport)
        content.addLayout(seek_row)
        content.addLayout(file_controls)
        content.addSpacing(14)
        section = QLabel("BIBLIOTHÈQUE MUSICALE")
        section.setObjectName("sectionTitle")
        content.addWidget(section)
        content.addWidget(self.search)
        content.addWidget(self.library, 1)
        content.addWidget(self.now_playing)
        content.addWidget(self.status)

        root = QWidget()
        root.setLayout(content)
        root.setStyleSheet(
            """
            QWidget { background: #101116; color: #f2f3f7; font-size: 13px; }
            QLabel#title { font-size: 30px; font-weight: 700; color: #c5b6ff; }
            QLabel#subtitle { color: #a4a6b5; }
            QLabel#sectionTitle { color: #aaa3d8; font-weight: 700; letter-spacing: 1px; }
            QLabel#status { color: #9295a6; padding-top: 4px; }
            QLabel#nowPlaying { color: #e0d9ff; padding: 10px 0; }
            QLineEdit, QListWidget { background: #191b23; border: 1px solid #303342;
                                     border-radius: 8px; padding: 8px; }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background: #37304f; border-radius: 4px; }
            QPushButton { background: #29243b; border: 1px solid #51466f;
                          border-radius: 7px; padding: 9px 10px; }
            QPushButton:hover { background: #393052; }
            QPushButton:checked { background: #514477; border-color: #c5b6ff; }
            QSlider::groove:horizontal { height: 5px; background: #343644; }
            QSlider::handle:horizontal { background: #c5b6ff; width: 13px;
                                         margin: -5px 0; border-radius: 6px; }
            """
        )
        self.setCentralWidget(root)

        self._player.errorOccurred.connect(self._on_player_error)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._restore_geometry()
        self._install_shortcuts()

    def _install_shortcuts(self) -> None:
        for sequence, callback in (
            ("Space", self._toggle_play),
            ("Ctrl+O", self._import_tracks),
            ("Ctrl+F", self.search.setFocus),
            ("Delete", self._remove_selected),
            ("Alt+Right", lambda: self._step_track(1)),
            ("Alt+Left", lambda: self._step_track(-1)),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(callback)

    def _restore_geometry(self) -> None:
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API naming
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("volume", self._audio_output.volume())
        super().closeEvent(event)

    def _set_volume(self, value: int) -> None:
        self._audio_output.setVolume(value / 100)
        self.settings.setValue("volume", value / 100)

    def _import_tracks(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Importer des fichiers audio", str(Path.home()), self.AUDIO_FILTER
        )
        self._add_tracks(files)

    def _scan_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier musical", str(Path.home())
        )
        if not folder:
            return
        root = Path(folder)
        files = sorted(
            (path for path in root.rglob("*") if path.is_file()
             and path.suffix.lower() in {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus"}),
            key=lambda path: str(path).casefold(),
        )
        self._add_tracks([str(path) for path in files])
        self.status.setText(f"Scan terminé : {len(files)} fichier(s) audio trouvé(s).")

    def _add_tracks(self, filenames: list[str]) -> None:
        existing = {
            self.library.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.library.count())
        }
        added = 0
        for filename in filenames:
            path = str(Path(filename).resolve())
            if path not in existing:
                from PySide6.QtWidgets import QListWidgetItem

                item = QListWidgetItem(Path(path).name)
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.library.addItem(item)
                existing.add(path)
                added += 1
        self.status.setText(f"{added} nouveau(x) morceau(x) ajouté(s).")

    def _visible_rows(self) -> list[int]:
        return [i for i in range(self.library.count()) if not self.library.item(i).isHidden()]

    def _filter_library(self, query: str) -> None:
        query = query.casefold().strip()
        for index in range(self.library.count()):
            item = self.library.item(index)
            item.setHidden(query not in item.text().casefold())
        self.status.setText(f"{len(self._visible_rows())} morceau(x) affiché(s).")

    def _selected_path(self) -> str | None:
        item = self.library.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _preview_selected(self, *_args: object) -> None:
        path = self._selected_path()
        if not path:
            QMessageBox.information(self, "Aucun morceau", "Sélectionne d'abord un fichier audio.")
            return
        if not Path(path).is_file():
            self.status.setText("Le fichier sélectionné est introuvable.")
            return
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        self.now_playing.setText(f"Lecture : {Path(path).name}")
        self.status.setText("Préécoute active — le mixage multi-platines arrivera dans une prochaine version.")

    def _toggle_play(self) -> None:
        if self._player.source().isEmpty():
            self._preview_selected()
        elif self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _step_track(self, direction: int) -> None:
        rows = self._visible_rows()
        if not rows:
            self.status.setText("La bibliothèque ne contient aucun morceau visible.")
            return
        current = self.library.currentRow()
        if self._shuffle and len(rows) > 1:
            candidates = [row for row in rows if row != current]
            target = random.choice(candidates)
        elif current in rows:
            target = rows[(rows.index(current) + direction) % len(rows)]
        else:
            target = rows[0]
        self.library.setCurrentRow(target)
        self._preview_selected()

    def _set_shuffle(self, enabled: bool) -> None:
        self._shuffle = enabled
        self.shuffle_button.setText(f"🔀 Aléatoire : {'ON' if enabled else 'OFF'}")
        self.status.setText("Lecture aléatoire activée." if enabled else "Lecture dans l'ordre de la bibliothèque.")

    def _set_repeat(self, enabled: bool) -> None:
        self._repeat = enabled
        self.repeat_button.setText(f"🔁 Répéter : {'ON' if enabled else 'OFF'}")

    def _remove_selected(self) -> None:
        row = self.library.currentRow()
        if row < 0:
            self.status.setText("Sélectionne un morceau à retirer.")
            return
        path = self.library.item(row).data(Qt.ItemDataRole.UserRole)
        if path and self._player.source().toLocalFile() == path:
            self._player.stop()
            self._player.setSource(QUrl())
            self.now_playing.setText("Aucun morceau en lecture")
        self.library.takeItem(row)
        self.status.setText("Morceau retiré de la liste (le fichier original n'a pas été supprimé).")

    def _begin_seek(self) -> None:
        self._seeking = True

    def _finish_seek(self) -> None:
        self._player.setPosition(self.seek.value())
        self._seeking = False

    def _on_position_changed(self, position: int) -> None:
        if not self._seeking:
            self.seek.setValue(position)
        self._update_time_label(position, self._player.duration())

    def _on_duration_changed(self, duration: int) -> None:
        self.seek.setRange(0, max(0, duration))
        self._update_time_label(self._player.position(), duration)

    def _update_time_label(self, position: int, duration: int) -> None:
        def stamp(ms: int) -> str:
            seconds = max(0, ms // 1000)
            return f"{seconds // 60:02d}:{seconds % 60:02d}"
        self.time_label.setText(f"{stamp(position)} / {stamp(duration)}")

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        self.play_button.setText(
            "⏸ Pause" if state == QMediaPlayer.PlaybackState.PlayingState else "▶ Lire"
        )

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self._repeat:
                self._player.setPosition(0)
                self._player.play()
            else:
                self._step_track(1)

    def _on_player_error(self, *_args: object) -> None:
        self.status.setText(f"Erreur de lecture : {self._player.errorString()}")
