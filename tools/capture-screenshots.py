#!/usr/bin/env python3
"""Regenerate the screenshots used in README.md.

Runs the settings window and a real indicator with a throwaway demo config
(Mecca) in a temporary XDG_CONFIG_HOME, so your own settings are never
touched. Any instance already installed under ~/.local is stopped for the
duration and restarted afterwards.

    python3 tools/capture-screenshots.py [OUT_DIR] [what]

    OUT_DIR   defaults to docs/screenshots
    what      all (default) | settings | shell

Needs a running X11 GNOME session (the "shell" shots click the real panel
item and photograph the menu GNOME Shell draws for it) and `xdotool`.
Screenshots are taken by cropping the root window, which is how ordinary
screenshot tools work, so window decorations and shadows come out right.
"""

import json
import os
import subprocess
import sys
import tempfile
import time

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "docs/screenshots"
WHAT = sys.argv[2] if len(sys.argv) > 2 else "all"

DEMO_CITY = "مكة المكرمة"
INSTALLED = os.path.expanduser("~/.local/share/prayer-times/run.py")

# Settings notebook pages worth showing, as (page index, file name).
TABS = [
    (0, "settings-location"),
    (1, "settings-calculation"),
    (2, "settings-adjustments"),
    (3, "settings-alerts"),
    (4, "settings-display"),
]


# --------------------------------------------------------------- screen grabs

def screen():
    return Gdk.get_default_root_window()


def grab(x, y, width, height, path=None):
    pb = Gdk.pixbuf_get_from_window(screen(), x, y, width, height)
    if pb is not None and path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        pb.savev(path, "png", [], [])
        print(f"==> {path}  ({pb.get_width()}x{pb.get_height()})")
    return pb


def grab_window(gdk_window, path):
    frame = gdk_window.get_frame_extents()
    grab(frame.x, frame.y, frame.width, frame.height, path)


def pixel_differs(before, after, tolerance=24):
    """Return a f(x, y) telling whether two same-sized captures differ there."""
    pa, pb = before.get_pixels(), after.get_pixels()
    sa, sb = before.get_rowstride(), after.get_rowstride()
    na, nb = before.get_n_channels(), after.get_n_channels()

    def differs(x, y):
        ia, ib = y * sa + x * na, y * sb + x * nb
        return (abs(pa[ia] - pb[ib]) + abs(pa[ia + 1] - pb[ib + 1])
                + abs(pa[ia + 2] - pb[ib + 2])) > tolerance

    return differs


def is_popup_colour(pb):
    """Return a f(x, y) matching the flat light background of a Shell menu."""
    px, stride, nch = pb.get_pixels(), pb.get_rowstride(), pb.get_n_channels()

    def light(x, y):
        i = y * stride + x * nch
        r, g, b = px[i], px[i + 1], px[i + 2]
        return min(r, g, b) > 224 and max(r, g, b) - min(r, g, b) < 12

    return light


def longest_run(flags):
    """Start and end index of the longest stretch of True in a list."""
    best = current = None
    for i, on in enumerate(flags):
        current = (current[0], i) if (on and current) else ((i, i) if on else None)
        if current and (best is None or current[1] - current[0] > best[1] - best[0]):
            best = current
    return best


def close_gaps(flags, gap):
    """Bridge runs of False no longer than `gap`, so glyphs merge into words."""
    out, last = list(flags), None
    for i, on in enumerate(flags):
        if on:
            if last is not None and i - last <= gap:
                out[last + 1:i] = [True] * (i - last - 1)
            last = i
    return out


# --------------------------------------------------------------- demo config

def demo_config():
    from prayertimes import cities, config

    cfg = dict(config.DEFAULTS)
    name, _, lat, lng, tz, method = cities.find(DEMO_CITY)
    cfg.update(configured=True, city=name, latitude=lat, longitude=lng,
               timezone=tz, method=method)
    return cfg


def write_demo_config(directory):
    cfg = demo_config()
    os.makedirs(os.path.join(directory, "prayer-times"), exist_ok=True)
    with open(os.path.join(directory, "prayer-times", "config.json"), "w",
              encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False)
    return cfg


def installed_instances():
    """PIDs of a prayer-times installed under ~/.local that is running now."""
    pids = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            raw = open(f"/proc/{entry}/cmdline", "rb").read()
        except OSError:
            continue
        argv = [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part]
        if len(argv) == 2 and argv[1] == INSTALLED:
            pids.append(entry)
    return pids


# --------------------------------------------------------------- settings shots

