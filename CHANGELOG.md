# Changelog

## v1.0.2 — 2026-10-11

### Fixed
- Rotation only ran while the GUI was open (GLib timer died on close).
  Now handled by the systemd service — keeps rotating with the GUI closed.

### Changed
- GUI rotate checkbox + interval slider are now pure conf writers.
  The service reads ~/.config/paperruner.conf every 5s and does the swap.
- paperruner-resume.sh now polls for rotation due-time alongside mpv liveness.
- Rotation updates last_wallpaper in conf so a reboot resumes the current one.


## v1.0.1 — 2026-10-11

### Added
- systemd user service for auto-start + auto-restart (survives crashes, resumes on login)
- paperruner-resume.sh: keep-alive wrapper that re-reads conf each loop
- install.sh now installs and enables the systemd service

### Fixed
- GUI now persists wallpaper folder and last-played file to ~/.config/paperruner.conf
- Folder picker was writing to a local variable instead of the module global
- Engine picks vo=gpu + gpu-context=x11egl when OpenGL is available (was stuck on x11)
- GIFs play cleanly via GPU compositing instead of failing with exit 4

### Changed
- GUI apply() now kills the running mpv instead of restarting the whole service
  (switch time dropped from 5–8s to ~2s). 1.5s debounce on rapid clicks.


## [1.0.0] — 2026-10-10
### Added
- `install.sh` / `uninstall.sh` for one-command desktop integration
- `assets/icon.svg` for app-menu icons
- Skip VAAPI decode for files under 2 MB (avoids green-screen corruption)

### Fixed
- Duplicate demuxer args silently overriding tuned values
- `pgrep` pattern that made the engine think mpv had died
- Rotation state not re-armed on relaunch
