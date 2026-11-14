"""
Dubbing Pipeline - Orchestrates the full dubbing workflow:
1. Extract audio
2. Transcribe (STT) — supports any language Whisper knows
3. Pivot translate (source → English, if not English)
4. Translate (English → Khmer)
5. Generate Khmer voices (TTS)
6. Sync audio to timeline
7. Mix with background audio
8. Export final video + subtitles
"""
import os
import tempfile
import shutil
from pathlib import Path
from typing import Callable, Optional, List
from dataclasses import dataclass, field

from core.audio_extractor import extract_audio, extract_audio_full_quality, get_video_info
from core.transcriber import Transcriber, TranscriptionSegment
from core.translator import Translator
from core.tts_engine import TTSEngine
from core.audio_sync import AudioSyncEngine
from core.subtitle_generator import generate_srt, generate_vtt
from core.video_exporter import VideoExporter
from config import OUTPUT_DIR


@dataclass
class PipelineConfig:
    """Configuration for a dubbing job."""
    video_path: str
    voice: str = "km-KH-PisethNeural"
    whisper_model: str = "base"
    source_language: str = "auto"       # Whisper language code, or "auto"
    pivot_model: Optional[str] = None   # HuggingFace model for source→EN pivot
    bgm_volume: float = 0.1
    dubbed_volume: float = 1.0
    export_srt: bool = True
    export_vtt: bool = True
    burn_subtitles: bool = False
    output_dir: str = None


class DubbingPipeline:
    """Full end-to-end dubbing pipeline."""

    def __init__(self, config: PipelineConfig, progress_callback: Callable = None):
        self.config = config
        self.progress_callback = progress_callback
        self.segments: List[TranscriptionSegment] = []
        self.temp_dir = None
        self.output_dir = Path(config.output_dir or OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)

        self.is_cancelled = False
        self.current_step = ""

    def cancel(self):
        self.is_cancelled = True

    def _progress(self, message: str):
        self.current_step = message
        if self.progress_callback:
            self.progress_callback(message)
        print(f"[Pipeline] {message}")

    def _check_cancel(self):
        if self.is_cancelled:
            raise InterruptedError("Pipeline cancelled by user.")

    def run(self) -> dict:
        self.temp_dir = tempfile.mkdtemp(prefix="khmer_dubbing_")
        try:
            return self._execute_pipeline()
        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _execute_pipeline(self) -> dict:
        video_path = self.config.video_path
        temp = Path(self.temp_dir)

        # ── Step 1: Video info ───────────────────────────────────────────
        self._progress("Reading video file...")
        video_info = get_video_info(video_path)
        video_duration = video_info["duration"]
        self._check_cancel()

        # ── Step 2: Extract audio ────────────────────────────────────────
        self._progress("Extracting audio from video...")
        whisper_audio = str(temp / "whisper_audio.wav")
        extract_audio(video_path, whisper_audio)

        original_audio = str(temp / "original_audio.wav")
        extract_audio_full_quality(video_path, original_audio)
        self._check_cancel()

        # ── Step 3: Transcribe ───────────────────────────────────────────
        # Pass "auto" as None to Whisper so it auto-detects
        whisper_lang = self.config.source_language
        if whisper_lang == "auto":
            whisper_lang = None

        lang_display = self.config.source_language.upper() if whisper_lang else "Auto"
        self._progress(f"Recognizing speech (Whisper AI) — Source: {lang_display}...")

        transcriber = Transcriber(
            model_size=self.config.whisper_model,
            progress_callback=self._progress,
        )
        self.segments = transcriber.transcribe(
            whisper_audio,
            language=whisper_lang,
            progress_callback=self._progress,
        )
        # Store the actual detected language for the translator
        self._detected_lang = whisper_lang or "en"
        self._check_cancel()

        if not self.segments:
            raise RuntimeError(
                "No speech detected in the video.\n"
                "Please check the video has clear audio and the correct source language is selected."
            )

        # ── Step 4: Translate ─────────────────────────────────────────────
        # If a pivot model is set: source → English → Khmer
        # If no pivot model: English → Khmer directly
        if self.config.pivot_model:
            self._progress(
                f"Translating to English first (pivot: {self.config.pivot_model.split('/')[-1]})..."
            )
        else:
            self._progress("Translating to Khmer...")

        # Pass detected language to translator (MyMemory handles all languages natively)
        detected_lang = getattr(self, '_detected_lang', None) or whisper_lang or "en"
        translator = Translator(progress_callback=self._progress)
        translator.translate_segments(
            self.segments,
            src_lang=detected_lang,
            progress_callback=self._progress,
        )
        self._check_cancel()

        # ── Step 5: Generate Khmer TTS ───────────────────────────────────
        self._progress("Generating Khmer voices...")
        tts_dir = str(temp / "tts_audio")
        tts_engine = TTSEngine(
            voice=self.config.voice,
            progress_callback=self._progress,
        )
        tts_engine.generate_segments(
            self.segments,
            output_dir=tts_dir,
            progress_callback=self._progress,
        )
        self._check_cancel()

        # ── Step 6: Assemble dubbed audio track ──────────────────────────
        self._progress("Synchronizing audio with video timeline...")
        sync_engine = AudioSyncEngine(progress_callback=self._progress)

        dubbed_track_path = str(temp / "dubbed_track.wav")
        sync_engine.build_dubbed_track(
            self.segments,
            video_duration=video_duration,
            output_path=dubbed_track_path,
            progress_callback=self._progress,
        )
        self._check_cancel()

        # ── Step 7: Mix with background audio ────────────────────────────
        self._progress("Mixing with background music...")
        mixed_audio_path = str(temp / "mixed_audio.wav")
        sync_engine.mix_with_background(
            dubbed_track_path=dubbed_track_path,
            original_audio_path=original_audio,
            output_path=mixed_audio_path,
            bgm_volume=self.config.bgm_volume,
            progress_callback=self._progress,
        )
        self._check_cancel()

        # ── Step 8: Generate subtitles ───────────────────────────────────
        output_paths = {}
        video_stem = Path(video_path).stem

        if self.config.export_srt:
            self._progress("Generating SRT subtitles...")
            srt_path = str(self.output_dir / f"{video_stem}_khmer.srt")
            generate_srt(self.segments, srt_path, use_khmer=True)
            output_paths["srt"] = srt_path

        if self.config.export_vtt:
            self._progress("Generating VTT subtitles...")
            vtt_path = str(self.output_dir / f"{video_stem}_khmer.vtt")
            generate_vtt(self.segments, vtt_path, use_khmer=True)
            output_paths["vtt"] = vtt_path

        self._check_cancel()

        # ── Step 9: Export final video ───────────────────────────────────
        self._progress("Exporting final dubbed video...")
        final_video = str(self.output_dir / f"{video_stem}_khmer_dubbed.mp4")

        exporter = VideoExporter(progress_callback=self._progress)
        exporter.export(
            video_path=video_path,
            dubbed_audio_path=mixed_audio_path,
            output_path=final_video,
            subtitle_path=output_paths.get("srt"),
            burn_subtitles=self.config.burn_subtitles,
            progress_callback=self._progress,
        )

        output_paths["video"] = final_video
        self._progress(f"Done! Output: {final_video}")

        return output_paths
