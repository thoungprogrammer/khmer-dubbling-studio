# 🎬 Khmer Dubbing Studio

> AI-powered desktop application that automatically dubs videos from any language into natural-sounding Khmer audio.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## What It Does

Upload any video — English, Chinese, French, Korean, Japanese, or 15 other languages — and the app will:

1. **Transcribe** the original speech using OpenAI Whisper (runs locally, offline)
2. **Translate** it into Khmer using MyMemory / Google Translate
3. **Generate** natural Khmer voiceovers using Microsoft Edge TTS (Piseth male / Sreymom female)
4. **Synchronize** the dubbed audio with the original video timeline
5. **Export** a finished Khmer-dubbed MP4 + SRT/VTT subtitle files

---

## Features

- 🌐 **15+ source languages** — English, Chinese, French, Korean, Japanese, Vietnamese, Thai, Arabic, and more
- 🎤 **Natural Khmer voices** — male (Piseth) and female (Sreymom) Neural TTS
- ⚡ **Parallel TTS generation** — 5 segments processed simultaneously for speed
- 🎵 **Background music preservation** — original BGM kept at adjustable volume
- 📝 **Built-in subtitle editor** — edit Khmer translations before exporting
- 🖋️ **Khmer font support** — Noto Sans Khmer and 100+ Khmer fonts in the subtitle editor
- 🖥️ **Modern dark UI** — drag & drop, live progress steps, processing log
- 📁 **SRT + VTT export** — compatible with YouTube, VLC, and all major video players

---

## GPU vs CPU

The app works on both CPU and GPU. GPU makes Whisper speech recognition **5–10x faster**.

| Component | CPU | GPU (NVIDIA) |
|---|---|---|
| Whisper (speech recognition) | ✅ Works, slower | ✅ Works, 5–10x faster |
| Translation (MyMemory) | ✅ Uses internet | ✅ Uses internet |
| Edge TTS (voice) | ✅ Uses internet | ✅ Uses internet |
| Audio sync / FFmpeg | ✅ Fast | ✅ Fast |

**To enable GPU (NVIDIA only):**

After installing normally, run this command to replace CPU PyTorch with the CUDA version:

```bash
# CUDA 12.1 (for most modern NVIDIA GPUs)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 --force-reinstall --no-deps
```

> ⚠️ This downloads ~2.4GB. Only do this on a fast internet connection.
> Your GPU must support CUDA. Check at: https://developer.nvidia.com/cuda-gpus

---

## Requirements

| Requirement | Details |
|---|---|
| Python | 3.11 (required — not 3.12 or higher) |
| FFmpeg | Must be installed and added to PATH |
| Internet | Required for translation (MyMemory) and TTS (Edge TTS) |
| Disk space | ~2GB free (for AI models downloaded on first run) |
| OS | Windows 10/11 or Linux (Ubuntu 20.04+) |

---

## Installation — Windows

### Step 1 — Install Python 3.11

Download the **Windows 64-bit installer** from:
https://www.python.org/downloads/release/python-3119/

During installation:
- ✅ Check **"Add Python to PATH"**
- Click **Install Now**

### Step 2 — Install FFmpeg

**Option A — Using winget (recommended):**
```powershell
winget install Gyan.FFmpeg
```
Then **restart your terminal** so PATH updates take effect.

**Option B — Manual:**
1. Download from: https://www.gyan.dev/ffmpeg/builds/ → `ffmpeg-release-essentials.zip`
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your Windows PATH:
   - Search **"Environment Variables"** in Start menu
   - Edit **Path** under System Variables → Add `C:\ffmpeg\bin`
4. Restart your terminal and run `ffmpeg -version` to confirm

### Step 3 — Clone or Download the Project

```powershell
git clone https://github.com/thoungprogrammer/khmer-dubbling-studio.git
cd khmer-dubbling-studio
```

### Step 4 — Run Setup

Double-click **`setup.bat`**

This will:
- Create a Python 3.11 virtual environment
- Install all required packages automatically

### Step 5 — Run the App

Double-click **`run.bat`**

---

## Installation — Linux (Ubuntu / Debian)

