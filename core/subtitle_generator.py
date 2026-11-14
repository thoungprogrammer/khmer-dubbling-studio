"""
Subtitle Generator - Creates SRT and VTT subtitle files from transcription segments.
"""
import srt
import datetime
from pathlib import Path
from typing import List


def seconds_to_timedelta(seconds: float) -> datetime.timedelta:
    """Convert float seconds to timedelta."""
    return datetime.timedelta(seconds=seconds)


def generate_srt(segments, output_path: str, use_khmer: bool = True) -> str:
    """
    Generate an SRT subtitle file from transcription segments.
    
    Args:
        segments: List of TranscriptionSegment objects
        output_path: Where to save the .srt file
        use_khmer: If True, use Khmer translation; if False, use original text
    
    Returns:
        Path to generated SRT file
    """
    subtitles = []
    
    for i, segment in enumerate(segments, start=1):
        text = segment.khmer_text if use_khmer and segment.khmer_text else segment.text
        
        if not text.strip():
            continue
        
        sub = srt.Subtitle(
            index=i,
            start=seconds_to_timedelta(segment.start),
            end=seconds_to_timedelta(segment.end),
            content=text,
        )
        subtitles.append(sub)
    
    srt_content = srt.compose(subtitles)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    return output_path


def generate_vtt(segments, output_path: str, use_khmer: bool = True) -> str:
    """
    Generate a WebVTT subtitle file from transcription segments.
    
    Args:
        segments: List of TranscriptionSegment objects
        output_path: Where to save the .vtt file
        use_khmer: If True, use Khmer translation
    
    Returns:
        Path to generated VTT file
    """
    lines = ["WEBVTT", ""]
    
    for i, segment in enumerate(segments, start=1):
        text = segment.khmer_text if use_khmer and segment.khmer_text else segment.text
        
        if not text.strip():
            continue
        
        start_str = _format_vtt_time(segment.start)
        end_str = _format_vtt_time(segment.end)
        
        lines.append(str(i))
        lines.append(f"{start_str} --> {end_str}")
        lines.append(text)
        lines.append("")
    
    vtt_content = "\n".join(lines)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(vtt_content)
    
    return output_path


def generate_bilingual_srt(segments, output_path: str) -> str:
    """
    Generate bilingual SRT with English on top, Khmer below.
    Useful for checking translation quality.
    """
    subtitles = []
    
    for i, segment in enumerate(segments, start=1):
        if not segment.text.strip():
            continue
        
        # English + Khmer combined
        content = segment.text
        if segment.khmer_text:
            content += f"\n{segment.khmer_text}"
        
        sub = srt.Subtitle(
            index=i,
            start=seconds_to_timedelta(segment.start),
            end=seconds_to_timedelta(segment.end),
            content=content,
        )
        subtitles.append(sub)
    
    srt_content = srt.compose(subtitles)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    return output_path


def _format_vtt_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm for VTT."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def load_srt(srt_path: str) -> list:
    """Load an SRT file and return parsed subtitle list."""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    return list(srt.parse(content))
