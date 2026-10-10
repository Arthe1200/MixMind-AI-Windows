"""Initial desktop window with local import and single-track preview."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidget, QMainWindow, QMessageBox,
    QPushButton, QSlider, QVBoxLayout, QWidget,
)


class MainWindow(QMainWindow):
    """Main window. Multi-deck mixing is planned for a later milestone."""

    AUDIO_FILTER = (
        "Fichiers audio (*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus);;"
        "Tous les fichiers (*.*)"
    )

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MixMind AI — Studio DJ")
        self.resize(1180, 760)
        self.setMinimumSize(850, 560)

        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.75)

        self.library = QListWidget()
        self.library.setObjectName("trackLibrary")
        self.library.itemDoubleClicked.connect(self._preview_selected)

        title = QLabel("MixMind AI")
        title.setObjectName("title")
        subtitle = QLabel(
            "Studio DJ local · Assistant IA facultatif · Première version de développement"
        )
        subtitle.setObjectName("subtitle")
        self.status = QLabel("Prêt — importe des fichiers audio pour commencer.")
        self.status.setObjectName("status")

        import_button = QPushButton("＋  Importer des morceaux")
        import_button.clicked.connect(self._import_tracks)
        self.play_button = QPushButton("▶  Écouter la sélection")
        self.play_button.clicked.connect(self._preview_selected)
        stop_button = QPushButton("■  Arrêter")
        stop_button.clicked.connect(self._player.stop)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(75)
        self.volume.valueChanged.connect(
            lambda value: self._audio_output.setVolume(value / 100)
        )
        self.now_playing = QLabel("Aucun morceau en lecture")
        self.now_playing.setObjectName("nowPlaying")

        header = QVBoxLayout()
        header.addWidget(title)
        header.addWidget(subtitle)
        controls = QHBoxLayout()
        controls.addWidget(import_button)
        controls.addWidget(self.play_button)
        controls.addWidget(stop_button)
        controls.addWidget(QLabel("Volume"))
        controls.addWidget(self.volume, 1)

        content = QVBoxLayout()
        content.addLayout(header)
        content.addSpacing(18)
        content.addLayout(controls)
        content.addSpacing(20)
        section = QLabel("BIBLIOTHÈQUE MUSICALE")
        section.setObjectName("sectionTitle")
        content.addWidget(section)
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
            QListWidget { background: #191b23; border: 1px solid #303342;
                          border-radius: 8px; padding: 8px; }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background: #37304f; border-radius: 4px; }
            QPushButton { background: #29243b; border: 1px solid #51466f;
                          border-radius: 7px; padding: 10px 12px; }
            QPushButton:hover { background: #393052; }
            QSlider::groove:horizontal { height: 5px; background: #343644; }
            QSlider::handle:horizontal { background: #c5b6ff; width: 13px;
                                         margin: -5px 0; border-radius: 6px; }
            """
        )
        self.setCentralWidget(root)
        self._player.errorOccurred.connect(self._on_player_error)

    def _import_tracks(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Importer des fichiers audio", str(Path.home()), self.AUDIO_FILTER
        )
        existing = {
            self.library.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.library.count())
        }
        added = 0
        for filename in files:
            path = str(Path(filename).resolve())
            if path not in existing:
                self.library.addItem(Path(path).name)
                self.library.item(self.library.count() - 1).setData(
                    Qt.ItemDataRole.UserRole, path
                )
                existing.add(path)
                added += 1
        self.status.setText(f"{added} morceau(x) ajouté(s) à la bibliothèque de cette session.")

    def _preview_selected(self, *_args: object) -> None:
        item = self.library.currentItem()
        if item is None:
            QMessageBox.information(
                self, "Aucun morceau sélectionné", "Importe puis sélectionne un fichier audio."
            )
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path or not Path(path).is_file():
            self.status.setText("Le fichier sélectionné est introuvable.")
            return
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        self.now_playing.setText(f"Lecture : {Path(path).name}")
        self.status.setText(
            "Préécoute simple active. Le mixage multi-platines sera développé ensuite."
        )

    def _on_player_error(self, *_args: object) -> None:
        self.status.setText(f"Erreur de lecture : {self._player.errorString()}")
