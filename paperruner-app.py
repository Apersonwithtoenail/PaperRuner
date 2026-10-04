#!/usr/bin/env python3
"""PaperRuner — lightweight live wallpaper manager for Linux."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

import os, sys, glob, subprocess, configparser, random

APP = "PaperRuner"
VER = "1.0"
WALL_DIR = os.environ.get("PAPERRUNER_DIR", os.path.expanduser("~/Videos/LiveWallpapers"))
CONF = os.path.expanduser("~/.config/paperruner.conf")
THUMB_DIR = os.path.expanduser("~/.cache/paperruner/thumbs")

VIDEO_EXTS = (".mp4", ".webm", ".mkv", ".mov", ".avi", ".m4v")
IMAGE_EXTS = (".gif", ".png", ".jpg", ".jpeg", ".webp")

CSS = b"""
window { background: #1e1e2e; }
.sidebar { background: #181825; }
label.title { color: #89b4fa; font-size: 18pt; font-weight: bold; }
label.sub { color: #a6adc8; font-size: 9pt; }
label.section { color: #f9e2af; font-size: 10pt; font-weight: bold; margin-top: 8px; }
label.status { color: #a6adc8; font-size: 9pt; margin: 6px; }
button.menu {
    background: #313244; color: #cdd6f4;
    border: none; border-radius: 8px;
    padding: 9px 14px; font-size: 11pt; margin: 3px 0;
}
button.menu:hover { background: #45475a; }
button.menu:active { background: #89b4fa; color: #1e1e2e; }
button.thumb {
    background: #313244; border: 2px solid transparent;
    border-radius: 8px; padding: 4px;
}
button.thumb:hover { border-color: #89b4fa; }
button.thumb-active { border: 3px solid #89b4fa; }
combobox button { background: #313244; color: #cdd6f4; border: none; border-radius: 6px; }
scale trough { background: #313244; border-radius: 4px; min-height: 6px; }
scale highlight { background: #89b4fa; border-radius: 4px; }
"""


def screen_size():
    try:
        out = subprocess.check_output(["xdpyinfo"], stderr=subprocess.DEVNULL).decode()
        for line in out.splitlines():
            if "dimensions:" in line:
                dim = line.split()[1]
                w, h = dim.split("x")
                return int(w), int(h)
    except Exception:
        pass
    return 1366, 768


def media_files():
    out = []
    for ext in VIDEO_EXTS + IMAGE_EXTS:
        out.extend(glob.glob(os.path.join(WALL_DIR, f"*{ext}")))
    return sorted(out)


def thumb_path(src):
    return os.path.join(THUMB_DIR, os.path.basename(src) + ".png")


def make_thumb(src):
    dst = thumb_path(src)
    if os.path.exists(dst):
        return dst
    os.makedirs(THUMB_DIR, exist_ok=True)
    ext = os.path.splitext(src)[1].lower()
    try:
        if ext in VIDEO_EXTS:
            subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", src,
                            "-vframes", "1", "-vf", "scale=200:-1", dst],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15)
        else:
            from PIL import Image
            with Image.open(src) as im:
                im.seek(0)
                im = im.convert("RGB")
                im.thumbnail((200, 120))
                im.save(dst, "PNG")
        return dst if os.path.exists(dst) else None
    except Exception as e:
        print("thumb fail:", src, e)
        return None


class App(Gtk.Window):
    def __init__(self):
        super().__init__(title=f"{APP} v{VER}")
        self.set_default_size(1100, 700)

        self.current = None
        self.rotate_timer = None
        self.rotate_on = False
        self.rotate_mins = 10
        self._load_conf()

        p = Gtk.CssProvider()
        p.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(root)

        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        side.get_style_context().add_class("sidebar")
        side.set_size_request(240, -1)
        side.set_margin_start(12); side.set_margin_end(12)
        side.set_margin_top(12); side.set_margin_bottom(12)
        root.pack_start(side, False, False, 0)

        t = Gtk.Label(label=f"🎬  {APP}")
        t.get_style_context().add_class("title")
        t.set_xalign(0)
        side.pack_start(t, False, False, 4)

        s = Gtk.Label(label="lightweight live wallpapers")
        s.get_style_context().add_class("sub")
        s.set_xalign(0)
        side.pack_start(s, False, False, 12)

        self.btn(side, "📁   Change Folder",  self.pick_folder)
        self.btn(side, "🔄   Refresh",        self.refresh)
        self.btn(side, "🎲   Random",          self.apply_random)
        self.btn(side, "⏹   Stop Wallpaper",  self.stop_wallpaper)

        lbl = Gtk.Label(label="🔁  Auto-Rotate")
        lbl.get_style_context().add_class("section")
        lbl.set_xalign(0)
        side.pack_start(lbl, False, False, 0)

        self.rotate_check = Gtk.CheckButton(label="Enable rotation")
        self.rotate_check.set_active(self.rotate_on)
        self.rotate_check.connect("toggled", self.on_rotate_toggle)
        side.pack_start(self.rotate_check, False, False, 2)

        interval_lbl = Gtk.Label(label="Interval (minutes)")
        interval_lbl.get_style_context().add_class("sub")
        interval_lbl.set_xalign(0)
        side.pack_start(interval_lbl, False, False, 0)

        self.interval_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 1, 60, 1)
        self.interval_scale.set_value(self.rotate_mins)
        self.interval_scale.set_draw_value(True)
        self.interval_scale.connect("value-changed", self.on_interval)
        side.pack_start(self.interval_scale, False, False, 0)

        side.pack_start(Gtk.Label(), False, False, 8)
        self.btn(side, "❌   Quit", Gtk.main_quit)

        self.status = Gtk.Label(label="Ready")
        self.status.get_style_context().add_class("status")
        self.status.set_xalign(0)
        self.status.set_line_wrap(True)
        side.pack_end(self.status, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.flow = Gtk.FlowBox()
        self.flow.set_valign(Gtk.Align.START)
        self.flow.set_max_children_per_line(6)
        self.flow.set_min_children_per_line(2)
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_homogeneous(True)
        self.flow.set_margin_top(12); self.flow.set_margin_bottom(12)
        self.flow.set_margin_start(12); self.flow.set_margin_end(12)
        self.flow.set_row_spacing(12)
        self.flow.set_column_spacing(12)

        scroll.add(self.flow)
        root.pack_start(scroll, True, True, 0)

        self.connect("destroy", self.on_destroy)
        self.show_all()
        GLib.idle_add(self.refresh)

    def btn(self, parent, text, cb):
        b = Gtk.Button(label=text)
        b.get_style_context().add_class("menu")
        b.set_relief(Gtk.ReliefStyle.NONE)
        b.set_can_focus(False)
        b.connect("clicked", lambda *_: cb())
        parent.pack_start(b, False, False, 0)

    def set_status(self, text):
        self.status.set_text(text)

    def _load_conf(self):
        c = configparser.ConfigParser()
        try:
            c.read(CONF)
            if "main" in c:
                self.rotate_on = c["main"].getboolean("rotate", False)
                self.rotate_mins = c["main"].getint("interval", 10)
        except Exception:
            pass

    def _save_conf(self):
        c = configparser.ConfigParser()
        c["main"] = {
            "rotate": "1" if self.rotate_on else "0",
            "interval": str(self.rotate_mins),
        }
        try:
            os.makedirs(os.path.dirname(CONF), exist_ok=True)
            with open(CONF, "w") as f:
                c.write(f)
        except Exception:
            pass

    def refresh(self):
        for child in self.flow.get_children():
            self.flow.remove(child)
        files = media_files()
        if not files:
            lbl = Gtk.Label(label=f"No wallpapers in\n{WALL_DIR}")
            lbl.set_justify(Gtk.Justification.CENTER)
            self.flow.add(lbl)
            self.flow.show_all()
            self.set_status(f"📂  {WALL_DIR}\nEmpty — add mp4/webm/gif files")
            return
        for f in files:
            self.flow.add(self.make_tile(f))
        self.flow.show_all()
        self.set_status(f"📂  {WALL_DIR}\n{len(files)} wallpaper(s)")

    def make_tile(self, path):
        btn = Gtk.Button()
        btn.get_style_context().add_class("thumb")
        if self.current == path:
            btn.get_style_context().add_class("thumb-active")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        img = Gtk.Image()
        thumb = make_thumb(path)
        if thumb and os.path.exists(thumb):
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(thumb, 180, 110, True)
                img.set_from_pixbuf(pb)
            except Exception:
                img.set_from_icon_name("video-x-generic", Gtk.IconSize.DIALOG)
        else:
            img.set_from_icon_name("video-x-generic", Gtk.IconSize.DIALOG)
        box.pack_start(img, False, False, 0)
        name = os.path.basename(path)
        if len(name) > 24:
            name = name[:21] + "..."
        lbl = Gtk.Label(label=name)
        lbl.set_max_width_chars(22)
        box.pack_start(lbl, False, False, 0)
        btn.add(box)
        btn.connect("clicked", lambda *_: self.apply(path))
        return btn

    def apply(self, path):
        if not os.path.exists(path):
            self.set_status(f"❌  Missing: {path}")
            return
        self.current = path
        self._launch(path)
        self.set_status(f"▶  {os.path.basename(path)}")
        self.refresh()

    def _launch(self, path):
        subprocess.run(["pkill", "-f", "xwinwrap.*mpv"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import time
        time.sleep(0.3)
        w, h = screen_size()
        engine = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "paperruner-engine.sh")
        subprocess.Popen([engine, path, str(w), str(h)],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

    def apply_random(self):
        files = media_files()
        if not files:
            self.set_status("❌  No wallpapers")
            return
        self.apply(random.choice(files))

    def stop_wallpaper(self):
        subprocess.run(["pkill", "-f", "xwinwrap.*mpv"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.current = None
        self.set_status("⏹  Stopped")
        self.refresh()

    def pick_folder(self):
        global WALL_DIR
        d = Gtk.FileChooserDialog(
            title="Pick wallpaper folder", transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER)
        d.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
                      "Select", Gtk.ResponseType.OK)
        if os.path.isdir(WALL_DIR):
            d.set_current_folder(WALL_DIR)
        if d.run() == Gtk.ResponseType.OK:
            WALL_DIR = d.get_filename()
            self.set_status(f"📂  {WALL_DIR}")
            self.refresh()
        d.destroy()

    def on_rotate_toggle(self, btn):
        self.rotate_on = btn.get_active()
        self._save_conf()
        if self.rotate_on:
            self._start_rotate()
        else:
            self._stop_rotate()

    def on_interval(self, scale):
        self.rotate_mins = int(scale.get_value())
        self._save_conf()
        if self.rotate_on:
            self._stop_rotate()
            self._start_rotate()

    def _start_rotate(self):
        if self.rotate_timer:
            GLib.source_remove(self.rotate_timer)
        ms = self.rotate_mins * 60 * 1000
        self.rotate_timer = GLib.timeout_add(ms, self._rotate_tick)
        self.set_status(f"🔁  Rotating every {self.rotate_mins} min")

    def _stop_rotate(self):
        if self.rotate_timer:
            GLib.source_remove(self.rotate_timer)
            self.rotate_timer = None
        self.set_status("⏹  Rotation off")

    def _rotate_tick(self):
        self.apply_random()
        return True

    def on_destroy(self, *_):
        Gtk.main_quit()


if __name__ == "__main__":
    if not os.path.isdir(WALL_DIR):
        os.makedirs(WALL_DIR, exist_ok=True)
    if subprocess.run(["which", "xwinwrap"],
                      stdout=subprocess.DEVNULL).returncode != 0:
        print("xwinwrap not found. Install it via ./install.sh")
        sys.exit(1)
    win = App()
    Gtk.main()
