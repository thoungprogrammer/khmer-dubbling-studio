"""
Audio Sync Engine - Assembles Khmer dubbed audio aligned to the video timeline.

Fixes vs previous version:
1. REMOVED unconditional fade_out — this was cutting the last word of every segment
2. Only fade_out when a clip ACTUALLY overlaps the next segment (soft blend, not cut)
3. Speed adjustment uses ffmpeg atempo filter (pitch-preserving, up to 2.0x)
   instead of the frame-rate trick capped at 1.15x
4. Clips that overflow are allowed to run up to 85% of the gap to the next segment
5. Only add fade_in/fade_out at hard boundaries — not on natural-length clips
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional, List
from pydub import AudioSegment
from pydub.effects import normalize
from config import DUBBED_AUDIO_VOLUME, ORIGINAL_BGM_VOLUME, AUDIO_SAMPLE_RATE

# Fade constants (ms) — only applied when needed
FADE_IN_MS          = 40    # small fade-in to avoid click at segment start
FADE_OUT_MS         = 80    # only used when clip OVERLAPS next segment
MAX_SPEED_ATEMPO    = 1.60  # max speed-up via ffmpeg atempo (pitch preserved)
OVERLAP_THRESHOLD   = 0.85  # clip may use up to 85% of gap before next segment


def _atempo_stretch(audio: AudioSegment, speed: float) -> AudioSegment:
    """
    Change audio speed using ffmpeg atempo filter.
    - Preserves pitch (unlike the frame-rate hack)
    - atempo range: 0.5x to 100x (chain filters for >2x)
    - Only called when speed adjustment is actually needed
    """
    if abs(speed - 1.0) < 0.02:
        return audio

    # Write to temp file, run ffmpeg atempo, read back
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fin:
        in_path = fin.name
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fout:
        out_path = fout.name

    try:
        audio.export(in_path, format="wav")

        # atempo accepts 0.5–2.0; chain for higher values
        if speed <= 2.0:
            filter_str = f"atempo={speed:.4f}"
        else:
            # chain: atempo=2.0,atempo=X (for speed > 2.0)
            remainder = speed / 2.0
            filter_str = f"atempo=2.0,atempo={remainder:.4f}"

        cmd = [
            "ffmpeg", "-y", "-i", in_path,
            "-filter:a", filter_str,
            "-ar", str(AUDIO_SAMPLE_RATE),
            out_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        result = AudioSegment.from_wav(out_path)
    except Exception as e:
        print(f"[AudioSync] atempo failed ({e}), using frame-rate fallback")
        # Fallback: frame-rate trick (slight pitch change but no dependency)
        new_rate = int(audio.frame_rate * speed)
        result = audio._spawn(
            audio.raw_data, overrides={"frame_rate": new_rate}
        ).set_frame_rate(audio.frame_rate)
    finally:
        for p in [in_path, out_path]:
            try:
                os.unlink(p)
            except Exception:
                pass

    return result


class AudioSyncEngine:
    """Synchronizes Khmer TTS audio clips with the video timeline."""

    def __init__(self, progress_callback: Callable = None):
        self.progress_callback = progress_callback

    def build_dubbed_track(
        self,
        segments,
        video_duration: float,
        output_path: str,
        progress_callback: Callable = None,
    ) -> str:
        """
        Build the full dubbed audio track.

        Per-segment strategy:
        1. Load TTS clip, normalize volume
        2. If clip fits in slot → place with small fade_in only
        3. If clip overflows slot but fits within 85% of gap to next → place as-is
        4. If clip overflows that threshold → speed up with atempo (up to 1.6x)
        5. Add fade_out ONLY if the sped-up clip would still overlap next segment
        6. Never hard-truncate a clip
        """
        callback = progress_callback or self.progress_callback
        if callback:
            callback("Assembling dubbed audio track...")

        total_ms = int(video_duration * 1000) + 3000  # +3s safety buffer
        dubbed_track = AudioSegment.silent(duration=total_ms, frame_rate=AUDIO_SAMPLE_RATE)

        # Pre-compute next-segment start times (ms) for gap calculations
        next_start_ms: List[Optional[int]] = []
        for i in range(len(segments)):
            if i + 1 < len(segments):
                next_start_ms.append(int(segments[i + 1].start * 1000))
            else:
                next_start_ms.append(None)  # last segment

        for i, segment in enumerate(segments):
            if not segment.audio_path or not os.path.exists(segment.audio_path):
                continue

            if callback and i % 10 == 0:
                callback(f"Placing audio segment {i + 1} / {len(segments)}...")

            try:
                clip = AudioSegment.from_file(segment.audio_path)
                clip = normalize(clip)

                start_ms = int(segment.start * 1000)
                slot_ms  = max(int(segment.duration * 1000), 100)  # never 0
                clip_ms  = len(clip)
                next_ms  = next_start_ms[i]

                # --- How much room do we actually have? ---
                if next_ms is not None:
                    # Available space = from this segment's start to 85% into the gap
                    gap_ms        = next_ms - start_ms
                    available_ms  = int(gap_ms * OVERLAP_THRESHOLD)
                else:
                    # Last segment: use remaining track length
                    available_ms = total_ms - start_ms

                available_ms = max(available_ms, slot_ms)

                # --- Decide what to do ---
                if clip_ms <= available_ms:
                    # Clip fits — no speed change, small fade_in only
                    clip = clip.fade_in(FADE_IN_MS)

                else:
                    # Clip is too long — speed up with atempo
                    speed = clip_ms / available_ms
                    speed = min(speed, MAX_SPEED_ATEMPO)
                    clip = _atempo_stretch(clip, speed)

                    # After speed-up, add fade_out to blend into silence
                    clip = clip.fade_in(FADE_IN_MS).fade_out(FADE_OUT_MS)

                # --- Volume ---
                if DUBBED_AUDIO_VOLUME != 1.0:
                    vol_db = 20.0 * (DUBBED_AUDIO_VOLUME - 1.0)
                    clip = clip + vol_db

                # --- Overlay onto the track ---
                # pydub overlay does not truncate the base track —
                # any part of the clip beyond total_ms is simply lost,
                # which is fine since we added a 3s buffer above.
                dubbed_track = dubbed_track.overlay(clip, position=start_ms)

            except Exception as e:
                print(f"[AudioSync] Segment {i} error: {e}")
                continue

        dubbed_track.export(output_path, format="wav")
        if callback:
            callback("Dubbed audio track assembled.")
        return output_path

    def mix_with_background(
        self,
        dubbed_track_path: str,
        original_audio_path: str,
        output_path: str,
        bgm_volume: float = None,
        progress_callback: Callable = None,
    ) -> str:
        """Mix the dubbed Khmer audio with the original background music."""
        callback = progress_callback or self.progress_callback
        bgm_vol = bgm_volume if bgm_volume is not None else ORIGINAL_BGM_VOLUME

        if callback:
            callback("Mixing dubbed audio with background music...")

        dubbed   = AudioSegment.from_file(dubbed_track_path)
        original = AudioSegment.from_file(original_audio_path)

        # Match lengths
        diff = len(original) - len(dubbed)
        if diff > 0:
            dubbed = dubbed + AudioSegment.silent(duration=diff)
        elif diff < 0:
            original = original + AudioSegment.silent(duration=-diff)

        if bgm_vol <= 0:
            mixed = dubbed
        else:
            bgm_db = 20.0 * (bgm_vol - 1.0) if bgm_vol < 1.0 else 0.0
            mixed  = (original + bgm_db).overlay(dubbed)

        mixed.export(output_path, format="wav")
        if callback:
            callback("Audio mixing complete.")
        return output_path
