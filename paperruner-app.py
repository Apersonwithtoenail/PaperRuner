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
window {
    background: #0f0f14;
}
.topbar {
    background: #1a1a24;
    border-bottom: 1px solid #2a2a38;
    padding: 12px 18px;
}
label.brand {
    color: #ff8c42;
    font-size: 20pt;
    font-weight: bold;
}
label.brandsub {
    color: #7a7a8c;
    font-size: 9pt;
    margin-top: -4px;
}
label.section {
    color: #ff8c42;
    font-size: 10pt;
    font-weight: bold;
}
label.status {
    color: #7a7a8c;
    font-size: 9pt;
}
button.menu {
    background: #22222e;
    color: #e8e8f0;
    border: 1px solid #2a2a38;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 10pt;
    font-weight: bold;
    margin: 2px;
    transition: all 0.15s;
}
button.menu:hover {
    background: #2a2a38;
    border-color: #ff8c42;
}
button.menu:active {
    background: #ff8c42;
    color: #0f0f14;
}
button.primary {
    background: #ff8c42;
    color: #0f0f14;
    border: 1px solid #ff8c42;
}
button.primary:hover {
    background: #ff9d5c;
}
button.thumb {
    background: #1a1a24;
    border: 2px solid #22222e;
    border-radius: 12px;
    padding: 6px;
}
button.thumb:hover {
    border-color: #ff8c42;
    background: #22222e;
}
button.thumb-active {
    border: 3px solid #ff8c42;
    background: #2a1a10;
}
scale trough {
    background: #22222e;
    border-radius: 4px;
    min-height: 8px;
}
scale highlight {
    background: #ff8c42;
    border-radius: 4px;
}
checkbutton {
    color: #e8e8f0;
}
combobox button {
    background: #22222e;
    color: #e8e8f0;
    border: 1px solid #2a2a38;
    border-radius: 6px;
    padding: 4px 10px;
}
combobox button:hover {
    border-color: #ff8c42;
}
combobox window.popup,
combobox popup,
combobox menu {
    background: #22222e;
}
combobox cellview {
    background: #22222e;
    color: #e8e8f0;
    padding: 6px;
}
combobox cellview:selected,
combobox cellview:hover {
    background: #ff8c42;
    color: #0f0f14;
}
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
        self.quality = "auto"
        self.fps = "native"
        self._load_conf()

        p = Gtk.CssProvider()
        p.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # ---------- TOP BAR ----------
        topbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        topbar.get_style_context().add_class("topbar")
        topbar.set_margin_start(0); topbar.set_margin_end(0)
        root.pack_start(topbar, False, False, 0)

        # Brand
        brand_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        brand_lbl = Gtk.Label(label="🎬  PaperRuner")
        brand_lbl.get_style_context().add_class("brand")
        brand_lbl.set_xalign(0)
        brand_box.pack_start(brand_lbl, False, False, 0)
        brand_sub = Gtk.Label(label="lightweight live wallpapers")
        brand_sub.get_style_context().add_class("brandsub")
        brand_sub.set_xalign(0)
        brand_box.pack_start(brand_sub, False, False, 0)
        topbar.pack_start(brand_box, False, False, 0)

        topbar.pack_start(Gtk.Box(), True, True, 0)  # spacer

        self.btn(topbar, "📁  Folder",  self.pick_folder)
        self.btn(topbar, "🔄  Refresh", self.refresh)
        self.btn(topbar, "🎲  Random",  self.apply_random, primary=True)
        self.btn(topbar, "⏹  Stop",     self.stop_wallpaper)
        self.btn(topbar, "❌  Quit",    Gtk.main_quit)

        # ---------- MAIN AREA ----------
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.pack_start(main, True, True, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.flow = Gtk.FlowBox()
        self.flow.set_valign(Gtk.Align.START)
        self.flow.set_max_children_per_line(8)
        self.flow.set_min_children_per_line(2)
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_homogeneous(True)
        self.flow.set_margin_top(18); self.flow.set_margin_bottom(18)
        self.flow.set_margin_start(18); self.flow.set_margin_end(18)
        self.flow.set_row_spacing(16)
        self.flow.set_column_spacing(16)

        scroll.add(self.flow)
        main.pack_start(scroll, True, True, 0)

        # ---------- BOTTOM CONTROL BAR ----------
        botbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        botbar.get_style_context().add_class("topbar")
        botbar.set_margin_top(0)
        main.pack_end(botbar, False, False, 0)

        # Rotation toggle
        self.rotate_check = Gtk.CheckButton(label="🔁  Auto-Rotate")
        self.rotate_check.set_active(self.rotate_on)
        self.rotate_check.connect("toggled", self.on_rotate_toggle)
        botbar.pack_start(self.rotate_check, False, False, 0)

        # Quality dropdown
        qual_lbl = Gtk.Label(label="🎚  Quality:")
        botbar.pack_start(qual_lbl, False, False, 0)

        QUALITIES = ["auto", "low", "medium", "high"]
        self.quality_combo = Gtk.ComboBoxText()
        for q in QUALITIES:
            self.quality_combo.append_text(q)
        qi = QUALITIES.index(self.quality) if self.quality in QUALITIES else 0
        self.quality_combo.set_active(qi)
        self.quality_combo.connect("changed", self.on_quality_change)
        botbar.pack_start(self.quality_combo, False, False, 0)

        # FPS dropdown
        fps_lbl = Gtk.Label(label="🎞  FPS:")
        botbar.pack_start(fps_lbl, False, False, 0)

        FPSES = ["native", "60", "30", "24", "15", "10"]
        self.fps_combo = Gtk.ComboBoxText()
        for f in FPSES:
            self.fps_combo.append_text(f)
        fi = FPSES.index(self.fps) if self.fps in FPSES else 0
        self.fps_combo.set_active(fi)
        self.fps_combo.connect("changed", self.on_fps_change)
        botbar.pack_start(self.fps_combo, False, False, 0)

        # Interval
        int_lbl = Gtk.Label(label="every")
        botbar.pack_start(int_lbl, False, False, 0)

        self.interval_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 1, 60, 1)
        self.interval_scale.set_value(self.rotate_mins)
        self.interval_scale.set_draw_value(False)
        self.interval_scale.set_size_request(180, -1)
        self.interval_scale.connect("value-changed", self.on_interval)
        botbar.pack_start(self.interval_scale, False, False, 0)

        self.interval_lbl = Gtk.Label(label=f"{self.rotate_mins} min")
        botbar.pack_start(self.interval_lbl, False, False, 0)

        botbar.pack_start(Gtk.Box(), True, True, 0)  # spacer

        # Status
        self.status = Gtk.Label(label="Ready")
        self.status.set_line_wrap(True)
        self.status.set_justify(Gtk.Justification.RIGHT)
        self.status.get_style_context().add_class("status")
        self.status.set_xalign(1)
        self.status.set_ellipsize(3)
        botbar.pack_end(self.status, False, False, 0)

        self.connect("destroy", self.on_destroy)
        self.show_all()
        GLib.idle_add(self.refresh)
        if self.rotate_on:
            self._start_rotate()

    def btn(self, parent, text, cb, primary=False):
        b = Gtk.Button(label=text)
        b.get_style_context().add_class("menu")
        if primary:
            b.get_style_context().add_class("primary")
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
                self.quality = c["main"].get("quality", "auto")
                self.fps = c["main"].get("fps", "native")
        except Exception:
            pass

    def _save_conf(self):
        c = configparser.ConfigParser()
        c["main"] = {
            "rotate": "1" if self.rotate_on else "0",
            "interval": str(self.rotate_mins),
            "quality": self.quality,
            "fps": self.fps,
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
        subprocess.Popen([engine, path, str(w), str(h), self.quality, self.fps],
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
        if hasattr(self, "interval_lbl"):
            self.interval_lbl.set_text(f"{self.rotate_mins} min")
        self._save_conf()
        if self.rotate_on:
            self._stop_rotate()
            self._start_rotate()

    def on_quality_change(self, combo):
        self.quality = combo.get_active_text() or "auto"
        self._save_conf()
        if self.current:
            self.apply(self.current)

    def on_fps_change(self, combo):
        self.fps = combo.get_active_text() or "native"
        self._save_conf()
        if self.current:
            self.apply(self.current)

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
