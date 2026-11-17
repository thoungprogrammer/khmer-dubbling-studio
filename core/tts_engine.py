"""
TTS Engine - Multi-language Text-to-Speech using Microsoft Edge TTS.

Supports:
  - Khmer  : km-KH-PisethNeural (male), km-KH-SreymomNeural (female)
  - English: en-US-AndrewNeural, en-US-AriaNeural, en-GB-RyanNeural,
             en-GB-SoniaNeural, en-AU-WilliamNeural, en-AU-NatashaNeural

Parallel async generation — 5 segments at once for speed.
"""
import asyncio
import os
import tempfile
import time
from pathlib import Path
from typing import List, Callable, Optional
import edge_tts
from config import VOICES_BY_TARGET, DEFAULT_VOICE

DEFAULT_RATE   = "+0%"
MAX_CONCURRENT = 5


class TTSEngine:
    """Multi-language TTS using Edge TTS neural voices — parallel generation."""

    def __init__(self, voice: str = None, progress_callback: Callable = None):
        self.voice             = voice or DEFAULT_VOICE
        self.progress_callback = progress_callback

    def set_voice(self, voice_id: str):
        self.voice = voice_id

    # ── Async core ────────────────────────────────────────────────────────

    async def _generate_one(
        self,
        text: str,
        output_path: str,
        voice: str,
        rate: str,
        semaphore: asyncio.Semaphore,
        retries: int = 2,
    ) -> bool:
        async with semaphore:
            for attempt in range(retries + 1):
                try:
                    comm = edge_tts.Communicate(text=text, voice=voice, rate=rate)
                    await comm.save(output_path)
                    return True
                except Exception as e:
                    if attempt < retries:
                        await asyncio.sleep(0.8)
                    else:
                        print(f"[TTS] Failed: {e} | text: {text[:40]}")
                        return False

    async def _generate_all_async(
        self,
        tasks: List[dict],
        progress_callback: Callable = None,
    ):
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        total     = len(tasks)
        done      = [0]

        async def _wrap(task):
            ok = await self._generate_one(
                task["text"], task["path"], task["voice"], task["rate"], semaphore
            )
            done[0] += 1
            if progress_callback and done[0] % 5 == 0:
                progress_callback(f"Generating voice {done[0]} / {total}...")
            return ok

        return await asyncio.gather(*[_wrap(t) for t in tasks])

    # ── Public API ────────────────────────────────────────────────────────

    def generate_segments(
        self,
        segments,
        output_dir: str,
        progress_callback: Callable = None,
        speaker_voices: dict = None,
    ) -> list:
        """
        Generate TTS audio for all segments in parallel.
        Uses segment.khmer_text as the text source (holds translated text
        in whatever target language was selected).
        """
        callback  = progress_callback or self.progress_callback
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        if callback:
            callback(f"Generating voices for {len(segments)} segments...")

        tasks        = []
        task_to_seg  = {}

        for i, seg in enumerate(segments):
            if not seg.khmer_text or not seg.khmer_text.strip():
                seg.audio_path = ""
                continue

            voice = self.voice
            if speaker_voices and seg.speaker in speaker_voices:
                voice = speaker_voices[seg.speaker]

            path = str(output_dir / f"segment_{i:04d}.mp3")
            tasks.append({"text": seg.khmer_text, "path": path,
                          "voice": voice, "rate": DEFAULT_RATE})
            task_to_seg[len(tasks) - 1] = i

        if not tasks:
            return segments

        try:
            results = asyncio.run(
                self._generate_all_async(tasks, progress_callback=callback)
            )
        except RuntimeError:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                results = pool.submit(
                    asyncio.run,
                    self._generate_all_async(tasks, progress_callback=callback)
                ).result()

        for task_idx, ok in enumerate(results):
            seg_idx = task_to_seg[task_idx]
            if ok and os.path.exists(tasks[task_idx]["path"]):
                segments[seg_idx].audio_path = tasks[task_idx]["path"]
            else:
                segments[seg_idx].audio_path = ""

        if callback:
            success = sum(1 for r in results if r)
            callback(f"Voice generation complete: {success}/{len(tasks)} clips.")

        return segments

    def generate(self, text: str, output_path: str = None, rate: str = None) -> str:
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
        asyncio.run(self._generate_one(
            text, output_path, self.voice, rate or DEFAULT_RATE,
            asyncio.Semaphore(1)
        ))
        return output_path

    @staticmethod
    def get_voices_for_language(lang_code: str) -> dict:
        """Return the voice dict for a given target language code."""
        return VOICES_BY_TARGET.get(lang_code, VOICES_BY_TARGET["km"])
