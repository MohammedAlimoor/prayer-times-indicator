"""تحويل التاريخ الميلادي إلى هجري (التقويم الجدولي الكويتي) مع إزاحة قابلة للضبط.

هذا تقويم حسابي تقريبي وقد يختلف عن الرؤية الشرعية بيوم أو يومين،
لذلك يوفّر البرنامج خيار «تعديل التاريخ الهجري» في الإعدادات.
"""

HIJRI_MONTHS_AR = [
    "محرم", "صفر", "ربيع الأول", "ربيع الآخر", "جمادى الأولى", "جمادى الآخرة",
    "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة",
]

WEEKDAYS_AR = [
    "الاثنين", "الثلاثاء", "الأربعاء", "الخميس",
    "الجمعة", "السبت", "الأحد",
]

GREGORIAN_MONTHS_AR = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
]


def _gregorian_to_jd(year, month, day):
    if month < 3:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + (a // 4)
    return (int(365.25 * (year + 4716)) + int(30.6001 * (month + 1))
            + day + b - 1524)


def _jd_to_hijri(jd):
    lj = jd - 1948440 + 10632
    n = (lj - 1) // 10631
    lj = lj - 10631 * n + 354
    j = (((10985 - lj) // 5316) * ((50 * lj) // 17719)
         + (lj // 5670) * ((43 * lj) // 15238))
    lj = (lj - ((30 - j) // 15) * ((17719 * j) // 50)
          - (j // 16) * ((15238 * j) // 43) + 29)
    month = (24 * lj) // 709
    day = lj - (709 * month) // 24
    year = 30 * n + j - 30
    return year, month, day


def to_hijri(g_date, offset_days=0):
    """يرجع (سنة, شهر, يوم) هجري. offset_days يعدّل النتيجة يدوياً."""
    jd = _gregorian_to_jd(g_date.year, g_date.month, g_date.day) + int(offset_days)
    return _jd_to_hijri(jd)


def format_hijri(g_date, offset_days=0):
    """مثال: «١٥ رمضان ١٤٤٧ هـ» بصيغة عربية مقروءة."""
    y, m, d = to_hijri(g_date, offset_days)
    month_name = HIJRI_MONTHS_AR[max(0, min(11, m - 1))]
    return f"{d} {month_name} {y} هـ"


def format_gregorian(g_date):
    weekday = WEEKDAYS_AR[g_date.weekday()]
    month = GREGORIAN_MONTHS_AR[g_date.month - 1]
    return f"{weekday} {g_date.day} {month} {g_date.year}"


def is_ramadan(g_date, offset_days=0):
    return to_hijri(g_date, offset_days)[1] == 9
