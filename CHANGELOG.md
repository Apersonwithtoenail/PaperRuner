# Changelog

## [1.0.0] — 2026-10-05

### Added — First public release

**Engine**
- Automatic hardware detection: core count, VAAPI, OpenGL context
- Quality profiles: auto / low / medium / high
- FPS limiter: native / 60 / 30 / 24 / 15 / 10
- Fallback render path when EGL/gpu VO fails (x11 fallback)
- `.lite.mp4` preference in low-quality mode for weak CPUs
- Per-file hwdec decision — skips VAAPI decode for files under 2 MB

**GUI**
- GTK3 window with thumbnail grid
- Folder picker, random wallpaper, stop button
- Quality and FPS dropdowns applied live to the running wallpaper
- Auto-rotation timer (1–60 minutes)
- Status bar with live feedback on every action
- Config persistence at `~/.config/paperruner.conf`

**Tooling**
- `paperruner-optimize.sh` — ffmpeg re-encoder for weak CPUs
- `install.sh` / `uninstall.sh` for system-wide install

### Fixed
- Duplicate mpv args silently overwriting tuned demuxer values
- Wrong `pgrep` pattern that made the engine think mpv had died
- Rotation state not re-armed when the app was relaunched
- Green-screen and block corruption on small highly-compressed files
- Frame-drop artifacts on loop seek (`--framedrop=vo` → `--framedrop=decoder`)

### Notes
- Requires X11 (not Wayland)
- Tested on Kali Linux with 2 cores + VAAPI H.264
