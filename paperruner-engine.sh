#!/bin/bash
# PaperRuner engine — xwinwrap + mpv launcher

WALLPAPER="$1"
SCREEN_W="${2:-$(xdpyinfo | awk '/dimensions:/ {print $2}' | cut -dx -f1)}"
SCREEN_H="${3:-$(xdpyinfo | awk '/dimensions:/ {print $2}' | cut -dx -f2)}"

if [ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ]; then
    echo "usage: paperruner-engine.sh <file> [width] [height]"
    exit 1
fi

# Kill old
pkill -f "xwinwrap.*mpv" 2>/dev/null
sleep 0.3

# Launch
xwinwrap -g "${SCREEN_W}x${SCREEN_H}" -ni -s -nf -b -un -argb -fdt -- \
    mpv -wid WID --loop --no-audio --no-osc --no-input-default-bindings \
        --really-quiet --no-border --panscan=1.0 "$WALLPAPER" \
    > /dev/null 2>&1 &

sleep 0.5
echo "▶  playing: $(basename "$WALLPAPER")"
