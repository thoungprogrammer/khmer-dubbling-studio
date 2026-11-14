"""
Video Exporter - Combines dubbed audio with the original video using FFmpeg.
"""
import subprocess
import os
from pathlib import Path
from typing import Callable, Optional
from config import VIDEO_CODEC, AUDIO_CODEC, OUTPUT_DIR


class VideoExporter:
    """Exports the final dubbed video using FFmpeg."""
    
    def __init__(self, progress_callback: Callable = None):
        self.progress_callback = progress_callback
    
    def export(
        self,
        video_path: str,
        dubbed_audio_path: str,
        output_path: str = None,
        subtitle_path: str = None,
        burn_subtitles: bool = False,
        progress_callback: Callable = None,
    ) -> str:
        """
        Export the final video with Khmer dubbed audio.
        
        Args:
            video_path: Original video file path
            dubbed_audio_path: Khmer dubbed audio file path
            output_path: Output video path (auto-generated if None)
            subtitle_path: Optional SRT path for subtitle burning
            burn_subtitles: Whether to burn subtitles into video
            progress_callback: Optional progress callback
        
        Returns:
            Path to exported video
        """
        callback = progress_callback or self.progress_callback
        
        video_path = Path(video_path)
        
        if output_path is None:
            output_path = str(OUTPUT_DIR / f"{video_path.stem}_khmer_dubbed.mp4")
        
        if callback:
            callback("Exporting final video...")
        
        if subtitle_path and burn_subtitles:
            output_path = self._export_with_subtitles(
                str(video_path), dubbed_audio_path, output_path, subtitle_path
            )
        else:
            output_path = self._export_basic(
                str(video_path), dubbed_audio_path, output_path
            )
        
        if callback:
            callback(f"Export complete: {output_path}")
        
        return output_path
    
    def _export_basic(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
    ) -> str:
        """Replace audio in video with dubbed audio."""
        cmd = [
            "ffmpeg",
            "-i", video_path,           # Original video (video stream)
            "-i", audio_path,           # New dubbed audio
            "-c:v", "copy",             # Copy video without re-encoding (faster)
            "-c:a", AUDIO_CODEC,        # Encode audio as AAC
            "-map", "0:v:0",            # Use video from first input
            "-map", "1:a:0",            # Use audio from second input
            "-shortest",                # Match shortest stream
            "-y",                       # Overwrite output
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg export failed:\n{result.stderr}")
        
        return output_path
    
    def _export_with_subtitles(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        subtitle_path: str,
    ) -> str:
        """Export with burned-in subtitles."""
        # Escape path for FFmpeg subtitle filter
        sub_path_escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", VIDEO_CODEC,
            "-c:a", AUDIO_CODEC,
            "-vf", f"subtitles='{sub_path_escaped}'",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg subtitle export failed:\n{result.stderr}")
        
        return output_path
    
    def get_output_path(self, video_path: str, suffix: str = "_khmer_dubbed") -> str:
        """Generate a default output path based on input video name."""
        p = Path(video_path)
        return str(OUTPUT_DIR / f"{p.stem}{suffix}.mp4")
