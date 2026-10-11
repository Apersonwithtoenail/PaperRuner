#!/bin/bash
CONF="$HOME/.config/paperruner.conf"
[ -f "$CONF" ] || { echo "no conf"; exit 0; }
get() { grep -E "^$1 *=" "$CONF" | tail -1 | sed "s/^$1 *= *//"; }
read W H < <(xdpyinfo | awk '/dimensions:/{print $2}' | tr 'x' ' ')
ENGINE="$HOME/StudioProjects/livewall/paperruner-engine.sh"

cleanup() { pkill -f xwinwrap 2>/dev/null; pkill -f "mpv.*-wid" 2>/dev/null; exit 0; }
trap cleanup TERM INT

ROTATE_TICK=0
while true; do
    ROTATE=$(get rotate); ROTATE=${ROTATE:-0}
    INTERVAL=$(get interval); INTERVAL=${INTERVAL:-10}
    FOLDER=$(get folder)
    WALL=$(get last_wallpaper)
    Q=$(get quality); Q=${Q:-auto}
    F=$(get fps);     F=${F:-native}

    # ---- rotation: every INTERVAL minutes pick a random file from FOLDER ----
    if [ "$ROTATE" = "1" ] && [ -n "$FOLDER" ] && [ -d "$FOLDER" ]; then
        NOW=$(date +%s)
        if [ $(( NOW - ROTATE_TICK )) -ge $(( INTERVAL * 60 )) ]; then
            NEW=$(find "$FOLDER" -maxdepth 1 -type f \
                  \( -iname '*.mp4' -o -iname '*.webm' -o -iname '*.mkv' \
                  -o -iname '*.mov' -o -iname '*.avi' -o -iname '*.m4v' \
                  -o -iname '*.gif' \) | shuf -n 1)
            if [ -n "$NEW" ] && [ "$NEW" != "$WALL" ]; then
                echo "$(date +%H:%M:%S) rotate: $(basename "$NEW")"
                WALL="$NEW"
                # persist so a reboot keeps the current one
                sed -i "s|^last_wallpaper *=.*|last_wallpaper = $WALL|" "$CONF"
                ROTATE_TICK=$NOW
                pkill -f "mpv.*-wid" 2>/dev/null
                pkill -f "xwinwrap.*mpv" 2>/dev/null
                sleep 1
            elif [ -z "$ROTATE_TICK" ] || [ "$ROTATE_TICK" -eq 0 ]; then
                ROTATE_TICK=$NOW
            fi
        fi
    fi

    if [ -z "$WALL" ] || [ ! -f "$WALL" ]; then
        sleep 5
        continue
    fi

    "$ENGINE" "$WALL" "$W" "$H" "$Q" "$F"
    sleep 2

    if pgrep -f "mpv.*-wid" >/dev/null 2>&1; then
        # poll every 5s and check if rotation is due
        while pgrep -f "mpv.*-wid" >/dev/null 2>&1; do
            sleep 5
            ROTATE=$(get rotate); ROTATE=${ROTATE:-0}
            INTERVAL=$(get interval); INTERVAL=${INTERVAL:-10}
            [ "$ROTATE" = "1" ] || continue
            NOW=$(date +%s)
            if [ $(( NOW - ROTATE_TICK )) -ge $(( INTERVAL * 60 )) ]; then
                FOLDER=$(get folder)
                [ -d "$FOLDER" ] || continue
                NEW=$(find "$FOLDER" -maxdepth 1 -type f \
                      \( -iname '*.mp4' -o -iname '*.webm' -o -iname '*.mkv' \
                      -o -iname '*.mov' -o -iname '*.avi' -o -iname '*.m4v' \
                      -o -iname '*.gif' \) | shuf -n 1)
                if [ -n "$NEW" ] && [ "$NEW" != "$WALL" ]; then
                    echo "$(date +%H:%M:%S) rotate: $(basename "$NEW")"
                    sed -i "s|^last_wallpaper *=.*|last_wallpaper = $NEW|" "$CONF"
                    ROTATE_TICK=$NOW
                    pkill -f "mpv.*-wid" 2>/dev/null
                    pkill -f "xwinwrap.*mpv" 2>/dev/null
                    break
                fi
            fi
        done
    else
        sleep 5
    fi
done
