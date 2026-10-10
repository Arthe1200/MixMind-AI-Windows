"""MixMind AI: two-deck DJ-style interface with independent players and crossfader."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings, Qt, QUrl, QUrlQuery
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QTabWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus"}


def format_time(milliseconds: int) -> str:
    seconds = max(0, milliseconds // 1000)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class DeckPanel(QFrame):
    """One independent playback deck. Rate changes alter speed and pitch together."""

    def __init__(self, name: str, accent: str, settings: QSettings, parent=None) -> None:
        super().__init__(parent)
        self.name = name
        self.accent = accent
        self.settings = settings
        self.path: str | None = None
        self.seeking = False
        self.setObjectName("deckPanel")
        self.player = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.player.setAudioOutput(self.output)
        self.output.setVolume(0.8)

        self.deck_title = QLabel(f"PLATINE {name}")
        self.deck_title.setObjectName("deckTitle")
        self.deck_title.setStyleSheet(f"color: {accent};")
        self.track_label = QLabel("Charge un morceau depuis la bibliothèque")
        self.track_label.setObjectName("trackLabel")
        self.track_label.setWordWrap(True)
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("timeLabel")

        self.load_button = QPushButton(f"Charger sur {name}")
        self.play_button = QPushButton("▶ Lecture")
        self.cue_button = QPushButton("⏮ Cue")
        self.stop_button = QPushButton("■ Stop")
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 0)
        self.gain = QSlider(Qt.Orientation.Horizontal)
        self.gain.setRange(0, 100)
        self.gain.setValue(80)
        self.gain_label = QLabel("GAIN 80%")
        self.pitch = QSlider(Qt.Orientation.Horizontal)
        self.pitch.setRange(80, 120)
        self.pitch.setValue(100)
        self.pitch_label = QLabel("PITCH 0%")
        self.bpm = QDoubleSpinBox()
        self.bpm.setRange(40.0, 240.0)
        self.bpm.setDecimals(1)
        self.bpm.setValue(120.0)
        self.bpm.setSuffix(" BPM")
        self.bpm.setToolTip("Saisis le BPM connu du morceau pour la synchronisation manuelle.")

        transport = QHBoxLayout()
        transport.addWidget(self.load_button)
        transport.addWidget(self.play_button)
        transport.addWidget(self.cue_button)
        transport.addWidget(self.stop_button)

        gain_row = QHBoxLayout()
        gain_row.addWidget(self.gain_label)
        gain_row.addWidget(self.gain, 1)

        pitch_row = QHBoxLayout()
        pitch_row.addWidget(self.pitch_label)
        pitch_row.addWidget(self.pitch, 1)

        bpm_row = QHBoxLayout()
        bpm_row.addWidget(QLabel("Tempo saisi"))
        bpm_row.addWidget(self.bpm)
        bpm_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.deck_title)
        layout.addWidget(self.track_label)
        layout.addSpacing(5)
        layout.addLayout(transport)
        layout.addWidget(self.seek)
        layout.addWidget(self.time_label)
        layout.addLayout(gain_row)
        layout.addLayout(pitch_row)
        layout.addLayout(bpm_row)

        self.play_button.clicked.connect(self.toggle_play)
        self.cue_button.clicked.connect(self.cue)
        self.stop_button.clicked.connect(self.player.stop)
        self.seek.sliderPressed.connect(self._begin_seek)
        self.seek.sliderReleased.connect(self._finish_seek)
        self.gain.valueChanged.connect(self._gain_changed)
        self.pitch.valueChanged.connect(self._pitch_changed)
        self.player.positionChanged.connect(self._position_changed)
        self.player.durationChanged.connect(self._duration_changed)
        self.player.playbackStateChanged.connect(self._state_changed)
        self.player.errorOccurred.connect(self._player_error)

    def load_path(self, path: str) -> None:
        candidate = Path(path)
        if not candidate.is_file():
            self.track_label.setText("Fichier introuvable")
            return
        self.path = str(candidate.resolve())
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(self.path))
        self.player.setPlaybackRate(self.pitch.value() / 100)
        self.track_label.setText(candidate.name)
        self.seek.setValue(0)
        self.time_label.setText("00:00 / 00:00")

    def toggle_play(self) -> None:
        if not self.path:
            self.track_label.setText("Charge d'abord un morceau")
        elif self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def cue(self) -> None:
        if self.path:
            self.player.pause()
            self.player.setPosition(0)
            self._position_changed(0)

    def set_crossfade_level(self, level: float) -> None:
        self.output.setVolume(max(0.0, min(1.0, level * self.gain.value() / 100)))

    def _gain_changed(self, value: int) -> None:
        self.gain_label.setText(f"GAIN {value}%")
        self.parent_window().update_crossfade()

    def _pitch_changed(self, value: int) -> None:
        delta = value - 100
        self.pitch_label.setText(f"PITCH {delta:+d}%")
        self.player.setPlaybackRate(value / 100)

    def _begin_seek(self) -> None:
        self.seeking = True

    def _finish_seek(self) -> None:
        self.player.setPosition(self.seek.value())
        self.seeking = False

    def _position_changed(self, position: int) -> None:
        if not self.seeking:
            self.seek.setValue(position)
        self.time_label.setText(
            f"{format_time(position)} / {format_time(self.player.duration())}"
        )

    def _duration_changed(self, duration: int) -> None:
        self.seek.setRange(0, max(0, duration))
        self._position_changed(self.player.position())

    def _state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        self.play_button.setText(
            "⏸ Pause" if state == QMediaPlayer.PlaybackState.PlayingState else "▶ Lecture"
        )

    def _player_error(self, *_args: object) -> None:
        self.track_label.setText(f"Erreur audio : {self.player.errorString()}")

    def parent_window(self) -> "MainWindow":
        parent = self.parent()
        while parent is not None and not isinstance(parent, MainWindow):
            parent = parent.parent()
        return parent


class MainWindow(QMainWindow):
    """Two-deck DJ-style workstation with local files and a real output crossfader."""

    AUDIO_FILTER = (
        "Fichiers audio (*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus);;"
        "Tous les fichiers (*.*)"
    )

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MixMind AI — DJ Workstation")
        self.resize(1440, 900)
        self.setMinimumSize(1050, 720)
        self.settings = QSettings("MixMind AI", "MixMind")
        self.network = QNetworkAccessManager(self)
        self._shuffle = False
        self._repeat = False

        self.deck_a = DeckPanel("A", "#4ed8c2", self.settings, self)
        self.deck_b = DeckPanel("B", "#c5a4ff", self.settings, self)
        self.deck_a.load_button.clicked.connect(lambda: self._load_selected(self.deck_a))
        self.deck_b.load_button.clicked.connect(lambda: self._load_selected(self.deck_b))

        title = QLabel("MIXMIND")
        title.setObjectName("title")
        subtitle = QLabel("DJ WORKSTATION  /  LOCAL AUDIO  /  OPEN SOURCE")
        subtitle.setObjectName("subtitle")
        self.status = QLabel("Prêt. Importe tes fichiers puis charge un morceau sur A et/ou B.")
        self.status.setObjectName("status")

        self.library = QListWidget()
        self.library.setObjectName("trackLibrary")
        self.library.itemDoubleClicked.connect(lambda *_: self._load_selected(self.deck_a))
        self.search = QLineEdit()
        self.search.setPlaceholderText("⌕  Rechercher dans la bibliothèque…")
        self.search.textChanged.connect(self._filter_library)

        import_button = QPushButton("＋ Importer les fichiers")
        import_button.clicked.connect(self._import_tracks)
        folder_button = QPushButton("▤ Scanner un dossier")
        folder_button.clicked.connect(self._scan_folder)
        remove_button = QPushButton("Retirer de la liste")
        remove_button.clicked.connect(self._remove_selected)

        self.crossfader = QSlider(Qt.Orientation.Horizontal)
        self.crossfader.setRange(0, 100)
        self.crossfader.setValue(50)
        self.crossfader.setMinimumWidth(280)
        self.crossfader.valueChanged.connect(self.update_crossfade)
        self.crossfader_label = QLabel("A ◀────────●────────▶ B")
        self.crossfader_label.setObjectName("crossfaderLabel")
        center_button = QPushButton("Centrer")
        center_button.clicked.connect(lambda: self.crossfader.setValue(50))
        sync_button = QPushButton("⇄ Sync BPM")
        sync_button.setToolTip("Ajuste la vitesse de B selon les BPM saisis sur A et B.")
        sync_button.clicked.connect(self._sync_bpm)
        master_label = QLabel("MASTER")
        self.master = QSlider(Qt.Orientation.Horizontal)
        self.master.setRange(0, 100)
        self.master.setValue(85)
        self.master.setMaximumWidth(120)
        self.master.valueChanged.connect(self.update_crossfade)

        mixer = QFrame()
        mixer.setObjectName("mixerPanel")
        mixer_layout = QVBoxLayout(mixer)
        mixer_title = QLabel("MIXER CENTRAL")
        mixer_title.setObjectName("sectionTitle")
        mixer_layout.addWidget(mixer_title, alignment=Qt.AlignmentFlag.AlignHCenter)
        mixer_layout.addWidget(self.crossfader_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        mixer_layout.addWidget(self.crossfader)
        mixer_bottom = QHBoxLayout()
        mixer_bottom.addWidget(center_button)
        mixer_bottom.addWidget(sync_button)
        mixer_bottom.addStretch(1)
        mixer_bottom.addWidget(master_label)
        mixer_bottom.addWidget(self.master)
        mixer_layout.addLayout(mixer_bottom)

        decks_row = QHBoxLayout()
        decks_row.addWidget(self.deck_a, 1)
        decks_row.addWidget(self.deck_b, 1)

        library_panel = QFrame()
        library_panel.setObjectName("libraryPanel")
        library_layout = QVBoxLayout(library_panel)
        self.library_tabs = QTabWidget()
        local_tab = QWidget()
        local_layout = QVBoxLayout(local_tab)
        library_heading = QLabel("MUSIC LIBRARY")
        library_heading.setObjectName("sectionTitle")
        local_layout.addWidget(library_heading)
        local_layout.addWidget(self.search)
        library_actions = QHBoxLayout()
        library_actions.addWidget(import_button)
        library_actions.addWidget(folder_button)
        library_actions.addWidget(remove_button)
        local_layout.addLayout(library_actions)
        local_layout.addWidget(self.library, 1)
        hint = QLabel("Double-clique un titre pour le charger sur A. Les plateformes servent à rechercher le catalogue et ouvrir le titre officiel ; leur flux protégé n'est pas injecté dans les platines.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        local_layout.addWidget(hint)
        self.library_tabs.addTab(local_tab, "Fichiers locaux")

        platforms_tab = QWidget()
        platforms_layout = QVBoxLayout(platforms_tab)
        platform_heading = QLabel("PLATEFORMES MUSICALES")
        platform_heading.setObjectName("sectionTitle")
        platforms_layout.addWidget(platform_heading)
        platform_info = QLabel("Recherche dans les catalogues officiels. Les identifiants API nécessaires se configurent ci-dessous. La lecture DJ reste réservée aux fichiers audio locaux auxquels tu as légalement accès.")
        platform_info.setWordWrap(True)
        platform_info.setObjectName("hint")
        platforms_layout.addWidget(platform_info)
        platform_controls = QHBoxLayout()
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Deezer", "Spotify", "Apple Music", "YouTube Music"])
        self.platform_query = QLineEdit()
        self.platform_query.setPlaceholderText("Titre, artiste ou album…")
        self.platform_query.returnPressed.connect(self._search_platform)
        search_platform_button = QPushButton("Rechercher")
        search_platform_button.clicked.connect(self._search_platform)
        credentials_button = QPushButton("Configurer les API")
        credentials_button.clicked.connect(self._configure_platform_credentials)
        platform_controls.addWidget(self.platform_combo)
        platform_controls.addWidget(self.platform_query, 1)
        platform_controls.addWidget(search_platform_button)
        platform_controls.addWidget(credentials_button)
        platforms_layout.addLayout(platform_controls)
        self.music_results = QListWidget()
        self.music_results.setObjectName("musicResults")
        self.music_results.itemDoubleClicked.connect(self._open_platform_result)
        platforms_layout.addWidget(self.music_results, 1)
        platform_actions = QHBoxLayout()
        open_result_button = QPushButton("Ouvrir le titre sélectionné")
        open_result_button.clicked.connect(self._open_platform_result)
        browser_search_button = QPushButton("Recherche sur le site (sans clé API)")
        browser_search_button.clicked.connect(self._open_platform_search)
        platform_actions.addWidget(open_result_button)
        platform_actions.addWidget(browser_search_button)
        platforms_layout.addLayout(platform_actions)
        self.library_tabs.addTab(platforms_tab, "Plateformes")
        library_layout.addWidget(self.library_tabs)

        content = QVBoxLayout()
        top = QHBoxLayout()
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(subtitle)
        content.addLayout(top)
        content.addLayout(decks_row, 3)
        content.addWidget(mixer)
        content.addWidget(library_panel, 2)
        content.addWidget(self.status)

        root = QWidget()
        root.setLayout(content)
        root.setStyleSheet(
            """
            QWidget { background: #0d0f14; color: #eef0f7; font-size: 12px; }
            QLabel#title { font-size: 28px; font-weight: 900; color: #f3f0ff; letter-spacing: 4px; }
            QLabel#subtitle { color: #777f94; letter-spacing: 1px; }
            QLabel#sectionTitle { color: #9c91c9; font-weight: 800; letter-spacing: 2px; }
            QLabel#status { color: #a4a9b8; padding: 6px; }
            QLabel#trackLabel { font-size: 15px; font-weight: 700; min-height: 40px; }
            QLabel#timeLabel, QLabel#hint { color: #9399aa; }
            QLabel#crossfaderLabel { color: #d7d1ef; font-weight: 700; }
            QFrame#deckPanel, QFrame#mixerPanel, QFrame#libraryPanel {
                background: #151821; border: 1px solid #2a2e3b; border-radius: 12px;
            }
            QFrame#deckPanel { padding: 7px; }
            QLineEdit, QListWidget, QDoubleSpinBox, QComboBox {
                background: #0e1118; border: 1px solid #303546; border-radius: 7px; padding: 8px;
            }
            QTabWidget::pane { border: 1px solid #2a2e3b; border-radius: 8px; }
            QTabBar::tab { background: #171b25; padding: 8px 14px; margin-right: 4px; border-radius: 6px; }
            QTabBar::tab:selected { background: #39314f; }
            QListWidget::item { padding: 8px; border-radius: 5px; }
            QListWidget::item:selected { background: #39314f; color: #fff; }
            QPushButton {
                background: #242938; border: 1px solid #3a4052; border-radius: 7px;
                padding: 8px 10px; font-weight: 600;
            }
            QPushButton:hover { background: #343047; border-color: #716493; }
            QSlider::groove:horizontal { height: 5px; background: #34394a; border-radius: 2px; }
            QSlider::handle:horizontal {
                background: #c5a4ff; width: 14px; margin: -5px 0; border-radius: 7px;
            }
            """
        )
        self.setCentralWidget(root)
        self._install_shortcuts()
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self.update_crossfade()

    def _configure_platform_credentials(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuration des plateformes musicales")
        dialog.resize(560, 320)
        layout = QVBoxLayout(dialog)
        note = QLabel("Les clés sont enregistrées dans les paramètres locaux de ton compte Windows (elles ne sont pas envoyées sur GitHub, mais cette configuration n'est pas un coffre chiffré). Ne partage jamais ces valeurs. Deezer utilise ici sa recherche publique.")
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        spotify_id = QLineEdit(str(self.settings.value("music/spotify_client_id", "")))
        spotify_secret = QLineEdit(str(self.settings.value("music/spotify_client_secret", "")))
        spotify_secret.setEchoMode(QLineEdit.EchoMode.Password)
        apple_token = QLineEdit(str(self.settings.value("music/apple_developer_token", "")))
        apple_token.setEchoMode(QLineEdit.EchoMode.Password)
        youtube_key = QLineEdit(str(self.settings.value("music/youtube_api_key", "")))
        youtube_key.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Spotify — Client ID", spotify_id)
        form.addRow("Spotify — Client Secret", spotify_secret)
        form.addRow("Apple Music — Developer Token", apple_token)
        form.addRow("YouTube Data API — API Key", youtube_key)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings.setValue("music/spotify_client_id", spotify_id.text().strip())
            self.settings.setValue("music/spotify_client_secret", spotify_secret.text().strip())
            self.settings.setValue("music/apple_developer_token", apple_token.text().strip())
            self.settings.setValue("music/youtube_api_key", youtube_key.text().strip())
            self.status.setText("Configuration des plateformes enregistrée localement.")

    @staticmethod
    def _url_with_query(base_url: str, params: dict[str, str]) -> QUrl:
        url = QUrl(base_url)
        query = QUrlQuery()
        for key, value in params.items():
            query.addQueryItem(key, value)
        url.setQuery(query)
        return url

    def _request_json(self, url: QUrl, callback, headers: dict[str, str] | None = None,
                      body: bytes | None = None) -> None:
        request = QNetworkRequest(url)
        request.setRawHeader(QByteArray(b"Accept"), QByteArray(b"application/json"))
        for key, value in (headers or {}).items():
            request.setRawHeader(QByteArray(key.encode()), QByteArray(value.encode()))
        if body is None:
            reply = self.network.get(request)
        else:
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader,
                              "application/x-www-form-urlencoded")
            reply = self.network.post(request, QByteArray(body))
        reply.finished.connect(lambda r=reply, cb=callback: self._finish_json_request(r, cb))

    def _finish_json_request(self, reply, callback) -> None:
        error = reply.error()
        raw = bytes(reply.readAll())
        error_text = reply.errorString()
        reply.deleteLater()
        if error:
            self.status.setText(f"Erreur de connexion à la plateforme : {error_text}")
            return
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.status.setText("La plateforme a renvoyé une réponse illisible.")
            return
        callback(payload)

    def _search_platform(self) -> None:
        query = self.platform_query.text().strip()
        if not query:
            self.status.setText("Saisis un titre ou un artiste à rechercher.")
            return
        platform = self.platform_combo.currentText()
        self.music_results.clear()
        self.status.setText(f"Recherche dans le catalogue {platform}…")
        if platform == "Deezer":
            url = self._url_with_query("https://api.deezer.com/search", {"q": query, "limit": "25"})
            self._request_json(url, lambda data: self._show_platform_results("Deezer", data))
        elif platform == "Spotify":
            client_id = str(self.settings.value("music/spotify_client_id", "")).strip()
            secret = str(self.settings.value("music/spotify_client_secret", "")).strip()
            if not client_id or not secret:
                self.status.setText("Configure le Client ID et le Client Secret Spotify dans « Configurer les API ».")
                return
            credentials = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
            self._request_json(QUrl("https://accounts.spotify.com/api/token"),
                lambda data: self._spotify_token_received(data, query),
                {"Authorization": f"Basic {credentials}"}, b"grant_type=client_credentials")
        elif platform == "Apple Music":
            token = str(self.settings.value("music/apple_developer_token", "")).strip()
            if not token:
                self.status.setText("Ajoute un Apple Music Developer Token dans « Configurer les API ».")
                return
            url = self._url_with_query("https://api.music.apple.com/v1/catalog/fr/search",
                                       {"term": query, "types": "songs", "limit": "25"})
            self._request_json(url, lambda data: self._show_platform_results("Apple Music", data),
                               {"Authorization": f"Bearer {token}"})
        else:
            key = str(self.settings.value("music/youtube_api_key", "")).strip()
            if not key:
                self.status.setText("Ajoute une clé YouTube Data API dans « Configurer les API ».")
                return
            url = self._url_with_query("https://www.googleapis.com/youtube/v3/search",
                {"part": "snippet", "type": "video", "videoCategoryId": "10",
                 "maxResults": "25", "q": query, "key": key})
            self._request_json(url, lambda data: self._show_platform_results("YouTube Music", data))

    def _spotify_token_received(self, payload: dict, query: str) -> None:
        token = payload.get("access_token")
        if not token:
            self.status.setText("Spotify n'a pas fourni de jeton. Vérifie les identifiants API.")
            return
        url = self._url_with_query("https://api.spotify.com/v1/search",
                                   {"q": query, "type": "track", "limit": "25"})
        self._request_json(url, lambda data: self._show_platform_results("Spotify", data),
                           {"Authorization": f"Bearer {token}"})

    def _show_platform_results(self, platform: str, payload: dict) -> None:
        if payload.get("error"):
            error = payload["error"]
            if isinstance(error, dict):
                error = error.get("message", str(error))
            self.status.setText(f"{platform} : {error}")
            return
        if platform == "Deezer":
            records = payload.get("data", [])
            parsed = [(f'{item.get("title", "Titre inconnu")} — {item.get("artist", {}).get("name", "Artiste inconnu")}', item.get("link", "")) for item in records]
        elif platform == "Spotify":
            records = payload.get("tracks", {}).get("items", [])
            parsed = [(f'{item.get("name", "Titre inconnu")} — {", ".join(a.get("name", "") for a in item.get("artists", []))}', item.get("external_urls", {}).get("spotify", "")) for item in records]
        elif platform == "Apple Music":
            records = payload.get("results", {}).get("songs", {}).get("data", [])
            parsed = [(f'{item.get("attributes", {}).get("name", "Titre inconnu")} — {item.get("attributes", {}).get("artistName", "Artiste inconnu")}', item.get("attributes", {}).get("url", "")) for item in records]
        else:
            records = payload.get("items", [])
            parsed = [(f'{item.get("snippet", {}).get("title", "Titre inconnu")} — {item.get("snippet", {}).get("channelTitle", "Chaîne inconnue")}', f'https://music.youtube.com/watch?v={item.get("id", {}).get("videoId", "")}') for item in records]
        count = 0
        for title, url in parsed:
            if not url:
                continue
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, url)
            self.music_results.addItem(item)
            count += 1
        self.status.setText(f"{count} résultat(s) trouvé(s) sur {platform}. Double-clique un résultat pour l'ouvrir." if count else f"Aucun résultat exploitable trouvé sur {platform}.")

    def _open_platform_search(self) -> None:
        query = self.platform_query.text().strip()
        if not query:
            self.status.setText("Saisis un titre ou un artiste à rechercher.")
            return
        platform = self.platform_combo.currentText()
        if platform == "Deezer":
            url = self._url_with_query("https://www.deezer.com/search", {"q": query})
        elif platform == "Spotify":
            url = QUrl("https://open.spotify.com/search/" + QUrl.toPercentEncoding(query).data().decode())
        elif platform == "Apple Music":
            url = self._url_with_query("https://music.apple.com/fr/search", {"term": query})
        else:
            url = self._url_with_query("https://music.youtube.com/search", {"q": query})
        QDesktopServices.openUrl(url)
        self.status.setText(f"Recherche {platform} ouverte dans le navigateur.")

    def _open_platform_result(self, *_args: object) -> None:
        item = self.music_results.currentItem()
        if not item:
            self.status.setText("Sélectionne d'abord un résultat de plateforme.")
            return
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _install_shortcuts(self) -> None:
        for sequence, callback in (
            ("Ctrl+O", self._import_tracks),
            ("Ctrl+F", self.search.setFocus),
            ("Space", self._toggle_active_deck),
            ("Ctrl+1", lambda: self._load_selected(self.deck_a)),
            ("Ctrl+2", lambda: self._load_selected(self.deck_b)),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(callback)

    def closeEvent(self, event) -> None:
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)

    def _toggle_active_deck(self) -> None:
        playing = (
            self.deck_a.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        )
        if playing:
            self.deck_a.toggle_play()
        else:
            self.deck_b.toggle_play()

    def _import_tracks(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Importer des fichiers audio", str(Path.home()), self.AUDIO_FILTER
        )
        self._add_tracks(files)

    def _scan_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Scanner un dossier musical", str(Path.home()))
        if not folder:
            return
        root = Path(folder)
        try:
            files = sorted(
                (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS),
                key=lambda p: str(p).casefold(),
            )
        except OSError as exc:
            self.status.setText(f"Impossible de scanner ce dossier : {exc}")
            return
        self._add_tracks([str(p) for p in files])
        self.status.setText(f"Scan terminé : {len(files)} fichier(s) audio trouvé(s).")

    def _add_tracks(self, filenames: list[str]) -> None:
        existing = {
            self.library.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.library.count())
        }
        added = 0
        for filename in filenames:
            path = str(Path(filename).resolve())
            if path in existing:
                continue
            item = QListWidgetItem(Path(path).name)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.library.addItem(item)
            existing.add(path)
            added += 1
        self.status.setText(f"{added} nouveau(x) morceau(x) ajouté(s) à la bibliothèque.")

    def _filter_library(self, query: str) -> None:
        query = query.casefold().strip()
        for index in range(self.library.count()):
            item = self.library.item(index)
            item.setHidden(query not in item.text().casefold())
        visible = sum(not self.library.item(i).isHidden() for i in range(self.library.count()))
        self.status.setText(f"{visible} morceau(x) affiché(s).")

    def _selected_path(self) -> str | None:
        item = self.library.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _load_selected(self, deck: DeckPanel) -> None:
        path = self._selected_path()
        if not path:
            QMessageBox.information(self, "Bibliothèque", "Sélectionne d'abord un morceau.")
            return
        deck.load_path(path)
        self.status.setText(f"{Path(path).name} chargé sur la platine {deck.name}.")

    def _remove_selected(self) -> None:
        row = self.library.currentRow()
        if row < 0:
            self.status.setText("Sélectionne un morceau à retirer de la liste.")
            return
        path = self.library.item(row).data(Qt.ItemDataRole.UserRole)
        for deck in (self.deck_a, self.deck_b):
            if deck.path == path:
                deck.player.stop()
                deck.player.setSource(QUrl())
                deck.path = None
                deck.track_label.setText("Morceau retiré de la bibliothèque")
        self.library.takeItem(row)
        self.status.setText("Entrée retirée. Le fichier original n'a pas été supprimé.")

    def update_crossfade(self, *_args: object) -> None:
        position = self.crossfader.value() / 100
        master = self.master.value() / 100
        # Equal-power crossfade: both decks retain a smooth perceived level near centre.
        import math

        self.deck_a.set_crossfade_level(math.cos(position * math.pi / 2) * master)
        self.deck_b.set_crossfade_level(math.sin(position * math.pi / 2) * master)
        if position < 0.45:
            self.crossfader_label.setText("A  ◀━━━━●────────▶  B")
        elif position > 0.55:
            self.crossfader_label.setText("A  ◀────────●━━━━▶  B")
        else:
            self.crossfader_label.setText("A  ◀━━━━━━●━━━━━━▶  B")

    def _sync_bpm(self) -> None:
        bpm_a = self.deck_a.bpm.value()
        bpm_b = self.deck_b.bpm.value()
        if not self.deck_a.path or not self.deck_b.path:
            self.status.setText("Charge un morceau sur A et un sur B avant la synchronisation.")
            return
        # Preserve A's pitch setting while adjusting B to the manually entered BPM ratio.
        rate = (bpm_a / bpm_b) * (self.deck_b.pitch.value() / 100)
        rate = max(0.5, min(2.0, rate))
        self.deck_b.player.setPlaybackRate(rate)
        self.deck_b.pitch.blockSignals(True)
        self.deck_b.pitch.setValue(max(80, min(120, round(rate * 100))))
        self.deck_b.pitch.blockSignals(False)
        self.deck_b.pitch_label.setText(f"PITCH {self.deck_b.pitch.value() - 100:+d}%")
        self.status.setText(
            f"Sync manuelle appliquée : B réglée depuis {bpm_a:.1f} → {bpm_b:.1f} BPM saisis. "
            "La vitesse et la hauteur changent ensemble ; vérifie le résultat à l'écoute."
        )
