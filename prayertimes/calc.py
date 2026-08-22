"""حساب أوقات الصلاة فلكياً — بدون إنترنت.

الخوارزمية قياسية (PrayTimes) وتعتمد على موضع الشمس المحسوب من التاريخ اليولياني.
كل الأوقات داخلياً تُمثَّل كسور ساعة (float) من منتصف الليل المحلي.
"""

import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------- الثوابت

PRAYERS = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]

PRAYER_NAMES_AR = {
    "fajr": "الفجر",
    "sunrise": "الشروق",
    "dhuhr": "الظهر",
    "asr": "العصر",
    "maghrib": "المغرب",
    "isha": "العشاء",
    "imsak": "الإمساك",
    "midnight": "منتصف الليل",
}

# طرق الحساب. القيم النصية مثل "90 min" تعني عدد دقائق بعد الوقت السابق.
METHODS = {
    "MWL": {
        "name": "رابطة العالم الإسلامي",
        "params": {"fajr": 18.0, "isha": 17.0},
    },
    "ISNA": {
        "name": "الجمعية الإسلامية لأمريكا الشمالية (ISNA)",
        "params": {"fajr": 15.0, "isha": 15.0},
    },
    "Egypt": {
        "name": "الهيئة المصرية العامة للمساحة",
        "params": {"fajr": 19.5, "isha": 17.5},
    },
    "Makkah": {
        "name": "أم القرى — مكة المكرمة",
        "params": {"fajr": 18.5, "isha": "90 min"},
    },
    "Karachi": {
        "name": "جامعة العلوم الإسلامية — كراتشي",
        "params": {"fajr": 18.0, "isha": 18.0},
    },
    "Tehran": {
        "name": "معهد الجيوفيزياء — طهران",
        "params": {"fajr": 17.7, "isha": 14.0, "maghrib": 4.5, "midnight": "Jafari"},
    },
    "Jafari": {
        "name": "الشيعة الإثنا عشرية (جعفري)",
        "params": {"fajr": 16.0, "isha": 14.0, "maghrib": 4.0, "midnight": "Jafari"},
    },
    "Gulf": {
        "name": "هيئة الخليج",
        "params": {"fajr": 19.5, "isha": "90 min"},
    },
    "Kuwait": {
        "name": "الكويت",
        "params": {"fajr": 18.0, "isha": 17.5},
    },
    "Qatar": {
        "name": "قطر",
        "params": {"fajr": 18.0, "isha": "90 min"},
    },
    "Singapore": {
        "name": "سنغافورة",
        "params": {"fajr": 20.0, "isha": 18.0},
    },
    "Turkey": {
        "name": "ديانت — تركيا",
        "params": {"fajr": 18.0, "isha": 17.0},
    },
    "Tunisia": {
        "name": "تونس",
        "params": {"fajr": 18.0, "isha": 18.0},
    },
    "Algeria": {
        "name": "الجزائر",
        "params": {"fajr": 18.0, "isha": 17.0},
    },
    "Morocco": {
        "name": "المغرب",
        "params": {"fajr": 19.0, "isha": 17.0},
    },
    "Jordan": {
        "name": "وزارة الأوقاف — الأردن",
        "params": {"fajr": 18.0, "isha": 18.0},
    },
    "Indonesia": {
        "name": "إندونيسيا",
        "params": {"fajr": 20.0, "isha": 18.0},
    },
    "Russia": {
        "name": "الإدارة الروحية لمسلمي روسيا",
        "params": {"fajr": 16.0, "isha": 15.0},
    },
}

DEFAULT_PARAMS = {
    "imsak": "10 min",
    "dhuhr": "0 min",
    "asr": "Standard",   # Standard (شافعي/مالكي/حنبلي) أو Hanafi
    "maghrib": "0 min",
    "midnight": "Standard",
    "highLats": "NightMiddle",
}

# معالجة خطوط العرض العالية
HIGH_LAT_METHODS = {
    "None": "بدون تعديل",
    "NightMiddle": "منتصف الليل",
    "AngleBased": "حسب الزاوية (سُبع الليل)",
    "OneSeventh": "سُبع الليل",
}

ASR_METHODS = {
    "Standard": "الجمهور (شافعي/مالكي/حنبلي) — ظل المثل",
    "Hanafi": "حنفي — ظل المثلين",
}


# ------------------------------------------------- دوال مثلثية بالدرجات

def _dsin(d):
    return math.sin(math.radians(d))


def _dcos(d):
    return math.cos(math.radians(d))


def _dtan(d):
    return math.tan(math.radians(d))


def _darcsin(x):
    return math.degrees(math.asin(x))


def _darccos(x):
    return math.degrees(math.acos(x))


