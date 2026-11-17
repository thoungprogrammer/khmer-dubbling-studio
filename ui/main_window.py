"""
Main Window - Khmer Dubbing Studio — modern responsive UI
"""
import os
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QSplitter, QTabWidget, QTextEdit, QMessageBox,
    QStatusBar, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QTimer
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent, QPainter, QColor, QLinearGradient

from ui.subtitle_editor import SubtitleEditorWidget
from ui.voice_panel import VoicePanelWidget
from ui.worker import DubbingWorker
from ui.styles import DARK_THEME, C_ACCENT, C_ACCENT2, C_BG, C_SURFACE, C_BORDER, C_TEXT, C_TEXT_DIM, UI_FONT
from core.pipeline import PipelineConfig
from config import APP_NAME, APP_VERSION, OUTPUT_DIR


# ── Animated gradient header ──────────────────────────────────────────────────

class GradientHeader(QWidget):
    """Painted header bar with a subtle left-to-right gradient."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(72)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0,  QColor("#0d1117"))
        grad.setColorAt(0.35, QColor("#1c2333"))
        grad.setColorAt(0.65, QColor("#1c2333"))
        grad.setColorAt(1.0,  QColor("#0d1117"))
        painter.fillRect(self.rect(), grad)
        # bottom border line
        painter.setPen(QColor(C_BORDER))
        painter.drawLine(0, self.height()-1, self.width(), self.height()-1)


# ── Drop zone widget ──────────────────────────────────────────────────────────

class DropZone(QLabel):
    """Styled drag-and-drop zone."""

    IDLE_STYLE = """
        QLabel {
            border: 2px dashed #30363d;
            border-radius: 12px;
            color: #7d8590;
            font-size: 13px;
            background: #161b22;
            padding: 12px;
        }
        QLabel:hover {
            border-color: #58a6ff;
            color: #58a6ff;
            background: #1c2333;
        }
    """
    LOADED_STYLE = """
        QLabel {
            border: 2px solid #3fb950;
            border-radius: 12px;
            color: #3fb950;
            font-size: 13px;
            background: rgba(63,185,80,0.07);
            padding: 12px;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Drop video here\nor click to browse\n\nMP4  MKV  MOV  AVI  WEBM")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(120)
        self.setStyleSheet(self.IDLE_STYLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_loaded(self, name: str):
        self.setText(f"{name}")
        self.setStyleSheet(self.LOADED_STYLE)

    def reset(self):
        self.setText("Drop video here\nor click to browse\n\nMP4  MKV  MOV  AVI  WEBM")
        self.setStyleSheet(self.IDLE_STYLE)


# ── Step badge ────────────────────────────────────────────────────────────────

class StepBadge(QWidget):
    """Small numbered step indicator used in the progress area."""

    def __init__(self, number: int, label: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        self.badge = QLabel(str(number))
        self.badge.setFixedSize(24, 24)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setStyleSheet(f"""
            QLabel {{
                background: #21262d;
                color: #7d8590;
                border-radius: 12px;
                font-weight: bold;
                font-size: 11px;
                font-family: '{UI_FONT}';
            }}
        """)

        self.lbl = QLabel(label)
        self.lbl.setStyleSheet(f"color: #7d8590; font-size: 12px; font-family: '{UI_FONT}';")

        layout.addWidget(self.badge)
        layout.addWidget(self.lbl)
        layout.addStretch()

    def set_active(self, active: bool):
        if active:
            self.badge.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 {C_ACCENT2}, stop:1 {C_ACCENT});
                    color: white;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 11px;
                    font-family: '{UI_FONT}';
                }}
            """)
            self.lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 12px; font-family: '{UI_FONT}'; font-weight: bold;")
        else:
            self.badge.setStyleSheet(f"""
                QLabel {{
                    background: #21262d;
                    color: #7d8590;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 11px;
                    font-family: '{UI_FONT}';
                }}
            """)
            self.lbl.setStyleSheet(f"color: #7d8590; font-size: 12px; font-family: '{UI_FONT}';")


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    STEPS = [
        "Extract audio",
        "Transcribe speech",
        "Translate to Khmer",
        "Generate Khmer voice",
        "Sync & mix audio",
        "Export video",
    ]

    STEP_KEYWORDS = [
        "extracting",
        "transcrib",
        "translat",
        "generat",
        "sync",
        "export",
    ]

    def __init__(self):
        super().__init__()
        self.video_path = None
        self.worker = None
        self.output_paths = {}
        self._dot_count = 0

        self._setup_window()
        self._setup_ui()
        self._setup_status_bar()
        self.setAcceptDrops(True)

        # Animate the "processing" dots in the status label
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._tick_dots)

    # ── Window ────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.setMinimumSize(1050, 650)
        self.resize(1300, 820)
        self.setStyleSheet(DARK_THEME)

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — drag a video file to get started")

    # ── Layout ────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self._build_header())

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([360, 940])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        content_layout.addWidget(splitter)
        vbox.addWidget(content, stretch=1)
        vbox.addWidget(self._build_bottom_bar())

    # ── Header ────────────────────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        header = GradientHeader()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # App icon placeholder + title
        icon_lbl = QLabel("▶")
        icon_lbl.setFixedSize(38, 38)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {C_ACCENT2}, stop:1 {C_ACCENT});
                border-radius: 10px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }}
        """)

        title_lbl = QLabel(APP_NAME)
        title_lbl.setObjectName("appTitle")

        subtitle_lbl = QLabel("Multi-language  →  Khmer  Dubbing Studio")
        subtitle_lbl.setObjectName("appSubtitle")

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_col.addWidget(title_lbl)
        title_col.addWidget(subtitle_lbl)

        layout.addWidget(icon_lbl)
        layout.addSpacing(12)
        layout.addLayout(title_col)
        layout.addStretch()

        self.video_info_label = QLabel("")
        self.video_info_label.setObjectName("videoInfoLabel")
        self.video_info_label.setVisible(False)
        layout.addWidget(self.video_info_label)

        return header

    # ── Left panel ────────────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(360)
        panel.setStyleSheet(f"background: {C_SURFACE}; border-right: 1px solid {C_BORDER};")

        scroll = QScrollArea()
        scroll.setWidget(panel)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setFixedWidth(360)

        outer = QWidget()
        outer.setFixedWidth(360)
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(scroll)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(14, 14, 14, 14)
        inner_layout.setSpacing(12)

        # ── Video input ──────────────────────────────────────────
        vid_lbl = QLabel("VIDEO INPUT")
        vid_lbl.setObjectName("sectionTitle")
        inner_layout.addWidget(vid_lbl)

        self.drop_zone = DropZone()
        self.drop_zone.mousePressEvent = lambda e: self._browse_video()
        inner_layout.addWidget(self.drop_zone)

        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("statusLabel")
        self.file_label.setWordWrap(True)
        inner_layout.addWidget(self.file_label)

        # Divider
        inner_layout.addWidget(self._divider())

        # ── Settings (voice panel) ───────────────────────────────
        self.voice_panel = VoicePanelWidget()
        inner_layout.addWidget(self.voice_panel)

        inner_layout.addStretch()
        scroll.setWidget(inner)

        return outer

    # ── Right panel ───────────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Subtitle editor
        self.subtitle_editor = SubtitleEditorWidget()
        self.tabs.addTab(self.subtitle_editor, "  Subtitle Editor  ")

        # Processing log
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setPlaceholderText("Processing log will appear here...")
        self.log_widget.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 12px;"
            f"background: {C_BG}; border: none; padding: 10px;"
        )
        self.tabs.addTab(self.log_widget, "  Processing Log  ")

        layout.addWidget(self.tabs)
        return widget

    # ── Bottom bar ────────────────────────────────────────────────────────

    def _build_bottom_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("card")
        bar.setStyleSheet(f"""
            QFrame#card {{
                background: {C_SURFACE};
                border-top: 1px solid {C_BORDER};
                border-radius: 0;
            }}
        """)
        bar.setFixedHeight(90)

        layout = QVBoxLayout(bar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(6)

        # ── Progress row ─────────────────────────────────────────
        progress_row = QHBoxLayout()
        progress_row.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        progress_row.addWidget(self.progress_bar, stretch=1)

        # Step badges
        self.step_badges = []
        for i, step in enumerate(self.STEPS):
            badge = StepBadge(i + 1, step)
            self.step_badges.append(badge)

        self.progress_label = QLabel("Select a video and click Start Dubbing")
        self.progress_label.setObjectName("progressLabel")
        progress_row.addWidget(self.progress_label, stretch=1)

        layout.addLayout(progress_row)

        # ── Button row ───────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.open_output_btn = QPushButton("  Open Output Folder")
        self.open_output_btn.setObjectName("successButton")
        self.open_output_btn.setVisible(False)
        self.open_output_btn.setFixedHeight(40)
        self.open_output_btn.clicked.connect(self._open_output_folder)

        self.cancel_btn = QPushButton("  Cancel")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setFixedWidth(110)
        self.cancel_btn.clicked.connect(self._cancel_dubbing)

        self.start_btn = QPushButton("  Start Dubbing")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.setEnabled(False)
        self.start_btn.setFixedHeight(44)
        self.start_btn.setFixedWidth(180)
        self.start_btn.clicked.connect(self._start_dubbing)

        btn_row.addWidget(self.open_output_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.start_btn)

        layout.addLayout(btn_row)
        return bar

    # ── Helpers ───────────────────────────────────────────────────────────

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background: {C_BORDER}; max-height: 1px; border: none;")
        return line

    # ── Video loading ─────────────────────────────────────────────────────

    def _browse_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "",
            "Video Files (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.flv);;All Files (*)"
        )
        if path:
            self._load_video(path)

    def _load_video(self, path: str):
        from core.audio_extractor import get_video_info
        self.video_path = path
        filename = Path(path).name

        try:
            info = get_video_info(path)
            dur = info["duration"]
            mins, secs = int(dur // 60), int(dur % 60)
            self.video_info_label.setText(
                f"{info['width']}×{info['height']}  ·  {mins}:{secs:02d}  ·  {info['format'].split(',')[0].upper()}"
            )
            self.video_info_label.setVisible(True)
        except Exception:
            self.video_info_label.setVisible(False)

        self.drop_zone.set_loaded(filename)
        self.file_label.setText(filename)
        self.file_label.setStyleSheet(f"color: #3fb950; font-size: 12px;")
        self.start_btn.setEnabled(True)
        self._log(f"Loaded: {path}")
        self.status_bar.showMessage(f"Ready  ·  {filename}")

    # ── Drag & drop ───────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(('.mp4', '.mkv', '.mov', '.avi', '.webm', '.m4v', '.flv')):
                self._load_video(path)
            else:
                QMessageBox.warning(self, "Unsupported File",
                    "Please drop a video file (MP4, MKV, MOV, AVI, WEBM).")

    # ── Dubbing pipeline ──────────────────────────────────────────────────

    def _start_dubbing(self):
        if not self.video_path:
            QMessageBox.warning(self, "No Video", "Please select a video file first.")
            return

        settings = self.voice_panel.get_settings()
        config = PipelineConfig(
            video_path=self.video_path,
            voice=settings["voice"],
            whisper_model=settings["whisper_model"],
            source_language=settings["source_language"],
            target_language=settings["target_language"],
            pivot_model=settings["pivot_model"],
            bgm_volume=settings["bgm_volume"],
            dubbed_volume=settings["dubbed_volume"],
            export_srt=settings["export_srt"],
            export_vtt=settings["export_vtt"],
            burn_subtitles=settings["burn_subtitles"],
        )

        # UI state
        self.start_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.cancel_btn.setEnabled(True)
        self.open_output_btn.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.tabs.setCurrentIndex(1)
        self.log_widget.clear()
        self._dot_count = 0
        self._dot_timer.start(500)

        self._log_separator()
        self._log(f"Video   : {Path(self.video_path).name}")
        self._log(f"Source  : {self.voice_panel.lang_combo.currentText()}")
        self._log(f"Target  : {self.voice_panel.target_combo.currentText()}")
        self._log(f"Voice   : {settings['voice']}")
        self._log(f"Model   : {settings['whisper_model']}")
        self._log_separator()

        self.worker = DubbingWorker(config)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.segments_ready.connect(self._on_segments_ready)
        self.worker.start()

    def _cancel_dubbing(self):
        if self.worker:
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)
            self._log("Cancelling...")

    def _on_progress(self, message: str):
        self._log(f"  {message}")
        # Strip dots for clean display
        clean = message.rstrip(". ")
        self.progress_label.setText(clean)
        self.status_bar.showMessage(clean)

        # Highlight active step badge
        msg_lower = message.lower()
        for i, keyword in enumerate(self.STEP_KEYWORDS):
            if keyword in msg_lower:
                for j, badge in enumerate(self.step_badges):
                    badge.set_active(j == i)
                break

    def _on_segments_ready(self, segments):
        self.subtitle_editor.load_segments(segments)
        self.tabs.setCurrentIndex(0)

    def _on_finished(self, output_paths: dict):
        self._dot_timer.stop()
        self.output_paths = output_paths
        video_out = output_paths.get("video", "")

        self._log_separator()
        self._log("DUBBING COMPLETE")
        self._log(f"Video : {video_out}")
        if output_paths.get("srt"):
            self._log(f"SRT   : {output_paths['srt']}")
        if output_paths.get("vtt"):
            self._log(f"VTT   : {output_paths['vtt']}")
        self._log_separator()

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_label.setText("Done!")
        self.progress_label.setStyleSheet(f"color: #3fb950; font-size: 12px;")
        self.status_bar.showMessage(f"Done  ·  {Path(video_out).name}")

        for badge in self.step_badges:
            badge.set_active(False)

        self.start_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self.open_output_btn.setVisible(True)

        QMessageBox.information(self, "Dubbing Complete",
            f"Khmer dubbed video saved:\n\n{video_out}")

    def _on_error(self, error_message: str):
        self._dot_timer.stop()
        self._log(f"\nERROR:\n{error_message}")
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Error — see log")
        self.progress_label.setStyleSheet(f"color: #f85149; font-size: 12px;")
        self.start_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        for badge in self.step_badges:
            badge.set_active(False)
        QMessageBox.critical(self, "Error", error_message[:600])

    # ── Utilities ─────────────────────────────────────────────────────────

    def _log(self, message: str):
        self.log_widget.append(message)

    def _log_separator(self):
        self.log_widget.append("─" * 52)

    def _tick_dots(self):
        self._dot_count = (self._dot_count + 1) % 4
        dots = "." * self._dot_count
        current = self.progress_label.text().rstrip(". ")
        self.progress_label.setText(current + dots)
        self.progress_label.setStyleSheet(f"color: {C_TEXT_DIM}; font-size: 12px;")

    def _open_output_folder(self):
        folder = str(OUTPUT_DIR)
        if os.path.exists(folder):
            subprocess.Popen(f'explorer "{folder}"')
