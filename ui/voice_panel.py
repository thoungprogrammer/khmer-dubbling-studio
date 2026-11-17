"""
Voice Panel - Settings sidebar with target language selection.
Supports dubbing into Khmer or English.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSlider, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from config import (
    VOICES_BY_TARGET, DEFAULT_VOICE,
    DUBBED_AUDIO_VOLUME, ORIGINAL_BGM_VOLUME,
    SOURCE_LANGUAGES, TARGET_LANGUAGES
)
from ui.styles import UI_FONT


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("sectionTitle")
    return lbl


def _hint_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("statusLabel")
    lbl.setWordWrap(True)
    return lbl


class VoicePanelWidget(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # ── Source Language ───────────────────────────────────────
        layout.addWidget(_section_label("SOURCE LANGUAGE"))

        self.lang_combo = QComboBox()
        for name in SOURCE_LANGUAGES.keys():
            self.lang_combo.addItem(name)
        self.lang_combo.setCurrentIndex(0)
        self.lang_combo.setToolTip(
            "The language spoken in your video.\n"
            "Auto Detect lets Whisper figure it out."
        )
        layout.addWidget(self.lang_combo)

        self.lang_info = _hint_label("Whisper will auto-detect the language.")
        layout.addWidget(self.lang_info)
        self.lang_combo.currentTextChanged.connect(self._on_lang_changed)

        layout.addWidget(self._divider())

        # ── Target Language ───────────────────────────────────────
        layout.addWidget(_section_label("TARGET LANGUAGE (DUB INTO)"))

        self.target_combo = QComboBox()
        for name in TARGET_LANGUAGES.keys():
            self.target_combo.addItem(name)
        self.target_combo.setCurrentIndex(0)   # Default: Khmer
        self.target_combo.setToolTip(
            "Choose the language you want the video dubbed into.\n"
            "Khmer — dub into Khmer (km-KH voices)\n"
            "English — dub into English (US/UK/AU voices)"
        )
        layout.addWidget(self.target_combo)

        self.target_info = _hint_label("Video will be dubbed into Khmer.")
        layout.addWidget(self.target_info)
        self.target_combo.currentTextChanged.connect(self._on_target_changed)

        layout.addWidget(self._divider())

        # ── Voice Selection ───────────────────────────────────────
        layout.addWidget(_section_label("VOICE"))

        self.voice_combo = QComboBox()
        self._populate_voices("km")   # populate with Khmer voices initially
        layout.addWidget(self.voice_combo)

        layout.addWidget(self._divider())

        # ── Whisper Model ─────────────────────────────────────────
        layout.addWidget(_section_label("SPEECH RECOGNITION MODEL"))

        self.whisper_combo = QComboBox()
        models = [
            ("tiny  — Fastest  (~75 MB)", "tiny"),
            ("base  — Balanced  (~150 MB)", "base"),
            ("small — Better  (~500 MB)", "small"),
            ("medium — Best  (~1.5 GB)", "medium"),
        ]
        for label, value in models:
            self.whisper_combo.addItem(label, value)
        self.whisper_combo.setCurrentIndex(1)
        layout.addWidget(self.whisper_combo)

        layout.addWidget(self._divider())

        # ── Audio Mix ─────────────────────────────────────────────
        layout.addWidget(_section_label("AUDIO MIX"))

        dubbed_row = QHBoxLayout()
        dubbed_row.addWidget(QLabel("Dubbed Voice"))
        dubbed_row.addStretch()
        self.dubbed_vol_label = QLabel(f"{int(DUBBED_AUDIO_VOLUME * 100)}%")
        self.dubbed_vol_label.setObjectName("accentLabel")
        dubbed_row.addWidget(self.dubbed_vol_label)
        layout.addLayout(dubbed_row)

        self.dubbed_vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.dubbed_vol_slider.setRange(0, 200)
        self.dubbed_vol_slider.setValue(int(DUBBED_AUDIO_VOLUME * 100))
        self.dubbed_vol_slider.valueChanged.connect(
            lambda v: self.dubbed_vol_label.setText(f"{v}%")
        )
        layout.addWidget(self.dubbed_vol_slider)

        bgm_row = QHBoxLayout()
        bgm_row.addWidget(QLabel("Background Music"))
        bgm_row.addStretch()
        self.bgm_vol_label = QLabel(f"{int(ORIGINAL_BGM_VOLUME * 100)}%")
        self.bgm_vol_label.setObjectName("accentLabel")
        bgm_row.addWidget(self.bgm_vol_label)
        layout.addLayout(bgm_row)

        self.bgm_vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.bgm_vol_slider.setRange(0, 100)
        self.bgm_vol_slider.setValue(int(ORIGINAL_BGM_VOLUME * 100))
        self.bgm_vol_slider.valueChanged.connect(
            lambda v: self.bgm_vol_label.setText(f"{v}%")
        )
        layout.addWidget(self.bgm_vol_slider)

        layout.addWidget(self._divider())

        # ── Export Options ────────────────────────────────────────
        layout.addWidget(_section_label("EXPORT OPTIONS"))

        self.export_srt_check = QCheckBox("Export SRT subtitles")
        self.export_srt_check.setChecked(True)
        layout.addWidget(self.export_srt_check)

        self.export_vtt_check = QCheckBox("Export VTT subtitles")
        self.export_vtt_check.setChecked(True)
        layout.addWidget(self.export_vtt_check)

        self.burn_subs_check = QCheckBox("Burn subtitles into video")
        self.burn_subs_check.setChecked(False)
        layout.addWidget(self.burn_subs_check)

        layout.addStretch()

    # ── Helpers ───────────────────────────────────────────────────

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: #30363d; max-height: 1px; border: none; margin: 2px 0;")
        return line

    def _populate_voices(self, lang_code: str):
        """Repopulate the voice dropdown for a given target language."""
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        voices = VOICES_BY_TARGET.get(lang_code, VOICES_BY_TARGET["km"])
        for name in voices.keys():
            self.voice_combo.addItem(name)
        self.voice_combo.blockSignals(False)

    # ── Slots ─────────────────────────────────────────────────────

    def _on_lang_changed(self, lang_name: str):
        lang_data = SOURCE_LANGUAGES.get(lang_name)
        if not lang_data:
            return
        _, pivot = lang_data
        if lang_name == "Auto Detect":
            self.lang_info.setText("Whisper will auto-detect the language.")
        elif pivot is None:
            self.lang_info.setText("Direct translation — no pivot needed.")
        else:
            self.lang_info.setText(f"{lang_name} → target language.")

    def _on_target_changed(self, target_name: str):
        """Update voice list and info when target language changes."""
        lang_code = TARGET_LANGUAGES.get(target_name, "km")
        self._populate_voices(lang_code)
        if lang_code == "km":
            self.target_info.setText("Video will be dubbed into Khmer.")
            self.export_srt_check.setText("Export Khmer SRT subtitles")
            self.export_vtt_check.setText("Export Khmer VTT subtitles")
        else:
            self.target_info.setText("Video will be dubbed into English.")
            self.export_srt_check.setText("Export English SRT subtitles")
            self.export_vtt_check.setText("Export English VTT subtitles")

    # ── Settings ──────────────────────────────────────────────────

    def get_settings(self) -> dict:
        """Return all current settings as a dict for the pipeline."""
        target_name  = self.target_combo.currentText()
        target_code  = TARGET_LANGUAGES.get(target_name, "km")
        voices       = VOICES_BY_TARGET.get(target_code, VOICES_BY_TARGET["km"])
        voice_name   = self.voice_combo.currentText()
        voice_id     = voices.get(voice_name, DEFAULT_VOICE)

        lang_name    = self.lang_combo.currentText()
        whisper_code, pivot_model = SOURCE_LANGUAGES.get(lang_name, ("auto", None))

        return {
            "voice":           voice_id,
            "whisper_model":   self.whisper_combo.currentData(),
            "source_language": whisper_code,
            "target_language": target_code,
            "pivot_model":     pivot_model,
            "dubbed_volume":   self.dubbed_vol_slider.value() / 100.0,
            "bgm_volume":      self.bgm_vol_slider.value() / 100.0,
            "export_srt":      self.export_srt_check.isChecked(),
            "export_vtt":      self.export_vtt_check.isChecked(),
            "burn_subtitles":  self.burn_subs_check.isChecked(),
        }