def _darctan2(y, x):
    return math.degrees(math.atan2(y, x))


def _darccot(x):
    return math.degrees(math.atan2(1.0, x))


def _fix(a, b):
    a = a - b * math.floor(a / b)
    return a + b if a < 0 else a


def _fixangle(a):
    return _fix(a, 360.0)


def _fixhour(a):
    return _fix(a, 24.0)


# ------------------------------------------------------ فلك الشمس

def julian_date(year, month, day):
    """التاريخ اليولياني عند منتصف ليل التوقيت العالمي."""
    if month <= 2:
        year -= 1
        month += 12
    a = math.floor(year / 100.0)
    b = 2 - a + math.floor(a / 4.0)
    return (math.floor(365.25 * (year + 4716))
            + math.floor(30.6001 * (month + 1))
            + day + b - 1524.5)


def sun_position(jd):
    """يرجع (الميل، معادلة الزمن) بالدرجات والساعات."""
    d = jd - 2451545.0
    g = _fixangle(357.529 + 0.98560028 * d)          # الشذوذ الوسطي
    q = _fixangle(280.459 + 0.98564736 * d)          # خط الطول الوسطي
    lam = _fixangle(q + 1.915 * _dsin(g) + 0.020 * _dsin(2 * g))  # خط الطول الظاهري

    eps = 23.439 - 0.00000036 * d                    # ميل فلك البروج
    decl = _darcsin(_dsin(eps) * _dsin(lam))         # الميل
    ra = _fixhour(_darctan2(_dcos(eps) * _dsin(lam), _dcos(lam)) / 15.0)
    eqt = q / 15.0 - ra                              # معادلة الزمن
    return decl, eqt


# ------------------------------------------------------- المحرك

