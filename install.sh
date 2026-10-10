#!/usr/bin/env bash
# install.sh — install PaperRuner to ~/.local/bin + app menu
set -e

APP_NAME="PaperRuner"
APP_ID="paperruner"
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/paperruner-app.py"

BIN="$HOME/.local/bin"
ICONS="$HOME/.local/share/icons/hicolor/scalable/apps"
APPS="$HOME/.local/share/applications"
mkdir -p "$BIN" "$ICONS" "$APPS"

[ -f "$SCRIPT" ] || { echo "❌ missing: $SCRIPT"; exit 1; }
chmod +x "$SCRIPT"

# wrapper script — pins /usr/bin/python3 so a stray venv can't break it
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

# refresh
update-desktop-database "$APPS" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "✅ $APP_NAME installed"
echo "   Run from terminal:  $APP_ID"
echo "   Or search the app menu."
echo "   Uninstall:          ./uninstall.sh"