def shoot_settings(cfg):
    """Open the settings window and photograph each tab."""
    from prayertimes.settings import SettingsWindow

    window = SettingsWindow(dict(cfg), on_saved=lambda c: False, first_run=False)
    window.set_position(Gtk.WindowPosition.CENTER)
    window.show_all()

    queue = []
    for index, name in TABS:
        queue.append(lambda i=index: window.notebook.set_current_page(i))
        queue.append(lambda n=name: grab_window(window.get_window(),
                                                os.path.join(OUT_DIR, n + ".png")))
    queue.append(window.destroy)

    def pump():
        if not queue:
            Gtk.main_quit()
            return False
        queue.pop(0)()
        GLib.timeout_add(700, pump)
        return False

    GLib.timeout_add(1500, pump)
    Gtk.main()


# --------------------------------------------------------------- shell shots

def shoot_shell():
    """Photograph the panel item and the menu GNOME Shell draws for it."""
    tmp = tempfile.mkdtemp(prefix="prayer-times-shots-")
    write_demo_config(tmp)

    stopped = installed_instances()
    for pid in stopped:
        subprocess.run(["kill", pid], check=False)
    if stopped:
        print(f"    (paused the installed instance: {', '.join(stopped)})")
        time.sleep(3)

    demo = subprocess.Popen([sys.executable, os.path.join(ROOT, "run.py")],
                            env=dict(os.environ, XDG_CONFIG_HOME=tmp))
    time.sleep(8)

    try:
        _shoot_shell_inner()
    finally:
        demo.terminate()
        time.sleep(1)
        if stopped:
            subprocess.Popen(["python3", INSTALLED], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("    (restarted the installed instance)")


def _shoot_shell_inner():
    width = screen().get_width()
    region_x, region_w, region_h = width - 700, 700, 1010

    # Click along the right-hand side of the panel until a tall popup appears.
    for click_x in range(width - 460, width - 280, 10):
        before = grab(region_x, 0, region_w, region_h)
        subprocess.run(["xdotool", "mousemove", str(click_x), "14", "click", "1"],
                       check=False)
        time.sleep(1.8)
        after = grab(region_x, 0, region_w, region_h)

        box = _popup_box(before, after, region_w, region_h)
        if box:
            x0, x1, y0, y1 = box
            # The panel strip above the popup carries the highlighted item.
            menu = after.new_subpixbuf(x0, 0, x1 - x0 + 1, y1 + 1)
            path = os.path.join(OUT_DIR, "menu.png")
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            menu.savev(path, "png", [], [])
            print(f"==> {path}  ({menu.get_width()}x{menu.get_height()})")

            subprocess.run(["xdotool", "key", "Escape"], check=False)
            time.sleep(1.2)
            grab(region_x + x0 - 12, 0, (x1 - x0) + 24, 30,
                 os.path.join(OUT_DIR, "panel.png"))
            return

        subprocess.run(["xdotool", "key", "Escape"], check=False)
        time.sleep(0.5)

    print("!! could not open the panel menu -- is the indicator running?")


def _popup_box(before, after, width, height):
    """Locate the menu: the region that both changed and is popup-coloured."""
    differs = pixel_differs(before, after)
    light = is_popup_colour(after)

    rows = range(0, height, 4)
    columns = close_gaps(
        [sum(differs(x, y) and light(x, y) for y in rows) > 40 for x in range(width)], 6)
    xr = longest_run(columns)
    if xr is None or not 150 < xr[1] - xr[0] < 420:
        return None

    sample = list(range(xr[0] + 4, xr[1] - 3, 4))
    lines = close_gaps(
        [sum(light(x, y) for x in sample) > 0.5 * len(sample) for y in range(height)], 8)
    yr = longest_run(lines)
    if yr is None or yr[1] - yr[0] < 400:
        return None
    return xr[0], xr[1], yr[0], yr[1]


# --------------------------------------------------------------- entry point

def main():
    if not os.environ.get("DISPLAY"):
        print("!! DISPLAY is not set -- an X11 session is required")
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    Gtk.Widget.set_default_direction(Gtk.TextDirection.RTL)

    if WHAT in ("all", "shell"):
        if not subprocess.run(["which", "xdotool"], capture_output=True).returncode == 0:
            print("!! xdotool is needed for the panel shots: sudo apt install xdotool")
            return 1
        shoot_shell()

    if WHAT in ("all", "settings"):
        # The demo config is handed straight to the window as a dict. Nothing is
        # written: SettingsWindow only touches disk when Save is pressed, and we
        # never press it -- so the window can show the real config path.
        shoot_settings(demo_config())

    return 0


if __name__ == "__main__":
    sys.exit(main())
