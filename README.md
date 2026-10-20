# Story-to-Video Starter (Windows)

A lightweight, local Python prototype that turns a small scene list into an MP4.
It uses Pillow for drawing and `imageio-ffmpeg` to encode frames. No AI API is required.

## Requirements
- Windows 10/11
- Python 3.10+ recommended
- Internet only for the one-time package installation

## Setup
1. Extract this ZIP to a folder such as `C:\Users\YourName\Documents\story_to_video_starter`.
2. Open that folder in File Explorer.
3. Click the address bar, type `cmd`, and press Enter.
4. Create a virtual environment:

   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   python -m pip install --upgrade pip
   pip install Pillow imageio-ffmpeg
   ```

5. Run the program:

   ```bat
   python main.py
   ```

6. Find the video at `output\story.mp4`.

## Customize your story
Open `main.py` in VS Code or Notepad. Edit the `STORY` list near the top.
Each scene has:
- `title`: short scene heading
- `caption`: on-screen narration
- `duration`: seconds
- `scene`: `station`, `platform`, or `fog`

For now, keep the scene value one of those three names. New scene types can be added to `draw_background()`.

## What this prototype does
- Generates 1280x720, 24 FPS MP4
- Draws a stylized night environment, perspective lines, fog, a silhouette character, captions, and a progress bar
- Runs locally after installation

## Current limitations
- Narration audio and music are not included in this first prototype.
- The character is a simple silhouette, not a detailed rigged cartoon.
- Story-to-scene planning is manual through the `STORY` list.
- It uses 2D drawing and perspective tricks rather than a real 3D engine.

## Next upgrades
1. Read scenes from a separate JSON file.
2. Add WAV/MP3 narration and background music.
3. Add reusable character PNGs with transparent backgrounds.
4. Add camera pans, parallax layers, and more scene types.
5. Optionally add local text generation later; do not require it for the renderer.
