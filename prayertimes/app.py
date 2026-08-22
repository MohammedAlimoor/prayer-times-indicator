"""نقطة الدخول — يفتح معالج الإعداد أول مرة، ثم يعمل في الشريط العلوي."""

import signal
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from . import config  # noqa: E402


def _single_instance():
    """يمنع تشغيل أكثر من نسخة عبر قفل على مقبس مجرّد (abstract socket)."""
    import socket
    try:
        lock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        lock.bind("\0prayer-times-indicator")
        return lock
    except OSError:
        return None


def main():
    lock = _single_instance()
    if lock is None:
        print("أوقات الصلاة يعمل بالفعل.", file=sys.stderr)
        return 0

    # اجعل واجهة GTK من اليمين إلى اليسار
    Gtk.Widget.set_default_direction(Gtk.TextDirection.RTL)
    # Ctrl+C في الطرفية يغلق البرنامج بشكل نظيف
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    cfg = config.load()

    if not cfg.get("configured"):
        # أول تشغيل: أظهر المعالج، وشغّل الأيقونة بعد الحفظ فقط
        from .settings import SettingsWindow

        state = {"indicator": None}

        def on_saved(new_cfg):
            from .indicator import PrayerIndicator
            state["indicator"] = PrayerIndicator(new_cfg)
            return False

        def on_destroy(_window):
            # أُغلق المعالج بدون حفظ ⇒ لا شيء يعمل، فاخرج
            if state["indicator"] is None:
                Gtk.main_quit()

        window = SettingsWindow(cfg, on_saved=on_saved, first_run=True)
        window.connect("destroy", on_destroy)
        window.show_all()
    else:
        from .indicator import PrayerIndicator
        PrayerIndicator(cfg)

    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
