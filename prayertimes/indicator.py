"""أيقونة الشريط العلوي وقائمتها."""

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
gi.require_version("Notify", "0.7")

from datetime import datetime, timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from gi.repository import AyatanaAppIndicator3 as AppIndicator  # noqa: E402
from gi.repository import GLib, Gtk, Notify  # noqa: E402

from . import hijri, sound  # noqa: E402
from .calc import PRAYER_NAMES_AR, PRAYERS, PrayerCalculator, next_prayer  # noqa: E402
from .settings import SettingsWindow  # noqa: E402

APP_NAME = "أوقات الصلاة"
INDICATOR_ID = "prayer-times"

ARABIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def _digits(text, arabic):
    return text.translate(ARABIC_DIGITS) if arabic else text


# المسافة بين عمود الاسم وعمود الوقت، بعرض مسافات
_COLUMN_GAP = 6

_measure_widget = None


def _text_width(text):
    """عرض النص بالبكسل حسب خط الواجهة الحالي."""
    global _measure_widget
    if _measure_widget is None:
        _measure_widget = Gtk.Label()
    return _measure_widget.create_pango_layout(text).get_pixel_size()[0]


def _grid_labels(rows, min_width=0):
    """يحوّل [(اسم, وقت)] إلى نصوص قائمة بعمودين محاذيين.

    min_width يمدّد الجدول ليملأ عرض القائمة (عرض أطول سطر فيها).

    جنوم-شل يرسم قوائم AppIndicator بنفسه عبر DBusMenu، فلا تنتقل إليه
    إلا نصوص التسميات — لا ويدجتات ولا تنسيق. وهو يحاذي كل سطر من اليسار،
    وباتجاه RTL يكون الوقت (آخر العناصر منطقياً) أقصى اليسار فينضبط عموده
    تلقائياً. يبقى أن نضبط عمود الأسماء: نساوي العرض الكلي لكل صف بحشو
    مسافات مقيسة فعلياً بـ Pango، فتتحاذى حافة الأسماء اليمنى أيضاً.
    """
    if not rows:
        return []

    # التشكيل العربي يجعل العرض غير جمعيّ (عرض الاسم + المسافات ≠ عرض
    # الناتج)، لذا نقيس النص النهائي ونزيد المسافات حتى تتساوى العروض.
    space = _text_width(" ") or 4
    build = lambda name, time_text, pad: f"{name}{' ' * pad}{time_text}"

    pads = {i: _COLUMN_GAP for i in range(len(rows))}
    target = max(max(_text_width(build(n, t, _COLUMN_GAP)) for n, t in rows),
                 int(min_width))

    for i, (name, time_text) in enumerate(rows):
        # حدّ أعلى للحلقة يمنع أي دوران غير منتهٍ لو تعذّر القياس
        for _ in range(80):
            width = _text_width(build(name, time_text, pads[i]))
            if width >= target - space / 2:
                break
            pads[i] += 1

    return [build(n, t, pads[i]) for i, (n, t) in enumerate(rows)]


