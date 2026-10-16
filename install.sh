#!/usr/bin/env bash
# install.sh — install PaperRuner to ~/.local/bin + app menu
set -e

APP_NAME="PaperRuner"
APP_ID="paperruner"
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/paperruner-app.py"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BIN="$HOME/.local/bin"
ICONS="$HOME/.local/share/icons/hicolor/scalable/apps"
APPS="$HOME/.local/share/applications"
mkdir -p "$BIN" "$ICONS" "$APPS"

[ -f "$SCRIPT" ] || { echo "❌ missing: $SCRIPT"; exit 1; }
chmod +x "$SCRIPT"

# 🔑 critical: remove any existing file/symlink FIRST, otherwise `cat >`
# follows a symlink and clobbers the real source file.
rm -f "$BIN/$APP_ID"

cat > "$BIN/$APP_ID" <<WRAP
#!/usr/bin/env bash
/usr/bin/python3 "$SCRIPT" "\$@"
WRAP
chmod +x "$BIN/$APP_ID"

# icon
cp "$(dirname "$SCRIPT")/assets/icon.svg" "$ICONS/$APP_ID.svg"

# .desktop
cat > "$APPS/$APP_ID.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=$APP_NAME
GenericName=Live Wallpaper
Comment=Lightweight live wallpaper manager for Linux/X11
Exec=$BIN/$APP_ID
Icon=$APP_ID
Terminal=false
Categories=Utility;Graphics;
Keywords=wallpaper;video;live;mpv;
DESKTOP

update-desktop-database "$APPS" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "✅ $APP_NAME installed"
echo "   Run from terminal:  $APP_ID"
echo "   Or search the app menu."
echo "   Uninstall:          ./uninstall.sh"

# ---------- systemd user service (auto-start + auto-restart) ----------
SVC_DIR="$HOME/.config/systemd/user"
SVC_FILE="$SVC_DIR/paperruner.service"
RESUME="$REPO_DIR/paperruner-resume.sh"

mkdir -p "$SVC_DIR"

cat > "$RESUME" <<'RESUME_EOF'
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
RESUME_EOF
chmod +x "$RESUME"

cat > "$SVC_FILE" <<SVC_EOF
[Unit]
Description=PaperRuner live wallpaper
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
Environment=DISPLAY=:0
ExecStart=$RESUME
Restart=on-failure
RestartSec=10
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=default.target
SVC_EOF

systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable paperruner.service 2>/dev/null || true
echo "systemd user service installed at $SVC_FILE"
echo "Start it with:  systemctl --user start paperruner"
