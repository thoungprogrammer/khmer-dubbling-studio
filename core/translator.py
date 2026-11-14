"""
Translator - Multi-language → Khmer

Translation backends (tried in order):
1. MyMemoryTranslator  — free, no API key, no IP rate limit, good Khmer quality
2. GoogleTranslator    — free, better quality, but has IP rate limits from testing
3. CLAck/en-km offline — cached local model, fallback when both online fail

MyMemory supports 50 languages including Khmer natively.
No pivot translation needed — single call handles any source language.
"""
import time
import re
from typing import List, Callable

# MyMemory language codes (source: "en-US", target: "km-KH")
MYMEMORY_LANG = {
    "en":   "en-US",  "zh":   "zh-CN",  "fr":   "fr-FR",
    "es":   "es-ES",  "de":   "de-DE",  "ja":   "ja-JP",
    "ko":   "ko-KR",  "vi":   "vi-VN",  "th":   "th-TH",
    "ar":   "ar-SA",  "ru":   "ru-RU",  "pt":   "pt-PT",
    "it":   "it-IT",  "hi":   "hi-IN",  "id":   "id-ID",
    "auto": "en-US",
}

# Google Translate language codes
GT_LANG_MAP = {
    "en": "en", "zh": "zh-CN", "fr": "fr", "es": "es",
    "de": "de", "ja": "ja",   "ko": "ko", "vi": "vi",
    "th": "th", "ar": "ar",   "ru": "ru", "pt": "pt",
    "it": "it", "hi": "hi",   "id": "id", "auto": "auto",
}

# Offline fallback
OFFLINE_MODEL           = "CLAck/en-km"
OFFLINE_TOKENIZER_MODEL = "Helsinki-NLP/opus-mt-en-zh"
OFFLINE_MAX_LENGTH      = 256

# Batch size — MyMemory has a 500 char limit per request,
# so we keep batches at 10 short segments
BATCH_SIZE    = 10
BATCH_DELAY   = 0.3   # seconds between batch calls


def _clean(text: str) -> str:
    """Remove repetition artifacts and normalize whitespace."""
    if not text:
        return ""
    for n in range(6, 1, -1):
        pat = r'(\b(?:\S+\s+){' + str(n - 1) + r'}\S+)\s+\1'
        text = re.sub(pat, r'\1', text, flags=re.UNICODE)
    return re.sub(r'\s{2,}', ' ', text).strip()


class Translator:
    """Multi-language → Khmer with online/offline fallback chain."""

    def __init__(self, progress_callback: Callable = None):
        self.progress_callback = progress_callback
        self._backend          = "mymemory"  # "mymemory" | "google" | "offline"
        # Offline model (lazy-loaded)
        self._offline_model = None
        self._tok_in        = None
        self._tok_out       = None

    # ── MyMemory backend ──────────────────────────────────────────────────

    def _mymemory_batch(self, texts: List[str], src_lang: str) -> List[str]:
        from deep_translator import MyMemoryTranslator
        mm_src = MYMEMORY_LANG.get(src_lang, "en-US")
        tr     = MyMemoryTranslator(source=mm_src, target="km-KH")
        results = []
        for text in texts:
            if not text.strip():
                results.append("")
                continue
            # MyMemory 500-char limit — truncate gracefully
            chunk = text[:490]
            r = tr.translate(chunk)
            results.append(_clean(r or ""))
            time.sleep(0.15)   # ~6 req/s, well within free limit
        return results

    # ── Google Translate backend ──────────────────────────────────────────

    def _google_batch(self, texts: List[str], src_lang: str) -> List[str]:
        from deep_translator import GoogleTranslator
        gt_src = GT_LANG_MAP.get(src_lang, "auto")
        tr     = GoogleTranslator(source=gt_src, target="km")
        results = []
        for text in texts:
            if not text.strip():
                results.append("")
                continue
            r = tr.translate(text[:4500])
            results.append(_clean(r or ""))
            time.sleep(0.25)
        return results

    # ── Offline CLAck/en-km fallback ─────────────────────────────────────

    def _load_offline(self):
        if self._offline_model:
            return
        if self.progress_callback:
            self.progress_callback("Loading offline translation model...")
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        self._tok_out = AutoTokenizer.from_pretrained(OFFLINE_MODEL)
        self._tok_in  = AutoTokenizer.from_pretrained(OFFLINE_TOKENIZER_MODEL)
        self._tok_in.add_tokens(["<2zh>", "<2khm>"], special_tokens=True)
        self._offline_model = AutoModelForSeq2SeqLM.from_pretrained(OFFLINE_MODEL)
        self._offline_model.eval()

    def _offline_batch(self, texts: List[str]) -> List[str]:
        import torch
        self._load_offline()
        prefixed = [f"<2khm> {t.strip()}" for t in texts]
        inputs = self._tok_in(
            prefixed, return_tensors="pt", padding=True,
            truncation=True, max_length=OFFLINE_MAX_LENGTH,
        )
        with torch.no_grad():
            out = self._offline_model.generate(
                **inputs, max_length=OFFLINE_MAX_LENGTH,
                num_beams=4, early_stopping=True,
                no_repeat_ngram_size=4, length_penalty=0.8,
            )
        return [_clean(self._tok_out.decode(t, skip_special_tokens=True)) for t in out]

    # ── Routing with fallback chain ───────────────────────────────────────

    def _translate_chunk(self, texts: List[str], src_lang: str) -> List[str]:
        if self._backend == "mymemory":
            try:
                return self._mymemory_batch(texts, src_lang)
            except Exception as e:
                print(f"[Translator] MyMemory failed ({e}), trying Google.")
                self._backend = "google"

        if self._backend == "google":
            try:
                return self._google_batch(texts, src_lang)
            except Exception as e:
                print(f"[Translator] Google failed ({e}), using offline model.")
                self._backend = "offline"

        return self._offline_batch(texts)

    # ── Public API ────────────────────────────────────────────────────────

    def translate(self, text: str, src_lang: str = "en") -> str:
        if not text or not text.strip():
            return ""
        return self.translate_batch([text], src_lang=src_lang)[0]

    def translate_batch(
        self,
        texts: List[str],
        src_lang: str = "en",
        pivot_model: str = None,          # API compat — not used
        progress_callback: Callable = None,
        batch_size: int = BATCH_SIZE,
    ) -> List[str]:
        callback = progress_callback or self.progress_callback
        total    = len(texts)
        results  = []

        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            if callback:
                callback(f"Translating {min(i + batch_size, total)} / {total}...")

            non_empty_idx = [j for j, t in enumerate(batch) if t.strip()]
            non_empty     = [batch[j] for j in non_empty_idx]

            if not non_empty:
                results.extend([""] * len(batch))
                continue

            translated = self._translate_chunk(non_empty, src_lang)

            batch_out = [""] * len(batch)
            for idx, orig_idx in enumerate(non_empty_idx):
                batch_out[orig_idx] = translated[idx] if idx < len(translated) else ""
            results.extend(batch_out)

        if callback:
            callback(f"Translation complete: {total} segments.")
        return results

    def translate_segments(
        self,
        segments,
        src_lang: str = "en",
        pivot_model: str = None,
        progress_callback: Callable = None,
    ):
        """Translate TranscriptionSegment objects in-place (sets .khmer_text)."""
        texts = [seg.text for seg in segments]
        translations = self.translate_batch(
            texts, src_lang=src_lang,
            progress_callback=progress_callback,
        )
        for seg, kh in zip(segments, translations):
            seg.khmer_text = kh
        return segments