class PrayerIndicator:
    def __init__(self, cfg):
        self.cfg = cfg
        self.calc = None
        self.tz = None
        self.today_times = {}
        self._times_date = None

        # تتبّع ما أُشعر به حتى لا يتكرر التنبيه في نفس الدقيقة
        self._fired = set()
        self._settings_window = None
        self._last_label = None
        # libayatana لا تبثّ تسمية مطابقة للقيمة السابقة، وإضافة جنوم لا
        # تلتقط ما ضُبط قبل اكتمال التسجيل على DBus. لذلك نمتنع عن ضبط
        # التسمية نهائياً حتى تكتمل، ثم نضبطها لأول مرة فيُبثّ التغيير.
        self._label_ready = False

        Notify.init(APP_NAME)

        self.indicator = AppIndicator.Indicator.new(
            INDICATOR_ID, "prayer-times",
            AppIndicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.indicator.set_title(APP_NAME)

        self.menu = Gtk.Menu()
        self.indicator.set_menu(self.menu)

        self.reload(cfg)

        # نبضة كل ١٠ ثوانٍ: كافية لدقة الدقيقة وخفيفة على المعالج
        GLib.timeout_add_seconds(10, self._tick)
        # إضافة الشريط في جنوم لا تلتقط التسمية إن ضُبطت قبل اكتمال
        # التسجيل على DBus، لذلك نؤجّل أول ضبط بثانيتين.
        GLib.timeout_add_seconds(2, self._first_label)
        # التسمية لا تُبثّ إلا عند تغيّر نصّها؛ ننعش دورياً كي تعود
        # للظهور لو أُعيد تشغيل جنوم-شل والنص ثابت (العدّاد مُطفأ).
        GLib.timeout_add_seconds(300, self._force_label_refresh)

    # ------------------------------------------------------ الإعدادات

    def reload(self, cfg):
        """يعيد بناء الحاسبة والقائمة بعد تغيّر الإعدادات."""
        self.cfg = cfg
        try:
            self.tz = ZoneInfo(cfg["timezone"])
        except Exception:
            self.tz = ZoneInfo("UTC")

        self.calc = PrayerCalculator(
            lat=cfg["latitude"],
            lng=cfg["longitude"],
            elevation=cfg.get("elevation", 0.0),
            method=cfg.get("method", "MWL"),
            params={"asr": cfg.get("asr", "Standard"),
                    "highLats": cfg.get("high_lats", "NightMiddle")},
            offsets=cfg.get("offsets", {}),
        )
        self._times_date = None
        self._fired.clear()
        self._refresh_times()
        self._build_menu()
        self._update_label()

    # ------------------------------------------------------ الأوقات

    def _now(self):
        return datetime.now(self.tz)

    def _refresh_times(self):
        today = self._now().date()
        if self._times_date == today and self.today_times:
            return
        try:
            self.today_times = self.calc.datetimes_for(today, self.cfg["timezone"])
            self._times_date = today
            self._fired.clear()
        except Exception as exc:  # حساب فاشل يجب ألا يُسقط البرنامج
            print(f"[prayer-times] تعذّر حساب الأوقات: {exc}")
            self.today_times = {}

    def _fmt_time(self, dt):
        if dt is None:
            return "—"
        if self.cfg.get("time_format_24h", True):
            text = dt.strftime("%H:%M")
        else:
            text = dt.strftime("%I:%M").lstrip("0")
            text += " ص" if dt.hour < 12 else " م"
        return _digits(text, self.cfg.get("arabic_numerals", False))

    def _fmt_delta(self, delta):
        total = max(0, int(delta.total_seconds()))
        hours, rem = divmod(total, 3600)
        minutes = rem // 60
        text = f"{hours}:{minutes:02d}" if hours else f"{minutes} د"
        return _digits(text, self.cfg.get("arabic_numerals", False))

    # ------------------------------------------------------ القائمة

    def _build_menu(self):
        for child in self.menu.get_children():
            self.menu.remove(child)

        now = self._now()
        upcoming, _ = next_prayer(self.calc, self.cfg["timezone"], now)

        # رأس: المدينة والتاريخ
        city = self.cfg.get("city") or "موقع مخصّص"
        header = Gtk.MenuItem(label=f"📍 {city}")
        header.set_sensitive(False)
        self.menu.append(header)

        greg = hijri.format_gregorian(now.date())
        hij = hijri.format_hijri(now.date(), self.cfg.get("hijri_offset", 0))
        date_item = Gtk.MenuItem(label=f"{greg}")
        date_item.set_sensitive(False)
        self.menu.append(date_item)
        hijri_item = Gtk.MenuItem(label=f"{hij}")
        hijri_item.set_sensitive(False)
        self.menu.append(hijri_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        # الصلوات — تُبنى كجدول بعمودين محاذيين
        rows = []
        for prayer in PRAYERS:
            marker = "◀" if prayer == upcoming else " "
            rows.append((f"{marker} {PRAYER_NAMES_AR[prayer]}",
                         self._fmt_time(self.today_times.get(prayer))))
        midnight = self.today_times.get("midnight")
        if midnight is not None:
            rows.append((f"  {PRAYER_NAMES_AR['midnight']}",
                         self._fmt_time(midnight)))

        # يملأ الجدول عرض أطول سطر في القائمة بدل أن يبقى منكمشاً
        menu_width = max(_text_width(t) for t in
                         (f"📍 {city}", greg, hij, "⚙  الإعدادات…"))
        # تُترك مفعّلة عمداً: جنوم-شل يرسم العنصر المعطّل باهتاً، وهذه
        # الصفوف هي محتوى القائمة الأساسي فيجب أن تكون أوضح ما فيها.
        # النقر عليها لا يفعل شيئاً سوى إغلاق القائمة.
        for label in _grid_labels(rows, min_width=menu_width):
            self.menu.append(Gtk.MenuItem(label=label))

        self.menu.append(Gtk.SeparatorMenuItem())

        # أوامر
        settings_item = Gtk.MenuItem(label="⚙  الإعدادات…")
        settings_item.connect("activate", self.open_settings)
        self.menu.append(settings_item)

        mute_item = Gtk.MenuItem(label="🔇  إيقاف الصوت الجاري")
        mute_item.connect("activate", lambda *_: sound.stop())
        self.menu.append(mute_item)

        refresh_item = Gtk.MenuItem(label="↻  إعادة حساب الأوقات")
        refresh_item.connect("activate", self._on_refresh)
        self.menu.append(refresh_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="✕  خروج")
        quit_item.connect("activate", self._on_quit)
        self.menu.append(quit_item)

        self.menu.show_all()

    def _on_refresh(self, *_args):
        self._times_date = None
        self._refresh_times()
        self._build_menu()
        self._update_label()

    def _on_quit(self, *_args):
        sound.stop()
        Notify.uninit()
        Gtk.main_quit()

    # ------------------------------------------------------ نص الشريط

    def _update_label(self):
        now = self._now()
        name, when = next_prayer(self.calc, self.cfg["timezone"], now)
        if name is None:
            if self._label_ready:
                self.indicator.set_label(" ", "")
            return

        parts = []
        if self.cfg.get("show_prayer_name", True):
            parts.append(PRAYER_NAMES_AR[name])
        if self.cfg.get("show_countdown", True):
            parts.append(self._fmt_delta(when - now))
        else:
            parts.append(self._fmt_time(when))

        text = " ‑ ".join(parts) if parts else " "
        if not self._label_ready:
            return
        if text != self._last_label:
            self._last_label = text
            self.indicator.set_label(text, text)
        self.indicator.set_title(
            f"{PRAYER_NAMES_AR[name]} — {self._fmt_time(when)}")

    def _first_label(self):
        self._label_ready = True
        self._last_label = None
        self._update_label()
        return False

    def _force_label_refresh(self):
        """يعيد بثّ التسمية عبر مسافة صفرية العرض — غير مرئية للمستخدم."""
        if self._last_label:
            self.indicator.set_label(self._last_label + "\u200b", self._last_label)
            self.indicator.set_label(self._last_label, self._last_label)
        return True

    # ------------------------------------------------------ التنبيهات

    def _notify(self, title, body, urgent=False):
        try:
            note = Notify.Notification.new(title, body, "prayer-times")
            note.set_urgency(Notify.Urgency.CRITICAL if urgent
                             else Notify.Urgency.NORMAL)
            note.set_timeout(15000)
            note.show()
        except Exception as exc:
            print(f"[prayer-times] تعذّر الإشعار: {exc}")

    def _check_alerts(self):
        if not self.cfg.get("notify_enabled", True) and \
           not self.cfg.get("sound_enabled", False):
            return

        now = self._now().replace(second=0, microsecond=0)
        enabled = self.cfg.get("notify_prayers", {})
        before = int(self.cfg.get("notify_before_minutes", 10))

        for prayer in PRAYERS:
            dt = self.today_times.get(prayer)
            if dt is None or not enabled.get(prayer, prayer != "sunrise"):
                continue

            # تنبيه مسبق
            if before > 0 and self.cfg.get("notify_enabled", True):
                key = (prayer, "before", dt.date())
                if key not in self._fired and now == dt - timedelta(minutes=before):
                    self._fired.add(key)
                    mins = _digits(str(before), self.cfg.get("arabic_numerals", False))
                    self._notify(
                        f"اقترب وقت {PRAYER_NAMES_AR[prayer]}",
                        f"بقي {mins} دقيقة — الأذان {self._fmt_time(dt)}")

            # عند دخول الوقت
            key = (prayer, "at", dt.date())
            if key not in self._fired and now == dt:
                self._fired.add(key)
                if self.cfg.get("notify_enabled", True) and \
                   self.cfg.get("notify_at_time", True):
                    self._notify(
                        f"حان الآن وقت {PRAYER_NAMES_AR[prayer]}",
                        f"{self._fmt_time(dt)} — "
                        f"{self.cfg.get('city') or 'موقعك'}",
                        urgent=True)
                if self.cfg.get("sound_enabled", False) and prayer != "sunrise":
                    sound.play(self.cfg.get("sound_file", ""))

    # ------------------------------------------------------ النبضة

    def _tick(self):
        try:
            previous_date = self._times_date
            self._refresh_times()
            self._update_label()
            self._check_alerts()

            # عند تغيّر اليوم أو تغيّر الصلاة القادمة نعيد بناء القائمة
            now = self._now()
            upcoming, _ = next_prayer(self.calc, self.cfg["timezone"], now)
            if previous_date != self._times_date or \
               getattr(self, "_last_upcoming", None) != upcoming:
                self._last_upcoming = upcoming
                self._build_menu()
        except Exception as exc:
            print(f"[prayer-times] خطأ في التحديث الدوري: {exc}")
        return True  # استمر

    # ------------------------------------------------------ الإعدادات

    def open_settings(self, *_args):
        if self._settings_window is not None:
            self._settings_window.present()
            return

        window = SettingsWindow(self.cfg, on_saved=self._on_settings_saved)
        window.connect("destroy", self._on_settings_closed)
        self._settings_window = window
        window.show_all()
        window.present()

    def _on_settings_closed(self, *_args):
        self._settings_window = None

    def _on_settings_saved(self, cfg):
        self.reload(cfg)
        self._notify("تم حفظ الإعدادات",
                     f"{cfg.get('city') or 'الموقع المخصّص'} — "
                     f"{self._fmt_time(self.today_times.get('fajr'))} الفجر")
        return False
