from __future__ import annotations

import math
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

# Lightweight local story-to-video prototype.
# Edit STORY below, then run: python main.py

WIDTH, HEIGHT = 1280, 720
FPS = 24
OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)

STORY = [
    {
        "title": "THE LAST TRAIN",
        "caption": "At midnight, Dorian found a train that was not on any map.",
        "duration": 5,
        "scene": "station",
    },
    {
        "title": "NO PASSENGERS",
        "caption": "Every window was dark. Every door stood open.",
        "duration": 5,
        "scene": "platform",
    },
    {
        "title": "A VOICE IN THE FOG",
        "caption": "Then a voice behind him whispered, 'You are late.'",
        "duration": 6,
        "scene": "fog",
    },
]


def load_font(size: int, bold: bool = False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


FONT_TITLE = load_font(48, True)
FONT_CAPTION = load_font(30)
FONT_SMALL = load_font(20)


def lerp(a, b, t):
    return a + (b - a) * t


def draw_gradient(draw, top, bottom):
    for y in range(HEIGHT):
        t = y / max(1, HEIGHT - 1)
        color = tuple(int(lerp(top[i], bottom[i], t)) for i in range(3))
        draw.line((0, y, WIDTH, y), fill=color)


def draw_background(frame: Image.Image, scene: str, progress: float):
    draw = ImageDraw.Draw(frame)
    if scene == "station":
        draw_gradient(draw, (13, 20, 39), (76, 79, 101))
        horizon = 410
        draw.polygon([(0, horizon), (WIDTH, horizon), (WIDTH, HEIGHT), (0, HEIGHT)],
                     fill=(28, 31, 43))
        # Perspective platform lines
        for x in range(-300, WIDTH + 300, 180):
            draw.line((WIDTH // 2, horizon, x, HEIGHT), fill=(90, 93, 107), width=2)
        for y in (475, 535, 610, 690):
            draw.line((0, y, WIDTH, y), fill=(54, 57, 72), width=2)
        # Lamps
        for x in (170, 500, 850, 1130):
            draw.line((x, 100, x, 365), fill=(20, 22, 30), width=8)
            draw.ellipse((x - 23, 88, x + 23, 123), fill=(255, 221, 150))
            draw.ellipse((x - 55, 90, x + 55, 145), fill=(111, 104, 82))
    elif scene == "platform":
        draw_gradient(draw, (8, 13, 29), (53, 62, 79))
        draw.polygon([(0, 385), (WIDTH, 350), (WIDTH, HEIGHT), (0, HEIGHT)],
                     fill=(25, 29, 42))
        # Train silhouette with pseudo-perspective
        draw.polygon([(150, 215), (930, 185), (1120, 450), (130, 460)],
                     fill=(17, 21, 31))
        draw.line((170, 235, 930, 205), fill=(89, 102, 123), width=5)
        for x in (260, 420, 580, 740, 900):
            draw.polygon([(x, 255), (x + 105, 251), (x + 126, 370), (x - 5, 375)],
                         fill=(27, 39, 55), outline=(87, 104, 125))
        draw.line((0, 480, WIDTH, 455), fill=(120, 115, 100), width=4)
    else:
        draw_gradient(draw, (5, 8, 22), (35, 44, 63))
        # Fog bands
        for i in range(9):
            y = 250 + i * 45
            shift = int((progress * 90 + i * 70) % 180)
            x = shift - 90
            draw.ellipse((x, y, x + 620, y + 90), fill=(57, 66, 83))
            draw.ellipse((x + 390, y - 25, x + 980, y + 75), fill=(48, 58, 76))
        draw.polygon([(0, 480), (WIDTH, 460), (WIDTH, HEIGHT), (0, HEIGHT)],
                     fill=(18, 23, 35))


def draw_character(frame: Image.Image, progress: float, scene: str):
    draw = ImageDraw.Draw(frame)
    # A deliberately simple reusable silhouette character.
    x = int(WIDTH * (0.46 + 0.025 * math.sin(progress * math.pi)))
    y = 420
    scale = 1.0
    if scene == "fog":
        x = int(WIDTH * 0.58)
        scale = 0.82
    # Shadow
    draw.ellipse((x - 58, y + 165, x + 58, y + 185), fill=(10, 12, 20))
    # Legs
    draw.polygon([(x - 30, y + 105), (x - 5, y + 105),
                  (x - 17, y + 170), (x - 35, y + 170)], fill=(13, 15, 23))
    draw.polygon([(x + 5, y + 105), (x + 31, y + 105),
                  (x + 43, y + 168), (x + 22, y + 170)], fill=(13, 15, 23))
    # Coat
    draw.polygon([(x - 38, y + 8), (x + 38, y + 8), (x + 53, y + 115),
                  (x - 49, y + 115)], fill=(16, 19, 29), outline=(65, 72, 91))
    # Head and hood
    draw.ellipse((x - 31, y - 58, x + 31, y + 8), fill=(11, 13, 21))
    draw.arc((x - 34, y - 63, x + 34, y + 15), 180, 355, fill=(80, 87, 105), width=3)
    # Arms
    draw.line((x - 30, y + 25, x - 52, y + 91), fill=(17, 19, 29), width=17)
    draw.line((x + 30, y + 25, x + 53, y + 85), fill=(17, 19, 29), width=17)


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = word if not current else current + " " + word
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_text_overlay(frame, title, caption, progress):
    draw = ImageDraw.Draw(frame, "RGBA")
    # Soft dark caption panel
    panel_top = HEIGHT - 160
    draw.rounded_rectangle((70, panel_top, WIDTH - 70, HEIGHT - 35),
                           radius=18, fill=(4, 7, 15, 205),
                           outline=(130, 145, 170, 100), width=2)
    draw.text((100, panel_top + 14), title, font=FONT_TITLE, fill=(245, 238, 220, 255))
    lines = wrap_text(draw, caption, FONT_CAPTION, WIDTH - 210)
    for idx, line in enumerate(lines[:2]):
        draw.text((102, panel_top + 76 + idx * 37), line,
                  font=FONT_CAPTION, fill=(223, 229, 239, 255))
    # Progress bar
    bar_w = int((WIDTH - 140) * progress)
    draw.rounded_rectangle((70, HEIGHT - 18, WIDTH - 70, HEIGHT - 10),
                           radius=4, fill=(70, 75, 90, 190))
    draw.rounded_rectangle((70, HEIGHT - 18, 70 + bar_w, HEIGHT - 10),
                           radius=4, fill=(218, 183, 118, 255))


def render_story():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output_file = OUTPUT / "story.mp4"
    total_frames = sum(max(1, int(item["duration"] * FPS)) for item in STORY)

    command = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "ultrafast",
        "-crf", "23", "-pix_fmt", "yuv420p",
        str(output_file),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)

    frame_index = 0
    try:
        for item in STORY:
            scene_frames = max(1, int(item["duration"] * FPS))
            for local_index in range(scene_frames):
                progress = local_index / max(1, scene_frames - 1)
                global_progress = frame_index / max(1, total_frames - 1)
                frame = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
                draw_background(frame, item["scene"], progress)
                draw_character(frame, progress, item["scene"])
                draw_text_overlay(frame, item["title"], item["caption"], global_progress)
                process.stdin.write(frame.tobytes())
                frame_index += 1
                if frame_index % FPS == 0:
                    print(f"Rendered {frame_index}/{total_frames} frames...")
    finally:
        if process.stdin:
            process.stdin.close()

    code = process.wait()
    if code != 0:
        raise RuntimeError(f"FFmpeg failed with exit code {code}")
    print(f"\nDone! Video saved to: {output_file.resolve()}")


if __name__ == "__main__":
    render_story()
