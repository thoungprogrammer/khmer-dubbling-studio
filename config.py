"""
Khmer Dubbing Studio - Configuration
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure directories exist
MODELS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Whisper STT settings
WHISPER_MODEL = "base"          # Options: tiny, base, small, medium, large
WHISPER_LANGUAGE = "en"         # Source language (English)
WHISPER_DEVICE = "cpu"          # Use "cuda" if you have a GPU

# Translation settings
# Using CLAck/en-km (publicly accessible, fine-tuned MarianMT for English→Khmer)
TRANSLATION_MODEL = "CLAck/en-km"
TRANSLATION_TOKENIZER_MODEL = "Helsinki-NLP/opus-mt-en-zh"  # Tokenizer for English input
TRANSLATION_MAX_LENGTH = 512

# Supported source languages for dubbing
# Format: "Display Name": ("whisper_code", "pivot_model_or_None")
# pivot_model is used to translate source → English first, then English → Khmer
# If pivot_model is None, the language is already English (no pivot needed)
SOURCE_LANGUAGES = {
    "Auto Detect":      ("auto",  None),
    "English":          ("en",    None),
    "Chinese":          ("zh",    "Helsinki-NLP/opus-mt-zh-en"),
    "French":           ("fr",    "Helsinki-NLP/opus-mt-fr-en"),
    "Spanish":          ("es",    "Helsinki-NLP/opus-mt-es-en"),
    "German":           ("de",    "Helsinki-NLP/opus-mt-de-en"),
    "Japanese":         ("ja",    "Helsinki-NLP/opus-mt-ja-en"),
    "Korean":           ("ko",    "Helsinki-NLP/opus-mt-ko-en"),
    "Vietnamese":       ("vi",    "Helsinki-NLP/opus-mt-vi-en"),
    "Thai":             ("th",    "Helsinki-NLP/opus-mt-th-en"),
    "Arabic":           ("ar",    "Helsinki-NLP/opus-mt-ar-en"),
    "Russian":          ("ru",    "Helsinki-NLP/opus-mt-ru-en"),
    "Portuguese":       ("pt",    "Helsinki-NLP/opus-mt-pt-en"),
    "Italian":          ("it",    "Helsinki-NLP/opus-mt-it-en"),
    "Hindi":            ("hi",    "Helsinki-NLP/opus-mt-hi-en"),
    "Indonesian":       ("id",    "Helsinki-NLP/opus-mt-id-en"),
}

# Edge TTS Khmer voices
KHMER_VOICES = {
    "Male - Piseth": "km-KH-PisethNeural",
    "Female - Sreymom": "km-KH-SreymomNeural",
}
DEFAULT_VOICE = "km-KH-PisethNeural"

# Audio settings
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 2
DUBBED_AUDIO_VOLUME = 1.0       # 0.0 to 2.0
ORIGINAL_BGM_VOLUME = 0.1       # Keep background music at 10%

# Video export settings
OUTPUT_FORMAT = "mp4"
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"

# UI settings
APP_NAME = "Khmer Dubbing Studio"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
THEME = "dark"
