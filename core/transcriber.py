"""
Transcriber - Speech-to-Text using OpenAI Whisper.

ROOT CAUSE FIX for "1 segment = whole video" problem:
  Whisper sometimes groups entire conversations into one long segment.
  This causes one TTS clip to cover 10-15 seconds — impossible to sync.

SOLUTION:
  1. Use word_timestamps=True to get per-word timing from Whisper
  2. Split on sentence boundaries (. ! ? ) using word-level timestamps
  3. Each sentence becomes its own segment with precise start/end time
  4. Max segment duration capped at 6 seconds — force split if longer
  5. Result: 20-50 small segments instead of 1-3 giant ones
"""
import re
import whisper
import torch
from typing import List, Callable
from config import WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_DEVICE

# Maximum duration of a single segment in seconds
# If Whisper gives us anything longer, we split it further
MAX_SEGMENT_SEC  = 6.0

# Minimum duration — ignore segments shorter than this (noise/artefacts)
MIN_SEGMENT_SEC  = 0.3

FILLER_PATTERNS = [
    r"^\s*\[.*?\]\s*$",
    r"^\s*\(.*?\)\s*$",
    r"^\s*♪.*?♪\s*$",
    r"^\s*\.{3,}\s*$",
    r"^\s*-\s*$",
    r"(?i)^\s*(thank you|thanks)\s*\.?\s*$",
    r"(?i)^\s*subtitles?\s*(by|:).*$",
]
FILLER_RE = [re.compile(p) for p in FILLER_PATTERNS]


def _clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^\s*[,\.;:]+", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _is_filler(text: str) -> bool:
    if not text or len(text.strip()) < 2:
        return True
    for pat in FILLER_RE:
        if pat.match(text.strip()):
            return True
    return False


class TranscriptionSegment:
    """A single timed speech segment."""

    def __init__(self, start: float, end: float, text: str, speaker: str = "Speaker 1"):
        self.start      = start
        self.end        = end
        self.text       = text
        self.speaker    = speaker
        self.khmer_text = ""
        self.audio_path = ""

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> dict:
        return {
            "start": self.start, "end": self.end,
            "text": self.text,   "speaker": self.speaker,
            "khmer_text": self.khmer_text,
        }

    def __repr__(self):
        return f"[{self.start:.2f}s-{self.end:.2f}s] {self.text[:50]}"


def _split_by_words(words: list, max_sec: float = MAX_SEGMENT_SEC) -> List[TranscriptionSegment]:
    """
    Build segments from Whisper word-level timestamps.
    Splits at sentence punctuation (. ! ?) AND whenever a segment
    exceeds max_sec seconds.
    """
    if not words:
        return []

    segments   = []
    buf_words  = []
    buf_start  = None

    def _flush(end_time: float):
        nonlocal buf_words, buf_start
        if not buf_words:
            return
        text = _clean_text(" ".join(w.get("word", "").strip() for w in buf_words))
        if not _is_filler(text):
            dur = end_time - buf_start
            if dur >= MIN_SEGMENT_SEC:
                segments.append(TranscriptionSegment(
                    start=buf_start,
                    end=end_time,
                    text=text,
                ))
        buf_words = []
        buf_start = None

    for w in words:
        word  = w.get("word", "").strip()
        wst   = w.get("start", 0.0)
        wend  = w.get("end",   wst + 0.1)

        if buf_start is None:
            buf_start = wst

        buf_words.append(w)

        # Split at sentence-ending punctuation
        is_sentence_end = bool(re.search(r'[.!?]\s*$', word))

        # Also split if segment is getting too long
        is_too_long = (wend - buf_start) >= max_sec

        if is_sentence_end or is_too_long:
            _flush(wend)

    # Flush any remaining words
    if buf_words:
        last_end = buf_words[-1].get("end", buf_words[-1].get("start", 0.0) + 0.1)
        _flush(last_end)

    return segments


def _split_long_segment(seg: TranscriptionSegment) -> List[TranscriptionSegment]:
    """
    If a segment from Whisper has no word data and is too long,
    split it evenly by sentences based on punctuation.
    """
    if seg.duration <= MAX_SEGMENT_SEC:
        return [seg]

    # Split text by sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', seg.text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= 1:
        return [seg]

    # Distribute time evenly across sentences
    total_chars = sum(len(s) for s in sentences)
    if total_chars == 0:
        return [seg]

    result  = []
    current = seg.start
    for s in sentences:
        proportion = len(s) / total_chars
        duration   = seg.duration * proportion
        end        = min(current + duration, seg.end)
        result.append(TranscriptionSegment(
            start=current, end=end, text=s
        ))
        current = end

    return result


class Transcriber:
    """High-accuracy Whisper transcriber with sentence-level segmentation."""

    def __init__(self, model_size: str = None, progress_callback: Callable = None):
        self.model_size        = model_size or WHISPER_MODEL
        self.progress_callback = progress_callback
        self.model             = None

    def load_model(self):
        if self.model is None:
            if self.progress_callback:
                self.progress_callback(f"Loading Whisper '{self.model_size}' model...")
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

        callback = progress_callback or self.progress_callback

        if callback:
            callback("Loading speech recognition model...")

        model = self.load_model()

        if callback:
            callback("Transcribing audio...")

        result = model.transcribe(
            str(audio_path),
            language=language,
            task="transcribe",
            verbose=False,
            beam_size=5,
            best_of=5,
            temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
            condition_on_previous_text=True,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            word_timestamps=True,          # KEY: get per-word timing
            initial_prompt=(
                "The following is a transcription of a video with multiple speakers. "
                "Transcribe each sentence separately and accurately."
            ),
        )

        detected_lang = result.get("language", language or "unknown")
        if callback:
            callback(f"Detected language: {detected_lang.upper()}")

        # --- Build segments from word-level timestamps ---
        segments = []

        for whisper_seg in result.get("segments", []):
            # Check segment quality
            avg_logprob    = whisper_seg.get("avg_logprob", 0)
            no_speech_prob = whisper_seg.get("no_speech_prob", 0)
            if avg_logprob < -1.5 or no_speech_prob > 0.8:
                continue

            words = whisper_seg.get("words", [])

            if words:
                # Use word-level data to split into sentences
                sub_segs = _split_by_words(words, MAX_SEGMENT_SEC)
                segments.extend(sub_segs)
            else:
                # No word data — fall back to segment-level with text splitting
                text = _clean_text(whisper_seg.get("text", ""))
                if _is_filler(text):
                    continue
                raw_seg = TranscriptionSegment(
                    start=whisper_seg["start"],
                    end=whisper_seg["end"],
                    text=text,
                )
                segments.extend(_split_long_segment(raw_seg))

        if callback:
            callback(f"Transcription complete: {len(segments)} segments found.")

        return segments

    def detect_language(self, audio_path: str) -> str:
        model = self.load_model()
        audio = whisper.load_audio(str(audio_path))
        audio = whisper.pad_or_trim(audio)
        mel   = whisper.log_mel_spectrogram(audio).to(model.device)
        _, probs = model.detect_language(mel)
        return max(probs, key=probs.get)
