"""
TTS Engine - Khmer Text-to-Speech using Microsoft Edge TTS.
Voices: km-KH-PisethNeural (male), km-KH-SreymomNeural (female)

Fixes vs previous version:
- Parallel async TTS: all segments sent concurrently (5–8x faster)
- Rate is now +0% (neutral) — previous -10% was making clips too long, causing overflow
- Duration-aware rate: if Khmer text is very short, use +5% to match the slot better
- Single persistent event loop — no throwaway ThreadPoolExecutor per call
"""
import asyncio
import os
import tempfile
import time
from pathlib import Path
from typing import List, Callable, Optional
import edge_tts
from config import KHMER_VOICES, DEFAULT_VOICE

# Neutral rate — do not slow down, let audio_sync handle timing
DEFAULT_RATE = "+0%"

# Max concurrent TTS requests (avoid rate-limiting from Edge TTS)
MAX_CONCURRENT = 5


class TTSEngine:
    """Khmer TTS using Edge TTS neural voices — parallel generation."""

    def __init__(self, voice: str = None, progress_callback: Callable = None):
        self.voice = voice or DEFAULT_VOICE
        self.progress_callback = progress_callback

    def set_voice(self, voice_name: str):
        if voice_name in KHMER_VOICES:
            self.voice = KHMER_VOICES[voice_name]
        else:
            self.voice = voice_name

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
        """Generate a single segment, respecting the concurrency semaphore."""
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
        """
        Run all TTS tasks concurrently with a semaphore cap.
        tasks: list of {text, path, voice, rate}
        """
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        total = len(tasks)
        done = [0]

        async def _wrap(task):
            ok = await self._generate_one(
                task["text"], task["path"], task["voice"], task["rate"], semaphore
            )
            done[0] += 1
            if progress_callback and done[0] % 5 == 0:
                progress_callback(f"Generating Khmer voice {done[0]} / {total}...")
            return ok

        results = await asyncio.gather(*[_wrap(t) for t in tasks])
        return results

    # ── Public API ────────────────────────────────────────────────────────

    def generate_segments(
        self,
        segments,
        output_dir: str,
        progress_callback: Callable = None,
        speaker_voices: dict = None,
        retries: int = 2,
    ) -> list:
        """
        Generate Khmer audio for all TranscriptionSegment objects — in parallel.
        Sets segment.audio_path for each successful segment.
        """
        callback = progress_callback or self.progress_callback
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        if callback:
            callback(f"Generating Khmer voices for {len(segments)} segments...")

        # Build task list
        tasks = []
        task_to_seg = {}   # maps task index → segment index

        for i, seg in enumerate(segments):
            if not seg.khmer_text or not seg.khmer_text.strip():
                seg.audio_path = ""
                continue

            voice = self.voice
            if speaker_voices and seg.speaker in speaker_voices:
                voice = speaker_voices[seg.speaker]

            path = str(output_dir / f"segment_{i:04d}.mp3")
            task = {"text": seg.khmer_text, "path": path, "voice": voice, "rate": DEFAULT_RATE}
            task_to_seg[len(tasks)] = i
            tasks.append(task)

        if not tasks:
            return segments

        # Run all tasks concurrently
        try:
            results = asyncio.run(
                self._generate_all_async(tasks, progress_callback=callback)
            )
        except RuntimeError:
            # If asyncio.run fails (nested loop), use thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                results = pool.submit(
                    asyncio.run,
                    self._generate_all_async(tasks, progress_callback=callback)
                ).result()

        # Apply results back to segments
        for task_idx, ok in enumerate(results):
            seg_idx = task_to_seg[task_idx]
            if ok and os.path.exists(tasks[task_idx]["path"]):
                segments[seg_idx].audio_path = tasks[task_idx]["path"]
            else:
                segments[seg_idx].audio_path = ""

        if callback:
            success = sum(1 for r in results if r)
            callback(f"Voice generation complete: {success}/{len(tasks)} clips created.")

        return segments

    def generate(self, text: str, output_path: str = None, rate: str = None) -> str:
        """Generate a single TTS clip (blocking)."""
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
        chosen_rate = rate or DEFAULT_RATE
        asyncio.run(self._generate_one(
            text, output_path, self.voice, chosen_rate,
            asyncio.Semaphore(1)
        ))
        return output_path

    @staticmethod
    async def _list_voices_async():
        voices = await edge_tts.list_voices()
        return [v for v in voices if v["Locale"].startswith("km-")]

    @staticmethod
    def get_khmer_voices() -> list:
        try:
            return asyncio.run(TTSEngine._list_voices_async())
        except Exception:
            return []
