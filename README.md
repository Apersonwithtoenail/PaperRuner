# PaperRuner

Lightweight live wallpaper manager for Linux. Powered by xwinwrap + mpv.

## Why

Wallpaper Engine: ~500 MB RAM, GPU heavy.
Lively Wallpaper: ~250 MB.
**PaperRuner: ~100 MB, minimal GPU.**

Uses xwinwrap to hook an mpv window directly into the desktop background layer.

## Features

- Plays mp4, webm, mkv, mov, gif, png, jpg, webp
- Auto-rotate every N minutes
- Thumbnail grid, click to apply
- Folder picker, random shuffle, one-click stop
- Settings persist across launches
- GTK3 native

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

## Media folder

Default: ~/Videos/PaperRunerpapers/. Override:

    export PAPERRUNER_DIR="$HOME/Pictures/wallpapers"
    paperruner

## Configuration

Settings live in ~/.config/paperruner.conf

## Requirements

- xwinwrap (auto-built by install.sh)
- mpv
- ffmpeg
- GTK 3, Python 3.9+
- python3-pil

## Uninstall

    ./uninstall.sh

## Platform status

| Platform | Status |
|---|---|
| Linux (X11) | Tested |
| Linux (Wayland) | Not supported - needs X11 |
| macOS | Not supported |
| Windows | Not supported |

## License

MIT
