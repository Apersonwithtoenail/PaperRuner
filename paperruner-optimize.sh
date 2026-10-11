#!/bin/bash
# paperruner-optimize.sh <file> [width] [fps] [crf] [preset] [lowprio] [pause]
#   width   = 0 → auto (screen)
#   lowprio = 1 → nice -n 19 + ionice -c 3
#   pause   = 1 → stop paperruner during encode
set -e
SRC="$1"
[ -z "$SRC" ] || [ ! -f "$SRC" ] && { echo "usage: $0 <file> [w] [fps] [crf] [preset] [lowprio] [pause]"; exit 1; }
case "${SRC,,}" in *.lite.mp4) echo "already a .lite.mp4"; exit 0;; esac

W="${2:-0}"
if [ "$W" = "0" ] || [ -z "$W" ]; then
    W=$(xdpyinfo 2>/dev/null | awk '/dimensions:/{print $2}' | cut -dx -f1)
    W="${W:-1366}"
fi
FPS="${3:-24}"
CRF="${4:-26}"
XPRESET="${5:-ultrafast}"
LOWPRIO="${6:-1}"
PAUSE="${7:-1}"

OUT="${SRC%.*}.lite.mp4"
CORES=$(nproc 2>/dev/null || echo 2)
THREADS=$(( CORES > 2 ? CORES - 1 : 1 ))

PAUSED=0
if [ "$PAUSE" = "1" ] && systemctl --user is-active paperruner.service >/dev/null 2>&1; then
    systemctl --user stop paperruner.service >/dev/null 2>&1 && PAUSED=1
fi
trap '[ "$PAUSED" = "1" ] && systemctl --user start paperruner.service >/dev/null 2>&1' EXIT

echo "OPT_CFG: ${W}px @ ${FPS}fps crf=$CRF preset=$XPRESET threads=$THREADS lowprio=$LOWPRIO"

CMD=(ffmpeg -hide_banner -loglevel warning -stats -y -i "$SRC"
     -vf "scale=${W}:-2:flags=fast_bilinear,fps=${FPS}"
     -c:v libx264 -preset "$XPRESET" -crf "$CRF" -pix_fmt yuv420p
     -threads "$THREADS" -movflags +faststart -an "$OUT")

if [ "$LOWPRIO" = "1" ]; then
    nice -n 19 ionice -c 3 "${CMD[@]}" 2>&1
else
    "${CMD[@]}" 2>&1
fi

echo "DONE:$OUT"
ls -lh "$OUT" | awk '{print "SIZE:" $5}'
