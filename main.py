import shutil
import subprocess
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

#Settings
VIDEO_PATH = "add_your_video_here"
RAMP = " .:-=!*#$@"          # dark -> bright
# RAMP = " .'`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
INVERT = False               # flip the ramp
SHADE_MODE = "white"         # "white" = flat color, "gray" = shaded by brightness
BACKGROUND = 30              # background gray (0 = black)
FOREGROUND = 220             # character color in "white" mode
SHADOW_CUTOFF = 60           # darker than this = empty cell
FONT_PATH = "consola.ttf"
FONT_SIZE = 10
OUTPUT_WIDTH = 1920
GAMMA = 1.0                  # <1 brighter, >1 darker midtones
BRIGHTNESS = 1.4             # "gray" mode boost
PLAY_AUDIO = True
AV_SYNC_OFFSET = 0.0         # seconds; + if sound is ahead, - if behind
WINDOW_NAME = "ASCII Player"
START_FULLSCREEN = False     # F toggles fullscreen while playing
WINDOW_WIDTH = 1280          # starting window width
if INVERT:
    RAMP = RAMP[::-1]
space_index = RAMP.index(" ")

# Open video
cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print(f"Error: could not open {VIDEO_PATH}")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

if fps <= 0:
    print("Error: invalid FPS")
    exit()

print(f"FPS          : {fps}")
print(f"Resolution   : {width} x {height}")
print(f"Frame count  : {total_frames}")

#Glyph atlas
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

cell_w = int(round(font.getlength("@")))
ascent, descent = font.getmetrics()
cell_h = ascent + descent

atlas = np.zeros((len(RAMP), cell_h, cell_w), dtype=np.float32)
for i, ch in enumerate(RAMP):
    tile = Image.new("L", (cell_w, cell_h), color=0)
    ImageDraw.Draw(tile).text((0, 0), ch, fill=255, font=font)
    atlas[i] = np.array(tile, dtype=np.float32) / 255.0   # 0 = empty, 1 = ink

#Output size
if OUTPUT_WIDTH is None:
    out_w, out_h = width, height
else:
    out_w = OUTPUT_WIDTH
    out_h = int(round(OUTPUT_WIDTH * height / width))   # keep aspect ratio

cols = out_w // cell_w
rows = out_h // cell_h
ascii_w = cols * cell_w
ascii_h = rows * cell_h

# Center the grid if it doesn't fill the frame exactly
offset_x = (out_w - ascii_w) // 2
offset_y = (out_h - ascii_h) // 2

print(f"Cell size    : {cell_w} x {cell_h} px")
print(f"ASCII grid   : {cols} x {rows} chars")
print(f"Output frame : {out_w} x {out_h} px")

# Gamma lookup table
lookup = np.round(((np.arange(256) / 255.0) ** GAMMA) * 255).astype(np.uint8)

#Window (normal, resizable, starts at WINDOW_WIDTH)
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, WINDOW_WIDTH, int(WINDOW_WIDTH * out_h / out_w))

fullscreen = START_FULLSCREEN
if fullscreen:
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


def render_ascii(frame):
    """Frame -> ASCII frame (out_w x out_h, BGR)."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.LUT(gray, lookup)

    small_gray = cv2.resize(gray, (cols, rows), interpolation=cv2.INTER_AREA)

    indices = (small_gray.astype(np.int32) * (len(RAMP) - 1)) // 255
    indices[small_gray < SHADOW_CUTOFF] = space_index    # clean shadows

    tiles = atlas[indices]

    if SHADE_MODE == "gray":
        ink = np.clip(small_gray.astype(np.float32) * BRIGHTNESS, 0, 255)
        ink = ink[:, :, None, None]
    else:
        ink = float(FOREGROUND)

    cells = BACKGROUND + tiles * (ink - BACKGROUND)
    cells = np.clip(cells, 0, 255).astype(np.uint8)

    img = cells.transpose(0, 2, 1, 3).reshape(ascii_h, ascii_w)

    canvas = np.full((out_h, out_w), BACKGROUND, dtype=np.uint8)
    canvas[offset_y:offset_y + ascii_h, offset_x:offset_x + ascii_w] = img

    return cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)


def fit_to_window(img):
    """Scale img to the current window size, keeping aspect ratio."""
    _, _, win_w, win_h = cv2.getWindowImageRect(WINDOW_NAME)
    if win_w <= 0 or win_h <= 0:
        return img

    scale = min(win_w / out_w, win_h / out_h)
    new_w = max(1, int(out_w * scale))
    new_h = max(1, int(out_h * scale))

    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR   # sharper when shrinking
    resized = cv2.resize(img, (new_w, new_h), interpolation=interp)

    # Center on a background-colored canvas (letterbox)
    canvas = np.full((win_h, win_w, 3), BACKGROUND, dtype=np.uint8)
    x = (win_w - new_w) // 2
    y = (win_h - new_h) // 2
    canvas[y:y + new_h, x:x + new_w] = resized
    return canvas


def keep_window_ratio(last_size):
    """If the user resized the window, snap it back to the video's aspect ratio."""
    _, _, win_w, win_h = cv2.getWindowImageRect(WINDOW_NAME)
    if win_w <= 0 or win_h <= 0 or (win_w, win_h) == last_size:
        return last_size

    last_w, last_h = last_size

    # Follow whichever side the user changed more
    if abs(win_w - last_w) >= abs(win_h - last_h):
        new_w, new_h = win_w, round(win_w * out_h / out_w)
    else:
        new_w, new_h = round(win_h * out_w / out_h), win_h

    if (new_w, new_h) != (win_w, win_h):
        cv2.resizeWindow(WINDOW_NAME, new_w, new_h)

    return (new_w, new_h)


def start_audio(path):
    """Play audio with ffplay in the background."""
    if not shutil.which("ffplay"):
        print("ffplay not found, no audio")
        return None

    return subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        stdin=subprocess.DEVNULL,
    )


#Playback
frame_count = 0
total_processing_time = 0

audio = start_audio(VIDEO_PATH) if PLAY_AUDIO else None
playback_start = time.perf_counter() + AV_SYNC_OFFSET

last_size = (WINDOW_WIDTH, int(WINDOW_WIDTH * out_h / out_w))   # window size we last set

while True:
    start_time = time.perf_counter()

    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow(WINDOW_NAME, fit_to_window(render_ascii(frame)))

    total_processing_time += time.perf_counter() - start_time
    next_frame_time = playback_start + (frame_count + 1) / fps
    delay = max(1, int((next_frame_time - time.perf_counter()) * 1000))

    key = cv2.waitKey(delay) & 0xFF

    # Q or Esc to quit
    if key in (ord("q"), 27):
        break

    # F to toggle fullscreen
    if key == ord("f"):
        fullscreen = not fullscreen
        mode = cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, mode)
        if not fullscreen:
            cv2.resizeWindow(WINDOW_NAME, *last_size)   # back to the last window size

    # Window closed with the X button
    if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
        break

    # Keep the window at the video's aspect ratio while resizing
    if not fullscreen:
        last_size = keep_window_ratio(last_size)

    frame_count += 1

# Stop audio on exit
if audio is not None and audio.poll() is None:
    audio.terminate()

# Report
elapsed = time.perf_counter() - playback_start

if frame_count > 0:
    avg_time = total_processing_time / frame_count
    print(f"Avg processing : {avg_time * 1000:.2f} ms")
    print(f"Max FPS        : {1 / avg_time:.2f}")

print(f"Frames shown   : {frame_count}")
print(f"Played in      : {elapsed:.2f} s (video {total_frames / fps:.2f} s)")

cap.release()
cv2.destroyAllWindows()