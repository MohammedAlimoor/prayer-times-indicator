"""قاعدة مدن مدمجة للبحث السريع.

كل مدينة صف من ستة عناصر:
(عربي, إنجليزي, خط العرض, خط الطول, المنطقة الزمنية, الطريقة المقترحة).
"""

CITIES = [
    # ---------------------------------------------------- الأردن
    ("عمّان", "Amman", 31.9539, 35.9106, "Asia/Amman", "Jordan"),
    ("الزرقاء", "Zarqa", 32.0728, 36.0880, "Asia/Amman", "Jordan"),
    ("إربد", "Irbid", 32.5556, 35.8500, "Asia/Amman", "Jordan"),
    ("العقبة", "Aqaba", 29.5320, 35.0063, "Asia/Amman", "Jordan"),
    ("الكرك", "Karak", 31.1850, 35.7047, "Asia/Amman", "Jordan"),
    ("مادبا", "Madaba", 31.7160, 35.7930, "Asia/Amman", "Jordan"),
    ("السلط", "Salt", 32.0392, 35.7272, "Asia/Amman", "Jordan"),
    ("المفرق", "Mafraq", 32.3430, 36.2080, "Asia/Amman", "Jordan"),
    ("معان", "Ma'an", 30.1962, 35.7340, "Asia/Amman", "Jordan"),

    # ---------------------------------------------------- السعودية
    ("مكة المكرمة", "Mecca", 21.3891, 39.8579, "Asia/Riyadh", "Makkah"),
    ("المدينة المنورة", "Medina", 24.5247, 39.5692, "Asia/Riyadh", "Makkah"),
    ("الرياض", "Riyadh", 24.7136, 46.6753, "Asia/Riyadh", "Makkah"),
    ("جدة", "Jeddah", 21.4858, 39.1925, "Asia/Riyadh", "Makkah"),
    ("الدمام", "Dammam", 26.3927, 49.9777, "Asia/Riyadh", "Makkah"),
    ("الخبر", "Khobar", 26.2794, 50.2083, "Asia/Riyadh", "Makkah"),
    ("الطائف", "Taif", 21.2703, 40.4158, "Asia/Riyadh", "Makkah"),
    ("تبوك", "Tabuk", 28.3835, 36.5662, "Asia/Riyadh", "Makkah"),
    ("أبها", "Abha", 18.2465, 42.5117, "Asia/Riyadh", "Makkah"),
    ("بريدة", "Buraydah", 26.3260, 43.9750, "Asia/Riyadh", "Makkah"),
    ("حائل", "Hail", 27.5114, 41.7208, "Asia/Riyadh", "Makkah"),
    ("نجران", "Najran", 17.4917, 44.1322, "Asia/Riyadh", "Makkah"),
    ("جازان", "Jazan", 16.8892, 42.5511, "Asia/Riyadh", "Makkah"),
    ("الأحساء", "Al Ahsa", 25.3833, 49.5833, "Asia/Riyadh", "Makkah"),
    ("ينبع", "Yanbu", 24.0895, 38.0618, "Asia/Riyadh", "Makkah"),
    ("الجبيل", "Jubail", 27.0046, 49.6460, "Asia/Riyadh", "Makkah"),

    # ---------------------------------------------------- فلسطين
    ("القدس", "Jerusalem", 31.7683, 35.2137, "Asia/Hebron", "Egypt"),
    ("غزة", "Gaza", 31.5017, 34.4668, "Asia/Hebron", "Egypt"),
    ("رام الله", "Ramallah", 31.9038, 35.2034, "Asia/Hebron", "Egypt"),
    ("نابلس", "Nablus", 32.2211, 35.2544, "Asia/Hebron", "Egypt"),
    ("الخليل", "Hebron", 31.5326, 35.0998, "Asia/Hebron", "Egypt"),
    ("بيت لحم", "Bethlehem", 31.7054, 35.2024, "Asia/Hebron", "Egypt"),
    ("جنين", "Jenin", 32.4597, 35.2956, "Asia/Hebron", "Egypt"),
    ("حيفا", "Haifa", 32.7940, 34.9896, "Asia/Hebron", "Egypt"),
    ("يافا", "Jaffa", 32.0553, 34.7500, "Asia/Hebron", "Egypt"),

    # ---------------------------------------------------- مصر
    ("القاهرة", "Cairo", 30.0444, 31.2357, "Africa/Cairo", "Egypt"),
    ("الإسكندرية", "Alexandria", 31.2001, 29.9187, "Africa/Cairo", "Egypt"),
    ("الجيزة", "Giza", 30.0131, 31.2089, "Africa/Cairo", "Egypt"),
    ("بورسعيد", "Port Said", 31.2653, 32.3019, "Africa/Cairo", "Egypt"),
    ("السويس", "Suez", 29.9668, 32.5498, "Africa/Cairo", "Egypt"),
    ("الأقصر", "Luxor", 25.6872, 32.6396, "Africa/Cairo", "Egypt"),
    ("أسوان", "Aswan", 24.0889, 32.8998, "Africa/Cairo", "Egypt"),
    ("المنصورة", "Mansoura", 31.0409, 31.3785, "Africa/Cairo", "Egypt"),
    ("طنطا", "Tanta", 30.7865, 31.0004, "Africa/Cairo", "Egypt"),
    ("أسيوط", "Asyut", 27.1783, 31.1859, "Africa/Cairo", "Egypt"),

    # ---------------------------------------------------- الخليج
    ("دبي", "Dubai", 25.2048, 55.2708, "Asia/Dubai", "Gulf"),
    ("أبوظبي", "Abu Dhabi", 24.4539, 54.3773, "Asia/Dubai", "Gulf"),
    ("الشارقة", "Sharjah", 25.3463, 55.4209, "Asia/Dubai", "Gulf"),
    ("العين", "Al Ain", 24.1302, 55.8023, "Asia/Dubai", "Gulf"),
    ("عجمان", "Ajman", 25.4052, 55.5136, "Asia/Dubai", "Gulf"),
    ("رأس الخيمة", "Ras Al Khaimah", 25.7895, 55.9432, "Asia/Dubai", "Gulf"),
    ("الدوحة", "Doha", 25.2854, 51.5310, "Asia/Qatar", "Qatar"),
    ("الكويت", "Kuwait City", 29.3759, 47.9774, "Asia/Kuwait", "Kuwait"),
    ("المنامة", "Manama", 26.2285, 50.5860, "Asia/Bahrain", "Gulf"),
    ("مسقط", "Muscat", 23.5880, 58.3829, "Asia/Muscat", "Gulf"),
    ("صلالة", "Salalah", 17.0151, 54.0924, "Asia/Muscat", "Gulf"),

    # ---------------------------------------------------- الشام والعراق
    ("دمشق", "Damascus", 33.5138, 36.2765, "Asia/Damascus", "MWL"),
    ("حلب", "Aleppo", 36.2021, 37.1343, "Asia/Damascus", "MWL"),
    ("حمص", "Homs", 34.7324, 36.7137, "Asia/Damascus", "MWL"),
    ("اللاذقية", "Latakia", 35.5317, 35.7915, "Asia/Damascus", "MWL"),
    ("بيروت", "Beirut", 33.8938, 35.5018, "Asia/Beirut", "MWL"),
    ("طرابلس (لبنان)", "Tripoli Lebanon", 34.4367, 35.8497, "Asia/Beirut", "MWL"),
    ("بغداد", "Baghdad", 33.3152, 44.3661, "Asia/Baghdad", "MWL"),
    ("البصرة", "Basra", 30.5085, 47.7804, "Asia/Baghdad", "MWL"),
    ("الموصل", "Mosul", 36.3350, 43.1189, "Asia/Baghdad", "MWL"),
    ("أربيل", "Erbil", 36.1901, 44.0091, "Asia/Baghdad", "MWL"),
    ("النجف", "Najaf", 32.0000, 44.3350, "Asia/Baghdad", "Jafari"),
    ("كربلاء", "Karbala", 32.6160, 44.0249, "Asia/Baghdad", "Jafari"),

    # ---------------------------------------------------- شمال أفريقيا
    ("طرابلس (ليبيا)", "Tripoli Libya", 32.8872, 13.1913, "Africa/Tripoli", "MWL"),
    ("بنغازي", "Benghazi", 32.1167, 20.0667, "Africa/Tripoli", "MWL"),
    ("تونس", "Tunis", 36.8065, 10.1815, "Africa/Tunis", "Tunisia"),
    ("صفاقس", "Sfax", 34.7406, 10.7603, "Africa/Tunis", "Tunisia"),
    ("الجزائر", "Algiers", 36.7538, 3.0588, "Africa/Algiers", "Algeria"),
    ("وهران", "Oran", 35.6971, -0.6308, "Africa/Algiers", "Algeria"),
    ("قسنطينة", "Constantine", 36.3650, 6.6147, "Africa/Algiers", "Algeria"),
    ("الرباط", "Rabat", 34.0209, -6.8416, "Africa/Casablanca", "Morocco"),
    ("الدار البيضاء", "Casablanca", 33.5731, -7.5898, "Africa/Casablanca", "Morocco"),
    ("مراكش", "Marrakesh", 31.6295, -7.9811, "Africa/Casablanca", "Morocco"),
    ("فاس", "Fez", 34.0181, -5.0078, "Africa/Casablanca", "Morocco"),
    ("طنجة", "Tangier", 35.7595, -5.8340, "Africa/Casablanca", "Morocco"),
    ("نواكشوط", "Nouakchott", 18.0735, -15.9582, "Africa/Nouakchott", "MWL"),
    ("الخرطوم", "Khartoum", 15.5007, 32.5599, "Africa/Khartoum", "Egypt"),

    # ---------------------------------------------------- بقية العالم الإسلامي
    ("صنعاء", "Sanaa", 15.3694, 44.1910, "Asia/Aden", "MWL"),
    ("عدن", "Aden", 12.7855, 45.0187, "Asia/Aden", "MWL"),
    ("مقديشو", "Mogadishu", 2.0469, 45.3182, "Africa/Mogadishu", "MWL"),
    ("إسطنبول", "Istanbul", 41.0082, 28.9784, "Europe/Istanbul", "Turkey"),
    ("أنقرة", "Ankara", 39.9334, 32.8597, "Europe/Istanbul", "Turkey"),
    ("طهران", "Tehran", 35.6892, 51.3890, "Asia/Tehran", "Tehran"),
    ("كراتشي", "Karachi", 24.8607, 67.0011, "Asia/Karachi", "Karachi"),
    ("لاهور", "Lahore", 31.5204, 74.3587, "Asia/Karachi", "Karachi"),
    ("إسلام آباد", "Islamabad", 33.6844, 73.0479, "Asia/Karachi", "Karachi"),
    ("كابول", "Kabul", 34.5553, 69.2075, "Asia/Kabul", "Karachi"),
    ("دكا", "Dhaka", 23.8103, 90.4125, "Asia/Dhaka", "Karachi"),
    ("دلهي", "Delhi", 28.7041, 77.1025, "Asia/Kolkata", "Karachi"),
    ("مومباي", "Mumbai", 19.0760, 72.8777, "Asia/Kolkata", "Karachi"),
    ("حيدر آباد", "Hyderabad", 17.3850, 78.4867, "Asia/Kolkata", "Karachi"),
    ("جاكرتا", "Jakarta", -6.2088, 106.8456, "Asia/Jakarta", "Indonesia"),
    ("كوالالمبور", "Kuala Lumpur", 3.1390, 101.6869, "Asia/Kuala_Lumpur", "Singapore"),
    ("سنغافورة", "Singapore", 1.3521, 103.8198, "Asia/Singapore", "Singapore"),
    ("طشقند", "Tashkent", 41.2995, 69.2401, "Asia/Tashkent", "Russia"),
    ("باكو", "Baku", 40.4093, 49.8671, "Asia/Baku", "Russia"),
    ("ألماتي", "Almaty", 43.2220, 76.8512, "Asia/Almaty", "Russia"),

    # ---------------------------------------------------- أوروبا وأمريكا
    ("لندن", "London", 51.5074, -0.1278, "Europe/London", "MWL"),
    ("مانشستر", "Manchester", 53.4808, -2.2426, "Europe/London", "MWL"),
    ("برمنغهام", "Birmingham", 52.4862, -1.8904, "Europe/London", "MWL"),
    ("باريس", "Paris", 48.8566, 2.3522, "Europe/Paris", "MWL"),
    ("مارسيليا", "Marseille", 43.2965, 5.3698, "Europe/Paris", "MWL"),
    ("برلين", "Berlin", 52.5200, 13.4050, "Europe/Berlin", "MWL"),
    ("ميونخ", "Munich", 48.1351, 11.5820, "Europe/Berlin", "MWL"),
    ("فرانكفورت", "Frankfurt", 50.1109, 8.6821, "Europe/Berlin", "MWL"),
    ("أمستردام", "Amsterdam", 52.3676, 4.9041, "Europe/Amsterdam", "MWL"),
    ("بروكسل", "Brussels", 50.8503, 4.3517, "Europe/Brussels", "MWL"),
    ("مدريد", "Madrid", 40.4168, -3.7038, "Europe/Madrid", "MWL"),
    ("برشلونة", "Barcelona", 41.3851, 2.1734, "Europe/Madrid", "MWL"),
    ("روما", "Rome", 41.9028, 12.4964, "Europe/Rome", "MWL"),
    ("ميلانو", "Milan", 45.4642, 9.1900, "Europe/Rome", "MWL"),
    ("ستوكهولم", "Stockholm", 59.3293, 18.0686, "Europe/Stockholm", "MWL"),
    ("أوسلو", "Oslo", 59.9139, 10.7522, "Europe/Oslo", "MWL"),
    ("كوبنهاغن", "Copenhagen", 55.6761, 12.5683, "Europe/Copenhagen", "MWL"),
    ("فيينا", "Vienna", 48.2082, 16.3738, "Europe/Vienna", "MWL"),
    ("زيورخ", "Zurich", 47.3769, 8.5417, "Europe/Zurich", "MWL"),
    ("موسكو", "Moscow", 55.7558, 37.6173, "Europe/Moscow", "Russia"),
    ("سراييفو", "Sarajevo", 43.8563, 18.4131, "Europe/Sarajevo", "MWL"),
    ("نيويورك", "New York", 40.7128, -74.0060, "America/New_York", "ISNA"),
    ("شيكاغو", "Chicago", 41.8781, -87.6298, "America/Chicago", "ISNA"),
    ("ديترويت", "Detroit", 42.3314, -83.0458, "America/Detroit", "ISNA"),
    ("هيوستن", "Houston", 29.7604, -95.3698, "America/Chicago", "ISNA"),
    ("لوس أنجلوس", "Los Angeles", 34.0522, -118.2437, "America/Los_Angeles", "ISNA"),
    ("تورونتو", "Toronto", 43.6532, -79.3832, "America/Toronto", "ISNA"),
    ("مونتريال", "Montreal", 45.5017, -73.5673, "America/Toronto", "ISNA"),
    ("سيدني", "Sydney", -33.8688, 151.2093, "Australia/Sydney", "MWL"),
    ("ملبورن", "Melbourne", -37.8136, 144.9631, "Australia/Melbourne", "MWL"),
]


def _norm(text):
    """تطبيع عربي: توحيد الألف والهاء/التاء المربوطة وحذف التشكيل."""
    text = (text or "").strip().lower()
    for src, dst in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"),
                     ("ة", "ه"), ("ؤ", "و"), ("ئ", "ي"), ("ـ", "")):
        text = text.replace(src, dst)
    return "".join(c for c in text if not ("ً" <= c <= "ْ"))


def search(query, limit=40):
    """يبحث بالعربي أو الإنجليزي. يرجع قائمة صفوف المدن."""
    q = _norm(query)
    if not q:
        return CITIES[:limit]

    starts, contains = [], []
    for row in CITIES:
        ar, en = _norm(row[0]), _norm(row[1])
        if ar.startswith(q) or en.startswith(q):
            starts.append(row)
        elif q in ar or q in en:
            contains.append(row)
    return (starts + contains)[:limit]


def find(name_ar):
    for row in CITIES:
        if row[0] == name_ar:
            return row
    return None
