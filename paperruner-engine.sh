#!/bin/bash
# PaperRuner engine — auto-detects hardware, picks optimal mpv settings.
#
# Args:
#   $1  wallpaper file
#   $2  screen width
#   $3  screen height
#   $4  quality: auto | low | medium | high   (default: auto)
#   $5  fps: native | 60 | 30 | 24 | 15 | 10  (default: native)

WALLPAPER="$1"
SCREEN_W="${2:-1366}"
SCREEN_H="${3:-768}"
QUALITY="${4:-auto}"
FPS="${5:-native}"

[ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ] && exit 1

# Only fall back to .lite.mp4 when quality=low, or when the original is missing.
# Otherwise use the real file — that's what makes quality settings actually matter.
LITE="${WALLPAPER%.*}.lite.mp4"
if [ "$QUALITY" = "low" ] && [ -f "$LITE" ]; then
    WALLPAPER="$LITE"
fi

LOG=/tmp/paperruner-engine.log
: > "$LOG"

pkill -f "xwinwrap.*mpv" 2>/dev/null
pkill -f "mpv.*-wid" 2>/dev/null
sleep 0.3

# ---------- Hardware detection ----------
CORES=$(nproc 2>/dev/null || echo 2)
[ "$CORES" -lt 1 ] && CORES=1

# VAAPI available? Use auto-safe (falls back to software on bad streams).
# Skip hardware decode entirely for tiny files — VAAPI corrupts heavily
# compressed baseline-profile H.264. CPU handles <2MB files easily.
HW="auto-safe"
FILE_BYTES=$(stat -c %s "$WALLPAPER" 2>/dev/null || echo 0)
if [ "$FILE_BYTES" -lt 2000000 ]; then
    HW="no"
fi
if ! command -v vainfo >/dev/null 2>&1; then
    HW="no"
elif ! vainfo 2>/dev/null | grep -qE "VAProfileH264|VAProfileVP8|VAProfileVP9"; then
    HW="no"
fi

VO="gpu"
GPU_CTX="x11egl"
if ! glxinfo -B 2>/dev/null | grep -qi "OpenGL"; then
    VO="x11"
    GPU_CTX=""
fi

# ---------- Quality profile ----------
EXTRA_ARGS=""
VF=""

case "$QUALITY" in
    low)
        DECODE_THREADS=1
        DEMUX_MB=2
        BACK_MB=0
        READAHEAD=0.3
        if [ "$HW" = "no" ]; then
            # Only skip decoding work when we have no GPU decode to lean on
            EXTRA_ARGS="--vd-lavc-skiploopfilter=all --vd-lavc-skipidct=nonref --vd-lavc-fast --video-sync=display-desync"
        fi
        ;;
    medium)
        DECODE_THREADS=2
        DEMUX_MB=8
        BACK_MB=2
        READAHEAD=1
        ;;
    high)
        DECODE_THREADS=$CORES
        DEMUX_MB=32
        BACK_MB=8
        READAHEAD=2
        ;;
    auto|*)
        if [ "$HW" != "no" ]; then
            # Hardware decode available — no CPU-saving hacks needed
            DECODE_THREADS=$CORES
            DEMUX_MB=16
            BACK_MB=4
            READAHEAD=1
        elif [ "$CORES" -le 2 ]; then
            DECODE_THREADS=1
            DEMUX_MB=4
            BACK_MB=1
            READAHEAD=0.5
            EXTRA_ARGS="--vd-lavc-skiploopfilter=all --vd-lavc-skipidct=nonref --vd-lavc-fast --video-sync=display-desync"
        else
            DECODE_THREADS=$CORES
            DEMUX_MB=16
            BACK_MB=4
            READAHEAD=1
        fi
        ;;
esac

cat << INFO | tee -a "$LOG"
[engine] hardware:
  cores: $CORES
  hwdec: $HW
  vo:    $VO
  quality: $QUALITY
  fps: $FPS
  file: $(basename "$WALLPAPER")
[engine] tuned:
  threads: $DECODE_THREADS
  demux: ${DEMUX_MB}M fwd / ${BACK_MB}M back
  readahead: ${READAHEAD}s
  filter: ${VF:-(none)}
  extras: ${EXTRA_ARGS:-(none)}
INFO

# ---------- FPS filter ----------
FPS_FILTER=""
if [ "$FPS" != "native" ] && [ -n "$FPS" ]; then
    FPS_FILTER="fps=$FPS"
fi
if [ -n "$FPS_FILTER" ] && [ -n "$VF" ]; then
    VF="$FPS_FILTER,$VF"
elif [ -n "$FPS_FILTER" ]; then
    VF="$FPS_FILTER"
fi

# ---------- Launch ----------
MPV_ARGS=(
    -wid WID
    --loop
    --no-audio
    --no-osc
    --no-osd-bar
    --no-input-default-bindings
    --no-border
    --really-quiet
    --no-config
    --panscan=1.0
    --hwdec="$HW"
    --vo="$VO"
    --profile=fast
    --cache=no
    --demuxer-max-back-bytes="${BACK_MB}M"
    --demuxer-max-bytes="${DEMUX_MB}M"
    --demuxer-readahead-secs="$READAHEAD"
    --vd-queue-enable=no
    --ao=null
    --vd-lavc-threads="$DECODE_THREADS"
    --framedrop=decoder
    --hwdec-extra-frames=16
)
[ -n "$GPU_CTX" ] && MPV_ARGS+=( --gpu-context="$GPU_CTX" )
# shellcheck disable=SC2206
[ -n "$EXTRA_ARGS" ] && MPV_ARGS+=($EXTRA_ARGS)
[ -n "$VF" ] && MPV_ARGS+=( --vf="$VF" )
MPV_ARGS+=( "$WALLPAPER" )

nohup xwinwrap -g "${SCREEN_W}x${SCREEN_H}" -ni -s -nf -b -un -argb -fdt -- \
    mpv "${MPV_ARGS[@]}" >> "$LOG" 2>&1 &
sleep 1.5

if pgrep -f "mpv.*-wid" >/dev/null; then
    echo "[engine] ✅ mpv running"
    exit 0
fi

echo "[engine] ⚠ primary VO failed, trying fallback x11"
tail -5 "$LOG"
pkill -f "xwinwrap.*mpv" 2>/dev/null
sleep 0.3

MPV_ARGS=(
    -wid WID --loop --no-audio --no-osc --no-osd-bar
    --no-input-default-bindings --no-border --really-quiet
    --no-config --panscan=1.0 --hwdec="$HW" --vo=x11
    --cache=no
    --demuxer-max-back-bytes="${BACK_MB}M"
    --demuxer-max-bytes="${DEMUX_MB}M"
    --demuxer-readahead-secs="$READAHEAD"
    --vd-queue-enable=no --ao=null 
    --vd-lavc-threads="$DECODE_THREADS" --framedrop=decoder
)
[ -n "$VF" ] && MPV_ARGS+=( --vf="$VF" )
MPV_ARGS+=( "$WALLPAPER" )

nohup xwinwrap -g "${SCREEN_W}x${SCREEN_H}" -ni -s -nf -b -un -argb -fdt -- \
    mpv "${MPV_ARGS[@]}" >> "$LOG" 2>&1 &

sleep 1.5
if pgrep -f "mpv.*-wid" >/dev/null; then
    echo "[engine] ✅ fallback ok"
else
    echo "[engine] ❌ mpv still failing — full log:"
    cat "$LOG"
    exit 1
fi
