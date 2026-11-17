"""
Audio Sync Engine - Assembles dubbed audio aligned to the video timeline.

ROOT CAUSE OF "dub too slow / not matching" problem:
  - Translated text is longer than original → TTS clip longer than the slot
  - Previous code only sped up to 1.6x max and allowed overflow
  - Overflow clips pile up → dub falls behind and never catches up

FIX:
  1. Each clip is HARD-FIT to its exact slot duration using atempo
     (pitch-preserving ffmpeg filter, up to 2.5x speed)
  2. If the clip is > 2.5x longer, we compress to 2.5x AND fade-out
     the tail gracefully — this is the absolute maximum without distortion
  3. No overflow allowed into next segment — each slot is independent
  4. Short clips (TTS faster than speech) play naturally with trailing silence
  5. Fade-in 30ms on every clip to avoid click artefacts
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional, List
from pydub import AudioSegment
from pydub.effects import normalize
from config import DUBBED_AUDIO_VOLUME, ORIGINAL_BGM_VOLUME, AUDIO_SAMPLE_RATE

# Fade in on every clip (avoids click at segment start)
FADE_IN_MS       = 30

# Fade out ONLY when we hit the max speed cap (graceful tail cutoff)
FADE_OUT_MS      = 80

# Maximum speed-up via atempo — above this distorts speech quality
MAX_SPEED_ATEMPO = 2.5

# Minimum slot we will ever try to fit a clip into (ms)
# Prevents absurd speed-ups on very short segments
MIN_SLOT_MS      = 300

# How much breathing room to leave at end of each slot (ms)
# Prevents clips from bleeding right up to the next word
SLOT_PADDING_MS  = 60


def _atempo_stretch(audio: AudioSegment, speed: float) -> AudioSegment:
    """
    Change audio speed using ffmpeg atempo (pitch-preserving).
    Chains filters for speeds > 2.0x (atempo max per filter is 2.0).
    Falls back to frame-rate trick if ffmpeg fails.
    """
    if abs(speed - 1.0) < 0.02:
        return audio

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fin:
        in_path = fin.name
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fout:
        out_path = fout.name

    try:
        audio.export(in_path, format="wav")

        # Build atempo filter chain
        # atempo accepts 0.5–2.0 per filter, chain for higher values
        if speed <= 2.0:
            filter_str = f"atempo={speed:.4f}"
        elif speed <= 4.0:
            # Two filters: each takes sqrt(speed)
            half = speed ** 0.5
            filter_str = f"atempo={half:.4f},atempo={half:.4f}"
        else:
            # Three filters for extreme speeds (rare)
            third = speed ** (1/3)
            filter_str = f"atempo={third:.4f},atempo={third:.4f},atempo={third:.4f}"

        cmd = [
            "ffmpeg", "-y", "-i", in_path,
            "-filter:a", filter_str,
            "-ar", str(AUDIO_SAMPLE_RATE),
            "-loglevel", "error",
            out_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        result = AudioSegment.from_wav(out_path)
    except Exception as e:
        print(f"[AudioSync] atempo failed ({e}), using frame-rate fallback")
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
    """Synchronizes dubbed TTS audio clips with the video timeline."""

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

        Each segment is fitted EXACTLY to its original time slot:
        - If TTS clip fits → place with 30ms fade-in
        - If TTS clip is too long → speed up with atempo to fit exactly
        - If speed needed > 2.5x → cap at 2.5x and fade out tail
        - Each slot is padded by SLOT_PADDING_MS to prevent bleed
        - No overflow into next segment ever
        """
        callback = progress_callback or self.progress_callback
        if callback:
            callback("Assembling dubbed audio track...")

        total_ms    = int(video_duration * 1000) + 3000
        dubbed_track = AudioSegment.silent(duration=total_ms, frame_rate=AUDIO_SAMPLE_RATE)

        for i, segment in enumerate(segments):
            if not segment.audio_path or not os.path.exists(segment.audio_path):
                continue

            if callback and i % 10 == 0:
                callback(f"Placing audio segment {i + 1} / {len(segments)}...")

            try:
                clip     = AudioSegment.from_file(segment.audio_path)
                clip     = normalize(clip)

                start_ms = int(segment.start * 1000)
                slot_ms  = max(int(segment.duration * 1000) - SLOT_PADDING_MS, MIN_SLOT_MS)
                clip_ms  = len(clip)

                if clip_ms <= slot_ms:
                    # Clip fits — just add small fade-in, no speed change
                    clip = clip.fade_in(FADE_IN_MS)

                else:
                    # Clip is longer than slot — calculate exact speed needed
                    speed = clip_ms / slot_ms

                    if speed <= MAX_SPEED_ATEMPO:
                        # Speed up to fit exactly — pitch preserved
                        clip = _atempo_stretch(clip, speed)
                        clip = clip.fade_in(FADE_IN_MS)
                    else:
                        # Too long even at max speed — compress to max, fade tail
                        clip = _atempo_stretch(clip, MAX_SPEED_ATEMPO)
                        # Trim to slot if still over
                        if len(clip) > slot_ms:
                            clip = clip[:slot_ms]
                        clip = clip.fade_in(FADE_IN_MS).fade_out(FADE_OUT_MS)

                # Volume adjustment
                if DUBBED_AUDIO_VOLUME != 1.0:
                    vol_db = 20.0 * (DUBBED_AUDIO_VOLUME - 1.0)
                    clip   = clip + vol_db

                # Place onto the track at the correct timestamp
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
        """Mix dubbed audio with original background music."""
        callback = progress_callback or self.progress_callback
        bgm_vol  = bgm_volume if bgm_volume is not None else ORIGINAL_BGM_VOLUME

        if callback:
            callback("Mixing dubbed audio with background music...")

        dubbed   = AudioSegment.from_file(dubbed_track_path)
        original = AudioSegment.from_file(original_audio_path)

        # Match lengths
        diff = len(original) - len(dubbed)
        if diff > 0:
            dubbed   = dubbed   + AudioSegment.silent(duration=diff)
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
