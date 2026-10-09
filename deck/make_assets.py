#!/usr/bin/env python3
"""Extract the poster frame for the embedded demo video."""

import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.join(ROOT, "video_2026-10-08_16-58-25.mp4")
POSTER = os.path.join(HERE, "assets", "demo-poster.png")

# 45 s is inside the application walkthrough: a full-bleed screen recording.
FRAME_AT = "45"

os.makedirs(os.path.dirname(POSTER), exist_ok=True)
subprocess.run(
    ["ffmpeg", "-v", "error", "-ss", FRAME_AT, "-i", VIDEO, "-frames:v", "1",
     "-y", POSTER],
    check=True,
)
print("poster:", POSTER, os.path.getsize(POSTER), "bytes")
