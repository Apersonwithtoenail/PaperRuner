# PaperRuner

**Lightweight live wallpaper manager for Linux/X11 — powered by xwinwrap + mpv.**

Hooks a full-screen mpv window into the desktop background layer and lets you apply, rotate, and shuffle video wallpapers from a simple GTK3 grid.

## Why PaperRuner

| App | Typical RAM |
|-----|-------------|
| Wallpaper Engine | ~500 MB |
| Lively Wallpaper | ~250 MB |
| **PaperRuner** | **~100 MB** |

## Features

- Plays `mp4`, `webm`, `mkv`, `mov`, `gif`, `png`, `jpg`, `webp`
- Auto-rotate every N minutes
- Thumbnail grid, click to apply
- Folder picker, random shuffle, one-click stop
- Quality profiles: auto / low / medium / high
- FPS limiter: native / 60 / 30 / 24 / 15 / 10
- Per-file `.lite.mp4` preference in low mode
- Automatic hardware detection (VAAPI, OpenGL, core count)
- Settings persist across launches

## Requirements

- Debian, Ubuntu, or Kali on **X11** (not Wayland)
- GTK 3, Python 3.9+
- `mpv`, `ffmpeg`, `xwinwrap` (auto-built by `install.sh`)
- Optional: `vainfo` for VAAPI hardware decode

## Install

    git clone https://github.com/Apersonwithtoenail/PaperRuner.git
    cd PaperRuner
    ./install.sh

Then launch from your app menu, or run:

    paperruner

Uninstall with `./uninstall.sh`.

## Usage

1. Drop wallpapers into `~/Videos/PaperRunerpapers/`
2. Launch PaperRuner
3. Click a thumbnail to apply
4. Enable Auto-Rotate to shuffle every N minutes

## Configuration

Settings live in `~/.config/paperruner.conf`.

Media folder override:

    export PAPERRUNER_DIR="$HOME/Pictures/wallpapers"
    paperruner

## Optimize heavy videos

    ./paperruner-optimize.sh ~/Videos/PaperRunerpapers/bigfile.mp4

Creates `bigfile.lite.mp4` — 480x270 @ 15 fps, CRF 28, baseline profile.

## Platform status

| Platform | Status |
|----------|--------|
| Linux (X11) | Tested |
| Linux (Wayland) | Not supported — needs X11 |
| macOS | Not supported |
| Windows | Not supported |

## License

MIT — see [LICENSE](LICENSE).