class PrayerCalculator:
    """يحسب أوقات الصلاة ليوم معيّن في موقع معيّن."""

    def __init__(self, lat, lng, elevation=0.0, method="MWL",
                 params=None, offsets=None):
        self.lat = float(lat)
        self.lng = float(lng)
        self.elevation = float(elevation or 0.0)

        self.params = dict(DEFAULT_PARAMS)
        self.params.update(METHODS.get(method, METHODS["MWL"])["params"])
        if params:
            self.params.update({k: v for k, v in params.items() if v is not None})

        # تعديل يدوي بالدقائق لكل صلاة
        self.offsets = {p: 0 for p in PRAYERS}
        self.offsets["imsak"] = 0
        self.offsets["midnight"] = 0
        if offsets:
            self.offsets.update(offsets)

        self._jdate = 0.0

    # ---------------------------------------------------- داخلي

    def _mid_day(self, t):
        _, eqt = sun_position(self._jdate + t)
        return _fixhour(12.0 - eqt)

    def _sun_angle_time(self, angle, t, ccw=False):
        """الوقت الذي تكون فيه الشمس على ارتفاع زاوي معيّن.

        يرجع None إذا لم تبلغ الشمس تلك الزاوية أصلاً في ذلك اليوم
        (يحصل في خطوط العرض العالية).
        """
        decl, _ = sun_position(self._jdate + t)
        noon = self._mid_day(t)
        num = -_dsin(angle) - _dsin(decl) * _dsin(self.lat)
        den = _dcos(decl) * _dcos(self.lat)
        if den == 0:
            return None
        ratio = num / den
        if ratio > 1.0 or ratio < -1.0:
            return None
        hours = _darccos(ratio) / 15.0
        return noon - hours if ccw else noon + hours

    def _asr_time(self, factor, t):
        decl, _ = sun_position(self._jdate + t)
        angle = -_darccot(factor + _dtan(abs(self.lat - decl)))
        return self._sun_angle_time(angle, t)

    def _rise_set_angle(self):
        # 0.833° تصحيح الانكسار الجوي + نصف قطر القرص، مع تصحيح الارتفاع
        elv = self.elevation
        sign = 1.0 if elv >= 0 else -1.0
        return 0.833 + 0.0347 * sign * math.sqrt(abs(elv))

    def _asr_factor(self):
        return 2.0 if str(self.params.get("asr")) == "Hanafi" else 1.0

    @staticmethod
    def _eval_minutes(value):
        """يحوّل «90 min» إلى 90.0، ويرجع None إن كانت القيمة زاوية."""
        if isinstance(value, str) and "min" in value:
            try:
                return float(value.split()[0])
            except (ValueError, IndexError):
                return None
        return None

    @staticmethod
    def _angle_of(value):
        m = PrayerCalculator._eval_minutes(value)
        if m is not None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    # ------------------------------------------- خطوط العرض العالية

    @staticmethod
    def _time_diff(t1, t2):
        return _fixhour(t2 - t1)

    def _night_portion(self, angle, night):
        mode = self.params.get("highLats", "NightMiddle")
        if mode == "AngleBased":
            return (1.0 / 60.0) * (angle or 18.0) * night
        if mode == "OneSeventh":
            return night / 7.0
        return night / 2.0  # NightMiddle

    def _adjust_hl(self, t, base, angle, night, ccw=False):
        portion = self._night_portion(angle, night)
        if t is None:
            return base - portion if ccw else base + portion
        diff = self._time_diff(t, base) if ccw else self._time_diff(base, t)
        if diff > portion:
            return base - portion if ccw else base + portion
        return t

    # ---------------------------------------------------- عام

    def times_for(self, day, tz_offset):
        """يرجع dict بأسماء الصلوات وقيمها كسور ساعة محلية.

        day: كائن date
        tz_offset: إزاحة المنطقة الزمنية بالساعات لذلك اليوم (يشمل التوقيت الصيفي)
        """
        self._jdate = julian_date(day.year, day.month, day.day) - self.lng / (15.0 * 24.0)

        fajr_angle = self._angle_of(self.params.get("fajr", 18.0)) or 18.0
        isha_angle = self._angle_of(self.params.get("isha", 17.0))
        imsak_angle = self._angle_of(self.params.get("imsak"))
        maghrib_angle = self._angle_of(self.params.get("maghrib"))

        # تخمين ابتدائي (كسور يوم) ثم تكرار للتنقيح.
        # القيمة None تعني أن الشمس لم تبلغ تلك الزاوية — نُبقي التخمين السابق
        # ونعالجها لاحقاً في قسم خطوط العرض العالية.
        t = {"imsak": 5 / 24, "fajr": 5 / 24, "sunrise": 6 / 24, "dhuhr": 12 / 24,
             "asr": 13 / 24, "sunset": 18 / 24, "maghrib": 18 / 24, "isha": 18 / 24}
        unresolved = set()

        for _ in range(3):
            rs = self._rise_set_angle()
            computed = {
                "imsak": self._sun_angle_time(imsak_angle or fajr_angle,
                                              t["imsak"], ccw=True),
                "fajr": self._sun_angle_time(fajr_angle, t["fajr"], ccw=True),
                "sunrise": self._sun_angle_time(rs, t["sunrise"], ccw=True),
                "dhuhr": self._mid_day(t["dhuhr"]),
                "asr": self._asr_time(self._asr_factor(), t["asr"]),
                "sunset": self._sun_angle_time(rs, t["sunset"]),
                "maghrib": self._sun_angle_time(maghrib_angle, t["maghrib"])
                           if maghrib_angle else None,
                "isha": self._sun_angle_time(isha_angle, t["isha"])
                        if isha_angle else None,
            }
            unresolved = {k for k, v in computed.items() if v is None}
            t = {k: (v / 24.0 if v is not None else t[k])
                 for k, v in computed.items()}

        times = {k: v * 24.0 for k, v in t.items()}
        # ما لم يُحسب فعلياً يصبح None ليعالجه ما بعده
        for k in unresolved:
            if k in ("maghrib", "isha") and (maghrib_angle is None or isha_angle is None):
                continue  # ستُشتق من الغروب بقاعدة الدقائق
            times[k] = None

        # نقل الأوقات من UTC-النسبي إلى التوقيت المحلي
        shift = tz_offset - self.lng / 15.0
        for k in list(times):
            if times[k] is not None:
                times[k] = times[k] + shift

        # في الليل أو النهار القطبي لا وجود لشروق/غروب فعليّين، ولا تبلغ
        # الشمس زاوية العصر أحياناً. عندها نلجأ إلى «تقسيم اليوم نسبياً»:
        # يوم افتراضي طوله ١٢ ساعة حول الظهر، والعصر جزء نسبي منه.
        # هذا اجتهاد حسابي لا بديل عنه فلكياً، ويقتصر أثره على ما فوق
        # الدائرة القطبية تقريباً (٦٦°+).
        degenerate = times.get("sunrise") is None or times.get("sunset") is None
        if times.get("sunrise") is None:
            times["sunrise"] = times["dhuhr"] - 6.0
        if times.get("sunset") is None:
            times["sunset"] = times["dhuhr"] + 6.0
        if times.get("asr") is None:
            fraction = 5.0 / 6.0 if self._asr_factor() == 2.0 else 2.0 / 3.0
            times["asr"] = times["dhuhr"] + \
                (times["sunset"] - times["dhuhr"]) * fraction

        # تعديل خطوط العرض العالية قبل تطبيق قواعد «الدقائق»
        if self.params.get("highLats", "NightMiddle") != "None":
            sunrise, sunset = times.get("sunrise"), times.get("sunset")
            if sunrise is not None and sunset is not None:
                night = self._time_diff(sunset, sunrise)
                times["imsak"] = self._adjust_hl(
                    times["imsak"], sunrise, imsak_angle or fajr_angle, night, ccw=True)
                times["fajr"] = self._adjust_hl(
                    times["fajr"], sunrise, fajr_angle, night, ccw=True)
                if isha_angle:
                    times["isha"] = self._adjust_hl(
                        times["isha"], sunset, isha_angle, night)
                if maghrib_angle:
                    times["maghrib"] = self._adjust_hl(
                        times["maghrib"], sunset, maghrib_angle, night)

        # القواعد المعتمدة على الدقائق
        imsak_min = self._eval_minutes(self.params.get("imsak"))
        if imsak_min is not None and times.get("fajr") is not None:
            times["imsak"] = times["fajr"] - imsak_min / 60.0

        maghrib_min = self._eval_minutes(self.params.get("maghrib"))
        if maghrib_min is not None or times.get("maghrib") is None:
            times["maghrib"] = times["sunset"] + (maghrib_min or 0.0) / 60.0

        isha_min = self._eval_minutes(self.params.get("isha"))
        if isha_min is not None or times.get("isha") is None:
            times["isha"] = times["maghrib"] + (isha_min or 90.0) / 60.0

        dhuhr_min = self._eval_minutes(self.params.get("dhuhr")) or 0.0
        times["dhuhr"] = times["dhuhr"] + dhuhr_min / 60.0

        # منتصف الليل الشرعي — الجعفري ينتهي بالفجر، والجمهور بالشروق.
        # الفجر قد يكون None إذا عُطّلت معالجة خطوط العرض العالية.
        jafari = str(self.params.get("midnight")) == "Jafari"
        end_of_night = times.get("fajr") if jafari else times.get("sunrise")
        if end_of_night is None:
            end_of_night = times.get("sunrise")
        times["midnight"] = times["sunset"] + \
            self._time_diff(times["sunset"], end_of_night) / 2.0

        # في الحالة القطبية قد يسبق العصرُ المحسوبُ فلكياً غروبَنا الافتراضي،
        # فنفرض الترتيب المنطقي حتى لا يظهر جدول متناقض للمستخدم.
        if degenerate:
            order = ["fajr", "sunrise", "dhuhr", "asr", "sunset", "maghrib", "isha"]
            known = [k for k in order if times.get(k) is not None]
            for earlier, later in zip(known, known[1:]):
                if times[later] < times[earlier]:
                    times[later] = times[earlier]

        # التعديل اليدوي بالدقائق
        for k, minutes in self.offsets.items():
            if minutes and times.get(k) is not None:
                times[k] = times[k] + float(minutes) / 60.0

        # حارس أخير: لا ينبغي أن يصل None إلى هنا، لكن قيمة مفقودة يجب
        # ألا تُسقط البرنامج — نتركها None ليعرضها الواجهة كـ «—».
        return {k: (_fixhour(v) if v is not None else None)
                for k, v in times.items()}

    def datetimes_for(self, day, tzname):
        """نفس times_for لكن يرجع كائنات datetime واعية بالمنطقة الزمنية."""
        tz = ZoneInfo(tzname)
        # إزاحة المنطقة الزمنية عند ظهر ذلك اليوم (تتعامل مع التوقيت الصيفي)
        noon = datetime(day.year, day.month, day.day, 12, 0, tzinfo=tz)
        tz_offset = noon.utcoffset().total_seconds() / 3600.0

        times = self.times_for(day, tz_offset)
        out = {}
        midnight = datetime(day.year, day.month, day.day, 0, 0, tzinfo=tz)
        for name, hours in times.items():
            if hours is None:
                out[name] = None
                continue
            dt = midnight + timedelta(hours=hours)
            # منتصف الليل والعشاء المتأخر قد يقعان بعد منتصف الليل
            if name in ("midnight",) and hours < 12:
                dt = dt + timedelta(days=1)
            out[name] = dt.replace(second=0, microsecond=0)
        return out


def next_prayer(calc, tzname, now=None):
    """يرجع (اسم_الصلاة, وقتها) لأقرب صلاة قادمة، باحثاً في اليوم التالي عند اللزوم."""
    tz = ZoneInfo(tzname)
    now = now or datetime.now(tz)
    today = now.date()

    for offset in (0, 1):
        day = today + timedelta(days=offset)
        times = calc.datetimes_for(day, tzname)
        for name in PRAYERS:
            t = times.get(name)
            if t is not None and t > now:
                return name, t
    return None, None
