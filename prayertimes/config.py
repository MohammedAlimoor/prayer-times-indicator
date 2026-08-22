"""تحميل وحفظ الإعدادات + إدارة التشغيل التلقائي مع بدء الجهاز."""

import json
import os
import shutil
import sys

APP_ID = "prayer-times"

CONFIG_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), APP_ID)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

AUTOSTART_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "autostart")
AUTOSTART_PATH = os.path.join(AUTOSTART_DIR, f"{APP_ID}.desktop")

DEFAULTS = {
    # لم تُضبط الإعدادات بعد ⇒ يفتح معالج الإعداد أول مرة
    "configured": False,

    # الموقع
    "city": "",
    "latitude": 21.3891,
    "longitude": 39.8579,
    "elevation": 0.0,
    "timezone": "Asia/Riyadh",

    # الحساب
    "method": "Makkah",
    "asr": "Standard",
    "high_lats": "NightMiddle",
    "hijri_offset": 0,

    # تعديل يدوي بالدقائق لكل صلاة
    "offsets": {
        "fajr": 0, "sunrise": 0, "dhuhr": 0,
        "asr": 0, "maghrib": 0, "isha": 0,
    },

    # العرض في الشريط العلوي
    "show_countdown": True,
    "show_prayer_name": True,
    "time_format_24h": True,
    "arabic_numerals": False,

    # التنبيهات
    "notify_enabled": True,
    "notify_before_minutes": 10,
    "notify_at_time": True,
    "sound_enabled": False,
    "sound_file": "",
    "sound_at_adhan_only": True,
    # الصلوات التي تُفعَّل لها التنبيهات
    "notify_prayers": {
        "fajr": True, "sunrise": False, "dhuhr": True,
        "asr": True, "maghrib": True, "isha": True,
    },

    "autostart": True,
}


def _deep_merge(base, override):
    out = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load():
    """يقرأ الإعدادات، ويرجع الافتراضية إن لم يوجد ملف أو كان تالفاً."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("config root is not an object")
        return _deep_merge(DEFAULTS, data)
    except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
        return dict(DEFAULTS)


def save(config):
    """يكتب الإعدادات ذرّياً حتى لا يتلف الملف عند انقطاع مفاجئ."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, CONFIG_PATH)


# ------------------------------------------------- التشغيل التلقائي

def _launch_command():
    """أمر تشغيل البرنامج — يفضّل السكربت المثبّت، وإلا يستدعي بايثون مباشرة."""
    installed = shutil.which(APP_ID)
    if installed:
        return installed

    # التشغيل من مجلد المشروع مباشرة
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return f"{sys.executable} {os.path.join(project_root, 'run.py')}"


DESKTOP_TEMPLATE = """[Desktop Entry]
Type=Application
Name=أوقات الصلاة
Name[en]=Prayer Times
Comment=عرض أوقات الصلاة في الشريط العلوي
Comment[en]=Prayer times in the top bar
Exec={exec_cmd}
Icon={icon}
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=5
"""


def autostart_enabled():
    return os.path.exists(AUTOSTART_PATH)


def set_autostart(enabled, icon="prayer-times"):
    """يفعّل أو يعطّل التشغيل مع بدء الجهاز عبر ملف autostart قياسي."""
    if enabled:
        os.makedirs(AUTOSTART_DIR, exist_ok=True)
        content = DESKTOP_TEMPLATE.format(
            exec_cmd=_launch_command(), icon=icon)
        with open(AUTOSTART_PATH, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.chmod(AUTOSTART_PATH, 0o755)
    else:
        try:
            os.remove(AUTOSTART_PATH)
        except FileNotFoundError:
            pass
    return autostart_enabled()
