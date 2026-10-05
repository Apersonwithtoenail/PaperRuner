#!/bin/bash
# Re-encode a wallpaper to a super-light format for weak CPUs.
# Targets: 480x270 (or less), 15 fps, aggressive compression.

SRC="$1"
[ -z "$SRC" ] || [ ! -f "$SRC" ] && { echo "usage: $0 <video>"; exit 1; }
[[ "$SRC" == *".lite.mp4" ]] && exit 0

DST="${SRC%.*}.lite.mp4"
[ -f "$DST" ] && { echo "already optimized: $(basename "$DST")"; exit 0; }

W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$SRC")

# Target 480 wide, but never upscale
if [ "$W" -gt 480 ]; then
    SCALE="scale=480:-2"
else
    SCALE="scale=iw:ih"
fi

echo "→ $(basename "$SRC")  ${W}w  →  480w @ 15fps"

ffmpeg -y -i "$SRC" \
    -vf "$SCALE" \
    -r 15 \
    -c:v libx264 \
    -profile:v baseline \
    -level 3.0 \
    -preset veryfast \
    -crf 28 \
    -pix_fmt yuv420p \
    -g 30 \
    -an \
    -movflags +faststart \
    "$DST" \
    -loglevel error

if [ -f "$DST" ]; then
    echo "  ✅ $(du -h "$SRC" | cut -f1) → $(du -h "$DST" | cut -f1)"
else
    echo "  ❌ failed"
    exit 1
fi
