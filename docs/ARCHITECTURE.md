# How it works

A single GTK3 process. No daemon, no service, no background sync.

```
run.py
  └── prayertimes.app.main()
        ├── single-instance lock (an abstract UNIX socket)
        ├── first run?  ──► settings.SettingsWindow(first_run=True)
        └── otherwise   ──► indicator.PrayerIndicator(config)
                              ├── calc.PrayerCalculator   today's six times
                              ├── hijri                   the date line
                              ├── a 10-second GLib tick   label + notifications
                              └── sound                   adhan playback
```

## The calculation

`calc.py` is a self-contained implementation of the
[PrayTimes](http://praytimes.org/) algorithm. Nothing in it touches the network.

1. The civil date becomes a **Julian date** (`julian_date`).
2. From that, the sun's **declination** and the **equation of time**
   (`sun_position`) — a truncated series accurate to a few arc-seconds for
   any date this program will ever see.
3. Dhuhr is solar noon corrected by the equation of time and the longitude.
4. Every other prayer is the moment the sun sits at a given angle relative to
   the horizon (`_sun_angle_time`), solved with the hour-angle formula.
   Fajr and Isha use the method's twilight angles; Asr uses the shadow-length
   rule of the chosen school (`_asr_time`); sunrise and Maghrib use the
   horizon angle corrected for atmospheric refraction and observer elevation.
5. Where the sun never reaches an angle — high latitudes in summer — the
   result is `None`, and the configured high-latitude rule fills it in
   (`_adjust_hl`): the middle of the night, an angle-based portion, or one
   seventh of the night.
6. Finally the per-prayer minute offsets from the settings are applied and
   the fractional hours become timezone-aware `datetime`s.

Times are internally fractional hours since local midnight, which keeps the
arithmetic in one unit until the very last step.

## The panel label

GNOME Shell draws AppIndicator menus itself over DBusMenu, so only label
*strings* reach it — no widgets, no markup, no column alignment. `indicator.py`
therefore measures each row with Pango and pads it with spaces until every row
is the same pixel width, which is what makes the times line up in the menu.

Two more Shell quirks are worked around there: libayatana will not broadcast a
label identical to the previous one, and the Shell extension drops any label
set before DBus registration finishes. Hence the deferred first label and the
periodic refresh.

## Configuration

`config.py` reads and writes `~/.config/prayer-times/config.json`. Loading
deep-merges the file over `DEFAULTS`, so a config written by an older version
keeps working and gains new keys with sane values. Saving writes to a
temporary file in the same directory and renames it over the original, so an
interrupted write cannot leave a truncated config behind.

Autostart is a standard freedesktop `~/.config/autostart/*.desktop` entry with
a five second delay, written and removed by the same module.
