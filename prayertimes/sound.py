"""تشغيل صوت الأذان عبر أول مشغّل متاح في النظام."""

import os
import shutil
import subprocess

# مرتبة حسب الأفضلية؛ كلها تدعم mp3/ogg/wav عدا aplay (wav فقط)
PLAYERS = [
    ("paplay", ["paplay"]),
    ("gst-play-1.0", ["gst-play-1.0", "--quiet"]),
    ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]),
    ("mpv", ["mpv", "--no-video", "--really-quiet"]),
    ("aplay", ["aplay", "-q"]),
]

_current = None


def _find_player(path):
    is_wav = path.lower().endswith(".wav")
    for name, argv in PLAYERS:
        if name == "paplay" and not is_wav:
            continue          # paplay يتعامل مع wav/ogg فقط بشكل موثوق
        if name == "aplay" and not is_wav:
            continue
        if shutil.which(name):
            return argv
    return None


def play(path=""):
    """يشغّل الملف المحدد، أو نغمة النظام إن كان المسار فارغاً/غير موجود.

    يرجع True إذا بدأ التشغيل فعلاً.
    """
    global _current
    stop()

    path = (path or "").strip()
    if path and os.path.isfile(path):
        argv = _find_player(path)
        if argv:
            try:
                _current = subprocess.Popen(
                    argv + [path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    start_new_session=True)
                return True
            except OSError:
                pass

    # الرجوع إلى نغمة النظام
    if shutil.which("canberra-gtk-play"):
        try:
            _current = subprocess.Popen(
                ["canberra-gtk-play", "-i", "complete"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True)
            return True
        except OSError:
            pass
    return False


def stop():
    """يوقف الصوت الجاري إن وُجد."""
    global _current
    if _current and _current.poll() is None:
        try:
            _current.terminate()
        except OSError:
            pass
    _current = None


def is_playing():
    return bool(_current and _current.poll() is None)
