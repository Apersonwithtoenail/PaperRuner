#!/usr/bin/env bash
# uninstall.sh — remove PaperRuner
set -e

APP_NAME="PaperRuner"
APP_ID="paperruner"

rm -f "$HOME/.local/bin/paperruner"
rm -f "$HOME/.local/share/applications/$APP_ID.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/$APP_ID.svg"

update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
xfce4-panel -r 2>/dev/null || true

echo "✅ $APP_NAME removed"
