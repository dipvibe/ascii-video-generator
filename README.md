# ASCII Video Generator

Turn any video into ASCII art, played fullscreen with its original audio.

Built with Python, OpenCV, NumPy and Pillow.


---

## Table of Contents

1. [Features](#features)
2. [How it works](#how-it-works)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Running the program](#running-the-program)
6. [Controls](#controls)
7. [Configuration](#configuration)
8. [Console output](#console-output)
9. [Tips](#tips)
10. [Troubleshooting](#troubleshooting)
11. [Project structure](#project-structure)
12. [Roadmap](#roadmap)
13. [Acknowledgements](#acknowledgements)
14. [License](#license)

---

## Features

- Plays any video as ASCII art in a fullscreen window
- Keeps the original aspect ratio, with a configurable output resolution (e.g. 1920 × 1080)
- Audio playback in sync with the picture (via `ffplay`)
- Clean, solid shadows and adjustable contrast (gamma, shadow cutoff)
- Two looks: flat light characters, or characters shaded by brightness
- Fast rendering using a pre-drawn glyph atlas and NumPy, with no per-frame text drawing

---

## How it works

```
input.mp4 ──┬── video frames ──► grayscale ──► shrink to character grid ──► brightness → character
            │                                                                        │
            │                                                          glyph atlas (pre-drawn tiles)
            │                                                                        │
            │                                                                        ▼
            │                                                           ASCII frame ──► fullscreen window
            │
            └── audio track ──► ffplay (background) ──► speakers
```

1. **Read** each frame with OpenCV.
2. **Grayscale + gamma**: each pixel becomes one brightness value (0–255), with an optional gamma curve to adjust midtones.
3. **Shrink** the frame so one pixel equals one character cell. The grid size is the output resolution divided by the font's cell size, so the aspect ratio is preserved.
4. **Map brightness to characters** using a ramp like `" .:-=!*#$@"` (empty → dense). Pixels below `SHADOW_CUTOFF` become empty cells for clean shadows.
5. **Render** using a glyph atlas: every character is drawn once at startup as a small tile, then NumPy picks and stitches thousands of tiles per frame in one operation.
6. **Play** frames on a clock based on the video's FPS, while `ffplay` plays the audio in the background.

---

## Requirements

| Requirement | Why it is needed |
|---|---|
| **Python 3.9+** (tested on 3.13) | Runs the program |
| **opencv-python** | Reads video frames and shows the window |
| **numpy** | Fast per-frame image math |
| **Pillow** | Draws the characters with a TrueType font |
| **FFmpeg (`ffplay`)** *(optional)* | Plays the audio. Without it the video still plays, just with no sound |
| **A monospace `.ttf` font** | Default is `consola.ttf` (Consolas), which comes with Windows |

The exact Python package versions tested are pinned in [`requirements.txt`](requirements.txt).

---

## Installation

### 1. Get the code

```bash
git clone https://github.com/dipvibe/ascii-video-generator.git
cd ascii-video-generator
```

### 2. Create a virtual environment (recommended)

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
> If PowerShell blocks the script, run this once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install the Python packages

```bash
pip install -r requirements.txt
```

> This installs `opencv-python`, **not** `opencv-python-headless`. The headless build cannot open windows and `cv2.imshow` will fail.

### 4. Install FFmpeg (for audio)

`ffplay` must be on your `PATH`.

- **Windows:** `winget install Gyan.FFmpeg`
  (or download from https://www.gyan.dev/ffmpeg/builds/, unzip it, and add its `bin` folder to `PATH`)
- **macOS:** `brew install ffmpeg`
- **Ubuntu / Debian:** `sudo apt install ffmpeg`

Close and reopen your terminal, then check it works:

```bash
ffplay -version
```

If you skip this step, the program prints `ffplay not found, no audio` and plays the video without sound.

### 5. Add a video

Video files are **not** stored in the repo (`*.mp4` is in `.gitignore`), so bring your own:

- Copy any video into the project folder and name it **`input.mp4`**, **or**
- Change `VIDEO_PATH` at the top of `main.py` to point to your file (for example `VIDEO_PATH = "C:/Videos/clip.mp4"`).

Any format OpenCV can read will work (`.mp4`, `.avi`, `.mov`, `.mkv`, ...). H.264 video is the safest choice (see [Troubleshooting](#troubleshooting) about AV1).

### 6. (macOS / Linux only) Set a font

`consola.ttf` only exists on Windows. On other systems, change `FONT_PATH` in `main.py` to a monospace font on your machine, for example:

```python
# Linux
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
# macOS
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
```

---

## Running the program

With the virtual environment active, from the project folder:

```bash
python main.py
```

What happens:

1. Video info and grid size are printed in the terminal.
2. A **fullscreen** window called **"ASCII Player"** opens and the video plays as ASCII art.
3. Audio starts at the same time (if `ffplay` is installed).
4. When the video ends (or you quit), a short performance report is printed.

---

## Controls

| Key | Action |
|---|---|
| `q` | Quit |
| `Esc` | Quit |

> The window must have focus for the keys to work. Click on it if a key does nothing.

---

## Configuration

All settings are at the top of [`main.py`](main.py). Edit them and run the program again.

| Setting | Default | Description |
|---|---|---|
| `VIDEO_PATH` | `"input.mp4"` | Path to the video to play |
| `RAMP` | `" .:-=!*#$@"` | Characters from darkest to brightest. Must contain a space `" "`. A longer 70-character ramp is included as a comment for finer detail |
| `INVERT` | `False` | Reverse the ramp (bright areas become sparse). Useful for dark text on a light background |
| `SHADE_MODE` | `"white"` | `"white"`: every character uses the same color (`FOREGROUND`). `"gray"`: each character is shaded by its brightness |
| `BACKGROUND` | `30` | Background gray level, `0` (black) to `255` (white) |
| `FOREGROUND` | `220` | Character color in `"white"` mode, `0`–`255` |
| `SHADOW_CUTOFF` | `60` | Pixels darker than this become empty cells. Raise it for a cleaner, less noisy image |
| `FONT_PATH` | `"consola.ttf"` | Path to a monospace TrueType font |
| `FONT_SIZE` | `10` | Font size in pixels. **Smaller = more characters = more detail, but slower** |
| `OUTPUT_WIDTH` | `1920` | Width of the output image in pixels. Height follows the video's aspect ratio. Set to `None` to use the video's own resolution |
| `GAMMA` | `1.0` | Midtone adjustment. `< 1` brightens, `> 1` darkens |
| `BRIGHTNESS` | `1.4` | Brightness boost in `"gray"` mode only |
| `PLAY_AUDIO` | `True` | Set to `False` to play without sound |
| `AV_SYNC_OFFSET` | `0.0` | Audio/video sync fix in seconds. Use a **positive** value if the sound is ahead of the picture, **negative** if it is behind |

### Example presets

**More detail (needs a faster PC):**
```python
FONT_SIZE = 6
RAMP = " .'`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
```

**Shaded look on a black background:**
```python
SHADE_MODE = "gray"
BACKGROUND = 0
BRIGHTNESS = 1.6
```

**Light background, dark characters:**
```python
INVERT = True
BACKGROUND = 235
FOREGROUND = 20
SHADOW_CUTOFF = 0
```

---

## Console output

When the program starts:

```
FPS          : 30.0
Resolution   : 1280 x 720
Frame count  : 900
Cell size    : 6 x 12 px
ASCII grid   : 320 x 90 chars
Output frame : 1920 x 1080 px
```

When it ends:

```
Avg processing : 8.52 ms
Max FPS        : 117.37
Frames shown   : 900
Played in      : 30.04 s (video 30.00 s)
```

- **Avg processing / Max FPS**: how fast your PC renders one ASCII frame. If `Max FPS` is lower than the video's FPS, playback will lag behind the audio. Increase `FONT_SIZE` or lower `OUTPUT_WIDTH` to fix this.
- **Played in vs video length**: these should be close. A big difference means the program could not keep up.

*(These are example numbers. Yours depend on your video, font and hardware.)*

---

## Tips

- **High-contrast videos look best**: silhouettes, strong lighting, black-and-white animation.
- **Too many characters in dark areas?** Raise `SHADOW_CUTOFF` (80–120) or `GAMMA` (1.3–1.6).
- **Want finer detail?** Lower `FONT_SIZE` to 8.
- **Different monitor?** Set `OUTPUT_WIDTH` to your screen width (2560 for 1440p, 3840 for 4K).
- **Use videos you have the right to use**, especially if you share the output publicly.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Error: could not open input.mp4` | The file is missing or the path is wrong. Check `VIDEO_PATH` and that you are running from the project folder |
| Video won't open or shows no frames (often YouTube downloads) | The file may use the AV1 codec, which OpenCV often can't decode on Windows. Re-download as H.264, or convert: `ffmpeg -i input.webm -c:v libx264 -c:a aac input.mp4` |
| `Error: invalid FPS` | The video file is broken or has no frame-rate info. Re-encode it: `ffmpeg -i broken.mp4 input.mp4` |
| `OSError: cannot open resource` | The font in `FONT_PATH` was not found. Use the full path to a `.ttf` file (see [step 6](#6-macos--linux-only-set-a-font)) |
| `ModuleNotFoundError: No module named 'cv2'` | Activate the virtual environment and run `pip install -r requirements.txt` |
| `cv2.error ... The function is not implemented` on `imshow` | You have `opencv-python-headless`. Run `pip uninstall opencv-python-headless` then `pip install -r requirements.txt` |
| `ffplay not found, no audio` | Install FFmpeg and make sure `ffplay` is on `PATH`, then restart the terminal |
| No sound, even though `ffplay` is installed | The video may have no audio track. Check with `ffprobe -v error -show_entries stream=codec_type -of csv=p=0 input.mp4`. It should list both `video` and `audio` |
| Audio and video are out of sync | Adjust `AV_SYNC_OFFSET` (e.g. `0.2` or `-0.2`) |
| Playback is slow / choppy | Increase `FONT_SIZE`, lower `OUTPUT_WIDTH` (e.g. `1280`), or use the short default `RAMP` |
| Image is too dark / too noisy | Lower `GAMMA` (e.g. `0.8`) to brighten, or raise `SHADOW_CUTOFF` to remove noise |
| Can't exit fullscreen | Click the window, then press `q` or `Esc` |

---

## Project structure

```
ascii-video-generator/
├── main.py            # the player
├── requirements.txt   # Python dependencies (pinned versions)
├── .gitignore         # ignores virtual environments and video/image files
├── LICENSE
└── README.md
```

---

## Roadmap

- [x] Read video frames
- [x] Grayscale + character grid
- [x] Brightness to character mapping
- [x] Fast rendering with a glyph atlas
- [x] Fullscreen playback with audio
- [ ] Export to `output.mp4` with audio
- [ ] Command-line arguments (input file, font size, output width)
- [ ] Edge-detection mode
- [ ] Webcam input

---

## Acknowledgements

Inspired by [ASCIIPlayer](https://github.com/Esser50K/ASCIIPlayer) by Esser50K.

---

## License

This project is licensed under the [MIT License](LICENSE).
