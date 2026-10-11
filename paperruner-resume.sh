#!/bin/bash
CONF="$HOME/.config/paperruner.conf"
[ -f "$CONF" ] || { echo "no conf"; exit 0; }
get() { grep -E "^$1 *=" "$CONF" | tail -1 | sed "s/^$1 *= *//"; }
read W H < <(xdpyinfo | awk '/dimensions:/{print $2}' | tr 'x' ' ')
ENGINE="$HOME/StudioProjects/livewall/paperruner-engine.sh"

cleanup() { pkill -f xwinwrap 2>/dev/null; pkill -f "mpv.*-wid" 2>/dev/null; exit 0; }
trap cleanup TERM INT

while true; do
    WALL=$(get last_wallpaper)
    Q=$(get quality); Q=${Q:-auto}
    F=$(get fps);     F=${F:-native}

    if [ -z "$WALL" ] || [ ! -f "$WALL" ]; then
        sleep 5
        continue
    fi

    echo "resume: launching $WALL @ ${W}x${H} q=$Q fps=$F"
    "$ENGINE" "$WALL" "$W" "$H" "$Q" "$F"
    sleep 2

    if pgrep -f "mpv.*-wid" >/dev/null 2>&1; then
        # fast poll so a GUI kill is noticed within ~2s
        while pgrep -f "mpv.*-wid" >/dev/null 2>&1; do sleep 2; done
        echo "$(date +%H:%M:%S) mpv died, relaunching from conf"
    else
        echo "$(date +%H:%M:%S) mpv failed to start, retry in 5s"
        sleep 5
    fi
done