### Step 1 — Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y ffmpeg
sudo apt install -y libxcb-xinerama0 libxcb-cursor0 libgl1
```

Verify FFmpeg:
```bash
ffmpeg -version
```

### Step 2 — Clone the Project

```bash
git clone https://github.com/thoungprogrammer/khmer-dubbling-studio.git
cd khmer-dubbling-studio
```

### Step 3 — Run Setup

```bash
chmod +x setup.sh
./setup.sh
```

### Step 4 — Run the App

```bash
./run.sh
```

---

## Installation — Linux (Fedora / RHEL)

### Step 1 — Install Dependencies

```bash
sudo dnf install -y python3.11 python3.11-devel
sudo dnf install -y ffmpeg
sudo dnf install -y libxcb mesa-libGL
```

### Step 2 — Clone and Setup

```bash
git clone https://github.com/thoungprogrammer/khmer-dubbling-studio.git
cd khmer-dubbling-studio
chmod +x setup.sh
./setup.sh
```

### Step 3 — Run

```bash
./run.sh
```

---

## First Run — What Gets Downloaded Automatically

On first use, the app downloads these AI models once and caches them locally:

| Model | Size | Purpose |
|---|---|---|
| Whisper `base` | ~150 MB | Speech recognition |
| CLAck/en-km (offline fallback) | ~300 MB | Offline Khmer translation |

After the first run, **speech recognition and offline translation work without internet.**

Translation (MyMemory) and voice generation (Edge TTS) still require internet.

---

## How to Use

1. Launch the app (`run.bat` on Windows, `./run.sh` on Linux)
2. **Drag your video** onto the drop zone, or click to browse
3. Select the **Source Language** of your video (or leave as Auto Detect)
4. Choose a **Khmer Voice** — Male (Piseth) or Female (Sreymom)
5. Choose **Whisper Model** — `base` is recommended for most videos
6. Adjust **Background Music Volume** slider
7. Click **▶ Start Dubbing**
8. Watch progress in the **Processing Log** tab
9. Review and fix translations in the **Subtitle Editor** tab
10. Output files are saved to the `output/` folder

---

## Output Files

| File | Description |
|---|---|
| `*_khmer_dubbed.mp4` | Final video with Khmer dubbing |
| `*_khmer.srt` | Khmer subtitles (SRT format) |
| `*_khmer.vtt` | Khmer subtitles (WebVTT format) |

---

## Supported Source Languages

| Language | Code | Method |
|---|---|---|
| English | en | Direct → Khmer |
| Chinese | zh | Chinese → Khmer |
| French | fr | French → Khmer |
| Spanish | es | Spanish → Khmer |
| German | de | German → Khmer |
| Japanese | ja | Japanese → Khmer |
| Korean | ko | Korean → Khmer |
| Vietnamese | vi | Vietnamese → Khmer |
| Thai | th | Thai → Khmer |
| Arabic | ar | Arabic → Khmer |
| Russian | ru | Russian → Khmer |
| Portuguese | pt | Portuguese → Khmer |
| Italian | it | Italian → Khmer |
| Hindi | hi | Hindi → Khmer |
| Indonesian | id | Indonesian → Khmer |

---

## Technology Stack

| Component | Technology |
|---|---|
| Desktop UI | PyQt6 |
| Speech-to-Text | OpenAI Whisper (local, offline) |
| Translation | MyMemory → Google Translate → CLAck/en-km (fallback chain) |
| Khmer TTS | Microsoft Edge TTS — km-KH-PisethNeural / km-KH-SreymomNeural |
| Audio sync | pydub + FFmpeg atempo filter |
| Video export | FFmpeg |
| Khmer fonts | Noto Sans Khmer + 100+ installed fonts |

---

## Accuracy

| Step | Accuracy |
|---|---|
| Speech recognition (Whisper base) | ~80–85% |
| Translation (MyMemory) | ~65–75% |
| Khmer voice quality (Edge TTS) | ~90% |
| Audio sync | ~75–80% |
| **Overall** | **~70–75%** |

Translation is the weakest link because Khmer is a low-resource language with limited training data.
You can improve results by editing translations manually in the **Subtitle Editor** before exporting.

Using **Whisper `small` or `medium`** improves speech recognition accuracy significantly.

---

## Troubleshooting

**`FFmpeg not found`**
→ Install FFmpeg and restart your terminal. Run `ffmpeg -version` to confirm.

**`No speech detected`**
→ Make sure the video has clear audio. Avoid heavy background music.
→ Select the correct source language instead of Auto Detect.

**`Translation returns English instead of Khmer`**
→ MyMemory sometimes returns English for very short phrases. This is a known limitation.
→ Edit manually in the Subtitle Editor.

**`App is slow`**
→ Switch Whisper model to `tiny` for faster processing.
→ Install CUDA PyTorch if you have an NVIDIA GPU (see GPU section above).

**`PyQt6 display error on Linux`**
→ Install missing Qt dependencies:
```bash
sudo apt install -y libxcb-xinerama0 libxcb-cursor0 libgl1 libglib2.0-0
```

**`Edge TTS error`**
→ Check your internet connection. Edge TTS requires internet for voice generation.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

MIT License — free to use, modify, and distribute.

---

Built with ❤️ for the Khmer community
