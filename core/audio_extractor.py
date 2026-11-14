"""
Audio Extractor - Extracts audio from video files using FFmpeg
"""
import subprocess
import os
from pathlib import Path


def extract_audio(video_path: str, output_audio_path: str = None) -> str:
    """
    Extract audio from a video file using FFmpeg.
    
    Args:
        video_path: Path to the input video file
        output_audio_path: Optional path for extracted audio (WAV format)
    
    Returns:
        Path to the extracted audio file
    """
    video_path = Path(video_path)
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if output_audio_path is None:
        output_audio_path = str(video_path.parent / f"{video_path.stem}_audio.wav")
    
    # Extract audio using FFmpeg: 16kHz mono WAV (optimal for Whisper)
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",                    # No video
        "-acodec", "pcm_s16le",   # PCM 16-bit
        "-ar", "16000",           # 16kHz sample rate (Whisper requirement)
        "-ac", "1",               # Mono channel
        "-y",                     # Overwrite output
        output_audio_path
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed:\n{result.stderr}")
    
    return output_audio_path


def extract_audio_full_quality(video_path: str, output_audio_path: str = None) -> str:
    """
    Extract full quality audio for mixing (stereo, original sample rate).
    Used for preserving background music.
    """
    video_path = Path(video_path)
    
    if output_audio_path is None:
        output_audio_path = str(video_path.parent / f"{video_path.stem}_original_audio.wav")
    
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "-y",
        output_audio_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg full audio extraction failed:\n{result.stderr}")
    
    return output_audio_path


def get_video_info(video_path: str) -> dict:
    """
    Get video metadata: duration, fps, resolution, etc.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"FFprobe failed:\n{result.stderr}")
    
    import json
    info = json.loads(result.stdout)
    
    video_stream = next(
        (s for s in info.get("streams", []) if s.get("codec_type") == "video"),
        {}
    )
    audio_stream = next(
        (s for s in info.get("streams", []) if s.get("codec_type") == "audio"),
        {}
    )
    
    duration = float(info.get("format", {}).get("duration", 0))
    
    return {
        "duration": duration,
        "fps": eval(video_stream.get("r_frame_rate", "24/1")),
        "width": video_stream.get("width", 0),
        "height": video_stream.get("height", 0),
        "audio_channels": audio_stream.get("channels", 2),
        "audio_sample_rate": audio_stream.get("sample_rate", "44100"),
        "format": info.get("format", {}).get("format_name", "unknown"),
    }
