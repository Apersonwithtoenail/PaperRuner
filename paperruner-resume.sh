#!/bin/bash
CONF="$HOME/.config/paperruner.conf"
[ -f "$CONF" ] || { echo "no conf"; exit 0; }
get() { grep -E "^$1 *=" "$CONF" | tail -1 | sed "s/^$1 *= *//"; }
read W H < <(xdpyinfo | awk '/dimensions:/{print $2}' | tr 'x' ' ')
ENGINE="$(dirname "$0")/paperruner-engine.sh"
cleanup() { pkill -f xwinwrap 2>/dev/null; pkill -f "mpv.*-wid" 2>/dev/null; exit 0; }
trap cleanup TERM INT
while true; do
    WALL=$(get last_wallpaper)
    Q=$(get quality); Q=${Q:-auto}
    F=$(get fps);     F=${F:-native}
    [ -z "$WALL" ] || [ ! -f "$WALL" ] && { sleep 5; continue; }
    "$ENGINE" "$WALL" "$W" "$H" "$Q" "$F"
    sleep 2
    if pgrep -f "mpv.*-wid" >/dev/null 2>&1; then
        while pgrep -f "mpv.*-wid" >/dev/null 2>&1; do sleep 2; done
    else
        sleep 5
    fi
done
