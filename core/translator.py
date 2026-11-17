"""
Translator - Multi-language → Khmer OR English

Target language is now selectable:
  - "km" → translate to Khmer (default)
  - "en" → translate to English

Translation backends (tried in order):
1. MyMemoryTranslator  — free, no API key, no IP rate limit
2. GoogleTranslator    — free, better quality, IP rate limits if abused
3. CLAck/en-km offline — cached local model, Khmer only fallback
"""
import time
import re
from typing import List, Callable

# MyMemory language codes
MYMEMORY_LANG = {
    "en":   "en-US",  "zh":   "zh-CN",  "fr":   "fr-FR",
    "es":   "es-ES",  "de":   "de-DE",  "ja":   "ja-JP",
    "ko":   "ko-KR",  "vi":   "vi-VN",  "th":   "th-TH",
    "ar":   "ar-SA",  "ru":   "ru-RU",  "pt":   "pt-PT",
    "it":   "it-IT",  "hi":   "hi-IN",  "id":   "id-ID",
    "km":   "km-KH",  "auto": "en-US",
}

# Google Translate language codes
GT_LANG_MAP = {
    "en": "en", "zh": "zh-CN", "fr": "fr", "es": "es",
    "de": "de", "ja": "ja",   "ko": "ko", "vi": "vi",
    "th": "th", "ar": "ar",   "ru": "ru", "pt": "pt",
    "it": "it", "hi": "hi",   "id": "id",
    "km": "km", "auto": "auto",
}

# Offline fallback (Khmer only)
OFFLINE_MODEL           = "CLAck/en-km"
OFFLINE_TOKENIZER_MODEL = "Helsinki-NLP/opus-mt-en-zh"
OFFLINE_MAX_LENGTH      = 256

BATCH_SIZE  = 10
BATCH_DELAY = 0.3


def _clean(text: str) -> str:
    """Remove repetition artifacts and normalize whitespace."""
    if not text:
        return ""
    for n in range(6, 1, -1):
        pat = r'(\b(?:\S+\s+){' + str(n - 1) + r'}\S+)\s+\1'
        text = re.sub(pat, r'\1', text, flags=re.UNICODE)
    return re.sub(r'\s{2,}', ' ', text).strip()


class Translator:
    """Multi-language → Khmer or English translator."""

    def __init__(self, progress_callback: Callable = None):
        self.progress_callback = progress_callback
        self._backend           = "mymemory"
        # Offline model (lazy-loaded, Khmer only)
        self._offline_model = None
        self._tok_in        = None
        self._tok_out       = None

    # ── MyMemory ─────────────────────────────────────────────────────────

    def _mymemory_batch(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        from deep_translator import MyMemoryTranslator
        mm_src = MYMEMORY_LANG.get(src_lang, "en-US")
        mm_tgt = MYMEMORY_LANG.get(tgt_lang, "km-KH")
        tr     = MyMemoryTranslator(source=mm_src, target=mm_tgt)
        results = []
        for text in texts:
            if not text.strip():
                results.append("")
                continue
            r = tr.translate(text[:490])
            results.append(_clean(r or ""))
            time.sleep(0.15)
        return results

    # ── Google Translate ──────────────────────────────────────────────────

    def _google_batch(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        from deep_translator import GoogleTranslator
        gt_src = GT_LANG_MAP.get(src_lang, "auto")
        gt_tgt = GT_LANG_MAP.get(tgt_lang, "km")
        tr     = GoogleTranslator(source=gt_src, target=gt_tgt)
        results = []
        for text in texts:
            if not text.strip():
                results.append("")
                continue
            r = tr.translate(text[:4500])
            results.append(_clean(r or ""))
            time.sleep(0.25)
        return results

    # ── Offline CLAck/en-km (Khmer only) ─────────────────────────────────

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
        """Offline fallback — English → Khmer only."""
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

    # ── Routing ───────────────────────────────────────────────────────────

    def _translate_chunk(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        if self._backend == "mymemory":
            try:
                return self._mymemory_batch(texts, src_lang, tgt_lang)
            except Exception as e:
                print(f"[Translator] MyMemory failed ({e}), trying Google.")
                self._backend = "google"

        if self._backend == "google":
            try:
                return self._google_batch(texts, src_lang, tgt_lang)
            except Exception as e:
                print(f"[Translator] Google failed ({e}), using offline model.")
                self._backend = "offline"

        # Offline only supports EN→KM
        if tgt_lang != "km":
            print("[Translator] Offline fallback only supports Khmer target. Returning original text.")
            return texts
        return self._offline_batch(texts)

    # ── Public API ────────────────────────────────────────────────────────

    def translate(self, text: str, src_lang: str = "en", tgt_lang: str = "km") -> str:
        if not text or not text.strip():
            return ""
        return self.translate_batch([text], src_lang=src_lang, tgt_lang=tgt_lang)[0]

    def translate_batch(
        self,
        texts: List[str],
        src_lang: str = "en",
        tgt_lang: str = "km",
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

            translated = self._translate_chunk(non_empty, src_lang, tgt_lang)

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
        tgt_lang: str = "km",
        pivot_model: str = None,
        progress_callback: Callable = None,
    ):
        """
        Translate TranscriptionSegment objects in-place.
        Sets segment.khmer_text (used for both Khmer and English target output).
        """
        texts = [seg.text for seg in segments]
        translations = self.translate_batch(
            texts, src_lang=src_lang, tgt_lang=tgt_lang,
            progress_callback=progress_callback,
        )
        for seg, translated in zip(segments, translations):
            seg.khmer_text = translated   # field reused for any target language
        return segments
