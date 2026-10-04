#!/bin/bash
rm -rf "$HOME/.local/share/paperruner"
rm -f  "$HOME/.local/bin/paperruner"
rm -f  "$HOME/.local/share/applications/paperruner.desktop"
rm -f  "$HOME/.config/paperruner.conf"
rm -rf "$HOME/.cache/paperruner"
pkill -f "xwinwrap.*mpv" 2>/dev/null
echo "PaperRuner uninstalled"
