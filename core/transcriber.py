"""
Transcriber - Speech-to-Text using OpenAI Whisper (runs locally, offline)
Outputs timestamped segments for precise dubbing synchronization.

Accuracy improvements:
- condition_on_previous_text=True for better context continuity
- compression_ratio_threshold tuned to avoid hallucinations
- logprob_threshold to filter low-confidence segments
- no_speech_threshold to skip silence
- temperature fallback for harder audio
- Post-processing: strip filler words, normalize whitespace
"""
import re
import whisper
import torch
from pathlib import Path
from typing import List, Callable, Optional
from config import WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_DEVICE


# Common filler words / hallucination phrases Whisper sometimes produces
FILLER_PATTERNS = [
    r"^\s*\[.*?\]\s*$",           # [Music], [Applause], [Laughter] etc.
    r"^\s*\(.*?\)\s*$",           # (Music), (Inaudible) etc.
    r"^\s*♪.*?♪\s*$",             # ♪ music notes ♪
    r"^\s*\.{3,}\s*$",            # ... (pure ellipsis)
    r"^\s*-\s*$",                 # lone dash
    r"(?i)^\s*(thank you|thanks)\s*\.?\s*$",   # standalone "thank you"
    r"(?i)^\s*subtitles?\s*(by|:).*$",         # "Subtitles by..."
]
FILLER_RE = [re.compile(p) for p in FILLER_PATTERNS]


def _clean_text(text: str) -> str:
    """Remove artifacts and normalize whitespace from Whisper output."""
    text = text.strip()
    # Remove leading/trailing punctuation artifacts
    text = re.sub(r"^\s*[,\.;:]+", "", text)
    # Normalize multiple spaces
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _is_filler(text: str) -> bool:
    """Return True if the segment is a filler / hallucination to skip."""
    if not text or len(text.strip()) < 2:
        return True
    for pattern in FILLER_RE:
        if pattern.match(text.strip()):
            return True
    return False


class TranscriptionSegment:
    """Represents a single speech segment with timing."""

    def __init__(self, start: float, end: float, text: str, speaker: str = "Speaker 1"):
        self.start = start
        self.end = end
        self.text = text
        self.speaker = speaker
        self.khmer_text = ""
        self.audio_path = ""

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "speaker": self.speaker,
            "khmer_text": self.khmer_text,
        }

    def __repr__(self):
        return f"[{self.start:.2f}s - {self.end:.2f}s] {self.text[:50]}"


class Transcriber:
    """High-accuracy Whisper-based speech transcription engine."""

    def __init__(self, model_size: str = None, progress_callback: Callable = None):
        self.model_size = model_size or WHISPER_MODEL
        self.progress_callback = progress_callback
        self.model = None

    def load_model(self):
        """Load Whisper model (downloads on first use)."""
        if self.model is None:
            if self.progress_callback:
                self.progress_callback(
                    f"Loading Whisper '{self.model_size}' model..."
                )
            device = WHISPER_DEVICE
            if device == "cuda" and not torch.cuda.is_available():
                device = "cpu"
            self.model = whisper.load_model(self.model_size, device=device)
        return self.model

    def transcribe(
        self,
        audio_path: str,
        language: str = None,
        progress_callback: Callable = None,
    ) -> List[TranscriptionSegment]:
        """
        Transcribe audio and return clean, timestamped segments.

        Accuracy settings used:
        - beam_size=5          → wider beam = more accurate (default is 5 but explicit)
        - best_of=5            → sample 5 candidates, pick best
        - temperature=(0,)     → greedy first, fallback to 0.2/0.4 if needed
        - condition_on_previous_text=True → use context from prior segments
        - compression_ratio_threshold=2.4 → discard overly repetitive output
        - logprob_threshold=-1.0          → filter very low-confidence segments
        - no_speech_threshold=0.6         → skip near-silent segments
        - word_timestamps=True            → precise word-level timing
        """
        callback = progress_callback or self.progress_callback

        if callback:
            callback("Loading speech recognition model...")

        model = self.load_model()

        if callback:
            callback("Transcribing audio... (this may take a few minutes)")

        result = model.transcribe(
            str(audio_path),
            language=language,                  # None = auto-detect
            task="transcribe",
            verbose=False,
            # ── Accuracy settings ──────────────────────────
            beam_size=5,
            best_of=5,
            temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),  # fallback ladder
            condition_on_previous_text=True,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            word_timestamps=True,
            # ── Prompt hint for better proper nouns ────────
            initial_prompt=(
                "The following is a clear transcription of a video. "
                "Transcribe accurately without paraphrasing."
            ),
        )

        # Merge detected language info into callback
        detected_lang = result.get("language", language or "unknown")
        if callback:
            callback(f"Detected language: {detected_lang.upper()}")

        segments = []
        for seg in result.get("segments", []):
            text = _clean_text(seg.get("text", ""))

            # Skip fillers, silence markers, hallucinations
            if _is_filler(text):
                continue

            # Skip very low confidence segments
            avg_logprob = seg.get("avg_logprob", 0)
            no_speech_prob = seg.get("no_speech_prob", 0)
            if avg_logprob < -1.5 or no_speech_prob > 0.8:
                continue

            segment = TranscriptionSegment(
                start=seg["start"],
                end=seg["end"],
                text=text,
            )
            segments.append(segment)

        if callback:
            callback(f"Transcription complete: {len(segments)} segments found.")

        return segments

    def detect_language(self, audio_path: str) -> str:
        """Auto-detect the spoken language in the audio."""
        model = self.load_model()
        audio = whisper.load_audio(str(audio_path))
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        _, probs = model.detect_language(mel)
        return max(probs, key=probs.get)
