# 🎬 Khmer Dubbing Studio

**Automatic English → Khmer Video Dubbing using AI**

---

## Features

- 🎙️ Speech recognition using OpenAI Whisper (runs locally, offline)
- 🌐 English to Khmer translation using Helsinki-NLP OPUS-MT (runs offline)
- 🔊 Natural Khmer voices — male (Piseth) and female (Sreymom) using Microsoft Edge TTS
- 🎞️ Automatic audio synchronization with the video timeline
- 🎵 Background music preservation with volume control
- 📝 Built-in subtitle editor (SRT + VTT export)
- 🖥️ Modern dark-themed professional UI
- 📁 Drag & drop video loading

---

## Requirements

- Windows 10/11 (64-bit)
- Python 3.11
- FFmpeg installed and added to PATH
- Internet connection (for Edge TTS voice generation and first-time model download)
- ~4GB free disk space (for AI models)

---

## Installation

### Step 1: Install Python 3.11
Download from: https://www.python.org/downloads/release/python-3119/
Install the 64-bit version.

### Step 2: Install FFmpeg
1. Download from: https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your Windows PATH environment variable

### Step 3: Run Setup
Double-click `setup.bat` — it will create a virtual environment and install all dependencies.

### Step 4: Run the Application
Double-click `run.bat`

---

## First Run Notes

On first use, the app will automatically download:
- Whisper `base` model (~150MB) — for speech recognition
- OPUS-MT `en-km` model (~300MB) — for English-to-Khmer translation

These are saved locally and do not need to be downloaded again.

---

## Usage

1. Launch with `run.bat`
2. Drag your video file onto the drop zone (or click to browse)
3. Select a Khmer voice (Male/Female)
4. Choose Whisper model quality
5. Adjust audio mix volumes
6. Click **▶ Start Dubbing**
7. Wait for processing (time depends on video length and your CPU)
8. Review and edit subtitles in the Subtitle Editor tab
9. Find your output in the `output/` folder

---

## Output Files

| File | Description |
|------|-------------|
| `*_khmer_dubbed.mp4` | Final video with Khmer dubbing |
| `*_khmer.srt` | Khmer subtitle file (SRT format) |
| `*_khmer.vtt` | Khmer subtitle file (WebVTT format) |

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| UI | PyQt6 |
| Speech-to-Text | OpenAI Whisper (local) |
| Translation | Helsinki-NLP OPUS-MT (local, offline) |
| Khmer TTS | Microsoft Edge TTS (free) |
| Video Processing | FFmpeg |
| Audio Processing | pydub |

---

## Troubleshooting

**"FFmpeg not found"** — Install FFmpeg and add it to your PATH

**"No speech detected"** — Make sure your video has clear audio and the source language is English

**TTS error** — Check your internet connection (Edge TTS requires internet)

**Slow processing** — Use a smaller Whisper model (tiny/base) for faster but less accurate transcription

---

Built with ❤️ for the Khmer community
