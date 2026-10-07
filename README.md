# PaperRuner

**Lightweight live wallpaper manager for Linux/X11 — powered by xwinwrap + mpv.**

Hooks a full-screen mpv window into the desktop background layer and lets you apply, rotate, and shuffle video wallpapers from a simple GTK3 grid.

## Why

| App | RAM |
|-----|-----|
| Wallpaper Engine | ~500 MB |
| Lively Wallpaper | ~250 MB |
| **PaperRuner** | **~100 MB** |

## Features

- Plays mp4, webm, mkv, mov, gif, png, jpg, webp
- Auto-rotate every N minutes
- Thumbnail grid, click to apply
- Folder picker, random shuffle, one-click stop
- Settings persist across launches
- GTK3 native

## Requirements

- xwinwrap (auto-built by install.sh)
- mpv
- ffmpeg
- GTK 3, Python 3.9+
- python3-pil

## Install

    git clone https://github.com/Apersonwithtoenail/paperruner.git
    cd paperruner
    ./install.sh
    paperruner

## Usage

1. Drop wallpapers into ~/Videos/PaperRunerpapers/
2. Launch PaperRuner
3. Click a thumbnail to apply
4. Enable Auto-Rotate to shuffle every N minutes

## Configuration

Settings live in ~/.config/paperruner.conf

Media folder — default ~/Videos/PaperRunerpapers/. Override:

    export PAPERRUNER_DIR="$HOME/Pictures/wallpapers"
    paperruner

## Platform status

| Platform | Status |
|----------|--------|
| Linux (X11) | Tested |
| Linux (Wayland) | Not supported — needs X11 |
| macOS | Not supported |
| Windows | Not supported |

## Uninstall

    ./uninstall.sh

## License

MIT — see LICENSE.
