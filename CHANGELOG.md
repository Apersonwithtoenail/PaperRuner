# Changelog

## [1.0.0] — 2026-10-10
### Added
- `install.sh` / `uninstall.sh` for one-command desktop integration
- `assets/icon.svg` for app-menu icons
- Skip VAAPI decode for files under 2 MB (avoids green-screen corruption)

### Fixed
- Duplicate demuxer args silently overriding tuned values
- `pgrep` pattern that made the engine think mpv had died
- Rotation state not re-armed on relaunch
