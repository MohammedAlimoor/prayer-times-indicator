"""نافذة الإعدادات — تُستخدم كمعالج أول تشغيل وكلوحة تحكم لاحقاً."""

import gi

gi.require_version("Gtk", "3.0")
from zoneinfo import available_timezones  # noqa: E402

from gi.repository import Gdk, GLib, Gtk  # noqa: E402

from . import cities, config  # noqa: E402
from .calc import ASR_METHODS, HIGH_LAT_METHODS, METHODS, PRAYER_NAMES_AR, PRAYERS  # noqa: E402

CSS = b"""
.pt-title  { font-size: 15pt; font-weight: bold; }
.pt-hint   { font-size: 9pt; opacity: 0.68; }
.pt-section{ font-weight: bold; margin-top: 6px; }
"""


def _apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


class SettingsWindow(Gtk.Window):
    """لوحة الإعدادات. on_saved تُستدعى بعد الحفظ بالإعدادات الجديدة."""

    def __init__(self, cfg, on_saved=None, first_run=False):
        super().__init__(title="إعدادات أوقات الصلاة")
        self.cfg = dict(cfg)
        self.cfg["offsets"] = dict(cfg.get("offsets", {}))
        self.cfg["notify_prayers"] = dict(cfg.get("notify_prayers", {}))
        self.on_saved = on_saved
        self.first_run = first_run

        _apply_css()
        self.set_default_size(660, 720)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("prayer-times")

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(outer)

        if first_run:
            outer.pack_start(self._welcome_banner(), False, False, 0)

        self.notebook = Gtk.Notebook()
        self.notebook.set_margin_top(8)
        self.notebook.set_margin_bottom(4)
        self.notebook.set_margin_start(10)
        self.notebook.set_margin_end(10)
        outer.pack_start(self.notebook, True, True, 0)

        self.notebook.append_page(self._page_location(), Gtk.Label(label="الموقع"))
        self.notebook.append_page(self._page_calculation(), Gtk.Label(label="الحساب"))
        self.notebook.append_page(self._page_adjustments(), Gtk.Label(label="تعديل الأوقات"))
        self.notebook.append_page(self._page_alerts(), Gtk.Label(label="التنبيهات"))
        self.notebook.append_page(self._page_display(), Gtk.Label(label="العرض"))

        outer.pack_start(self._action_bar(), False, False, 0)
        self.notebook.set_current_page(0)
        self.connect("key-press-event", self._on_key)

    # ------------------------------------------------------ رأس المعالج

    def _welcome_banner(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        title = Gtk.Label(label="أهلاً بك 👋")
        title.get_style_context().add_class("pt-title")
        title.set_xalign(1.0)

        hint = Gtk.Label(
            label="اختر مدينتك وطريقة الحساب، ثم اضغط «حفظ». "
                  "تقدر تغيّر أي إعداد لاحقاً من قائمة الشريط العلوي ← الإعدادات.")
        hint.get_style_context().add_class("pt-hint")
        hint.set_xalign(1.0)
        hint.set_line_wrap(True)

        box.pack_start(title, False, False, 0)
        box.pack_start(hint, False, False, 0)
        return box

    # ------------------------------------------------------ أدوات مساعدة

    @staticmethod
    def _grid():
        g = Gtk.Grid(column_spacing=12, row_spacing=10)
        g.set_margin_top(14)
        g.set_margin_bottom(14)
        g.set_margin_start(14)
        g.set_margin_end(14)
        return g

    @staticmethod
    def _label(text, bold=False):
        lbl = Gtk.Label(label=text)
        lbl.set_xalign(1.0)
        if bold:
            lbl.get_style_context().add_class("pt-section")
        return lbl

    @staticmethod
    def _hint(text):
        lbl = Gtk.Label(label=text)
        lbl.get_style_context().add_class("pt-hint")
        lbl.set_xalign(1.0)
        lbl.set_line_wrap(True)
        return lbl

    @staticmethod
    def _scrolled(child):
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(child)
        return sw

    # ------------------------------------------------------ صفحة الموقع

    def _page_location(self):
        grid = self._grid()
        row = 0

        grid.attach(self._label("ابحث عن مدينتك:"), 0, row, 1, 1)
        self.city_search = Gtk.SearchEntry()
        self.city_search.set_placeholder_text("اكتب اسم المدينة بالعربي أو الإنجليزي…")
        self.city_search.connect("search-changed", self._on_city_search)
        self.city_search.set_hexpand(True)
        grid.attach(self.city_search, 1, row, 2, 1)
        row += 1

        # قائمة نتائج البحث
        self.city_store = Gtk.ListStore(str, str, float, float, str, str)
        self.city_view = Gtk.TreeView(model=self.city_store)
        self.city_view.set_headers_visible(True)
        for i, title in enumerate(("المدينة", "English")):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_expand(True)
            self.city_view.append_column(col)
        tz_col = Gtk.TreeViewColumn("المنطقة الزمنية", Gtk.CellRendererText(), text=4)
        self.city_view.append_column(tz_col)
        self.city_view.get_selection().connect("changed", self._on_city_selected)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_min_content_height(180)
        sw.add(self.city_view)
        grid.attach(sw, 0, row, 3, 1)
        row += 1

        grid.attach(self._label("أو أدخل الإحداثيات يدوياً", bold=True), 0, row, 3, 1)
        row += 1

        grid.attach(self._label("خط العرض:"), 0, row, 1, 1)
        self.lat_spin = Gtk.SpinButton.new_with_range(-90.0, 90.0, 0.0001)
        self.lat_spin.set_digits(4)
        self.lat_spin.set_value(float(self.cfg.get("latitude", 0.0)))
        self.lat_spin.set_hexpand(True)
        grid.attach(self.lat_spin, 1, row, 2, 1)
        row += 1

        grid.attach(self._label("خط الطول:"), 0, row, 1, 1)
        self.lng_spin = Gtk.SpinButton.new_with_range(-180.0, 180.0, 0.0001)
        self.lng_spin.set_digits(4)
        self.lng_spin.set_value(float(self.cfg.get("longitude", 0.0)))
        self.lng_spin.set_hexpand(True)
        grid.attach(self.lng_spin, 1, row, 2, 1)
        row += 1

        grid.attach(self._label("الارتفاع (متر):"), 0, row, 1, 1)
        self.elev_spin = Gtk.SpinButton.new_with_range(-500.0, 9000.0, 1.0)
        self.elev_spin.set_value(float(self.cfg.get("elevation", 0.0)))
        self.elev_spin.set_hexpand(True)
        grid.attach(self.elev_spin, 1, row, 2, 1)
        row += 1

        grid.attach(self._label("المنطقة الزمنية:"), 0, row, 1, 1)
        self.tz_combo = Gtk.ComboBoxText.new_with_entry()
        completion_store = Gtk.ListStore(str)
        self._tz_list = sorted(available_timezones())
        for tz in self._tz_list:
            self.tz_combo.append_text(tz)
            completion_store.append([tz])
        completion = Gtk.EntryCompletion()
        completion.set_model(completion_store)
        completion.set_text_column(0)
        completion.set_inline_completion(True)
        self.tz_combo.get_child().set_completion(completion)
        self.tz_combo.get_child().set_text(self.cfg.get("timezone", "Asia/Riyadh"))
        self.tz_combo.set_hexpand(True)
        grid.attach(self.tz_combo, 1, row, 2, 1)
        row += 1

        grid.attach(self._hint(
            "اختيار مدينة من القائمة يملأ الإحداثيات والمنطقة الزمنية "
            "وطريقة الحساب المناسبة تلقائياً."), 0, row, 3, 1)

        self._refresh_cities("")
        self._select_saved_city()
        return self._scrolled(grid)

    def _select_saved_city(self):
        """يحدّد المدينة المحفوظة في القائمة الكاملة ويمرّر إليها."""
        saved = self.cfg.get("city", "")
        if not saved:
            return
        for i, row in enumerate(self.city_store):
            if row[0] == saved:
                path = Gtk.TreePath.new_from_indices([i])
                self.city_view.get_selection().select_path(path)
                # التمرير يحتاج أن تكون الشجرة معروضة فعلاً
                GLib.idle_add(self.city_view.scroll_to_cell, path, None, True, 0.5, 0.0)
                self._selected_city = saved
                break

    def _refresh_cities(self, query=""):
        self.city_store.clear()
        for row in cities.search(query):
            self.city_store.append(list(row))

    def _on_city_search(self, entry):
        self._refresh_cities(entry.get_text())

    def _on_city_selected(self, selection):
        model, it = selection.get_selected()
        if it is None:
            return
        self.lat_spin.set_value(model[it][2])
        self.lng_spin.set_value(model[it][3])
        self.tz_combo.get_child().set_text(model[it][4])
        self._selected_city = model[it][0]

        # اقتراح طريقة الحساب المناسبة للبلد
        # (صفحة الحساب تُبنى بعد صفحة الموقع، فنتحقق من وجودها)
        suggested = model[it][5]
        if hasattr(self, "method_combo") and suggested in self._method_keys:
            self.method_combo.set_active(self._method_keys.index(suggested))

    # ------------------------------------------------------ صفحة الحساب

    def _page_calculation(self):
        grid = self._grid()
        row = 0

        grid.attach(self._label("طريقة الحساب:"), 0, row, 1, 1)
        self.method_combo = Gtk.ComboBoxText()
        self._method_keys = list(METHODS.keys())
        for key in self._method_keys:
            self.method_combo.append_text(METHODS[key]["name"])
        current = self.cfg.get("method", "Makkah")
        self.method_combo.set_active(
            self._method_keys.index(current) if current in self._method_keys else 0)
        self.method_combo.connect("changed", self._on_method_changed)
        grid.attach(self.method_combo, 1, row, 1, 1)
        row += 1

        self.method_detail = self._hint("")
        grid.attach(self.method_detail, 0, row, 2, 1)
        row += 1

        grid.attach(self._label("مذهب العصر:"), 0, row, 1, 1)
        self.asr_combo = Gtk.ComboBoxText()
        self._asr_keys = list(ASR_METHODS.keys())
        for key in self._asr_keys:
            self.asr_combo.append_text(ASR_METHODS[key])
        asr = self.cfg.get("asr", "Standard")
        self.asr_combo.set_active(
            self._asr_keys.index(asr) if asr in self._asr_keys else 0)
        grid.attach(self.asr_combo, 1, row, 1, 1)
        row += 1

        grid.attach(self._label("خطوط العرض العالية:"), 0, row, 1, 1)
        self.hl_combo = Gtk.ComboBoxText()
        self._hl_keys = list(HIGH_LAT_METHODS.keys())
        for key in self._hl_keys:
            self.hl_combo.append_text(HIGH_LAT_METHODS[key])
        hl = self.cfg.get("high_lats", "NightMiddle")
        self.hl_combo.set_active(
            self._hl_keys.index(hl) if hl in self._hl_keys else 1)
        grid.attach(self.hl_combo, 1, row, 1, 1)
        row += 1

        grid.attach(self._hint(
            "يُستخدم فقط في البلاد البعيدة عن خط الاستواء حيث لا يغيب "
            "الشفق صيفاً (مثل شمال أوروبا)."), 0, row, 2, 1)
        row += 1

        grid.attach(self._label("تعديل التاريخ الهجري:"), 0, row, 1, 1)
        self.hijri_spin = Gtk.SpinButton.new_with_range(-3, 3, 1)
        self.hijri_spin.set_value(int(self.cfg.get("hijri_offset", 0)))
        grid.attach(self.hijri_spin, 1, row, 1, 1)
        row += 1

        grid.attach(self._hint(
            "التاريخ الهجري محسوب فلكياً وقد يختلف عن الرؤية الشرعية بيوم؛ "
            "عدّله بالزائد أو الناقص ليطابق التقويم المعتمد عندك."), 0, row, 2, 1)

        self._on_method_changed(self.method_combo)
        return self._scrolled(grid)

    def _on_method_changed(self, combo):
        idx = combo.get_active()
        if idx < 0:
            return
        params = METHODS[self._method_keys[idx]]["params"]
        fajr = params.get("fajr", "—")
        isha = params.get("isha", "—")
        isha_txt = f"{isha} دقيقة بعد المغرب" if isinstance(isha, str) else f"زاوية {isha}°"
        self.method_detail.set_text(f"الفجر: زاوية {fajr}°   •   العشاء: {isha_txt}")

    # ------------------------------------------------ صفحة تعديل الأوقات

    def _page_adjustments(self):
        grid = self._grid()
        row = 0

        grid.attach(self._label("تعديل يدوي لكل صلاة (بالدقائق)", bold=True), 0, row, 2, 1)
        row += 1
        grid.attach(self._hint(
            "لمطابقة توقيت المسجد أو التقويم المحلي عندك. "
            "القيمة الموجبة تؤخّر الأذان والسالبة تقدّمه."), 0, row, 2, 1)
        row += 1

        self.offset_spins = {}
        offsets = self.cfg.get("offsets", {})
        for prayer in PRAYERS:
            grid.attach(self._label(PRAYER_NAMES_AR[prayer] + ":"), 0, row, 1, 1)
            spin = Gtk.SpinButton.new_with_range(-120, 120, 1)
            spin.set_value(int(offsets.get(prayer, 0)))
            self.offset_spins[prayer] = spin
            grid.attach(spin, 1, row, 1, 1)
            row += 1

        reset = Gtk.Button(label="تصفير كل التعديلات")
        reset.set_halign(Gtk.Align.START)
        reset.connect("clicked", self._on_reset_offsets)
        grid.attach(reset, 0, row, 2, 1)
        return self._scrolled(grid)

    def _on_reset_offsets(self, _button):
        for spin in self.offset_spins.values():
            spin.set_value(0)

    # ------------------------------------------------------ صفحة التنبيهات

    def _page_alerts(self):
        grid = self._grid()
        row = 0

        self.notify_check = Gtk.CheckButton(label="تفعيل التنبيهات")
        self.notify_check.set_active(bool(self.cfg.get("notify_enabled", True)))
        self.notify_check.connect("toggled", self._sync_alert_sensitivity)
        grid.attach(self.notify_check, 0, row, 2, 1)
        row += 1

        self.notify_at_check = Gtk.CheckButton(label="تنبيه عند دخول وقت الصلاة")
        self.notify_at_check.set_active(bool(self.cfg.get("notify_at_time", True)))
        grid.attach(self.notify_at_check, 0, row, 2, 1)
        row += 1

        grid.attach(self._label("تنبيه قبل الأذان بـ (دقيقة):"), 0, row, 1, 1)
        self.before_spin = Gtk.SpinButton.new_with_range(0, 60, 1)
        self.before_spin.set_value(int(self.cfg.get("notify_before_minutes", 10)))
        grid.attach(self.before_spin, 1, row, 1, 1)
        row += 1

        grid.attach(self._hint("اجعلها صفراً لإلغاء التنبيه المسبق."), 0, row, 2, 1)
        row += 1

        grid.attach(self._label("الصلوات المُنبَّه لها", bold=True), 0, row, 2, 1)
        row += 1

        prayers_box = Gtk.FlowBox()
        prayers_box.set_selection_mode(Gtk.SelectionMode.NONE)
        prayers_box.set_max_children_per_line(3)
        self.prayer_checks = {}
        enabled = self.cfg.get("notify_prayers", {})
        for prayer in PRAYERS:
            chk = Gtk.CheckButton(label=PRAYER_NAMES_AR[prayer])
            chk.set_active(bool(enabled.get(prayer, prayer != "sunrise")))
            self.prayer_checks[prayer] = chk
            prayers_box.add(chk)
        grid.attach(prayers_box, 0, row, 2, 1)
        row += 1

        grid.attach(self._label("الصوت", bold=True), 0, row, 2, 1)
        row += 1

        self.sound_check = Gtk.CheckButton(label="تشغيل صوت عند دخول الوقت")
        self.sound_check.set_active(bool(self.cfg.get("sound_enabled", False)))
        self.sound_check.connect("toggled", self._sync_alert_sensitivity)
        grid.attach(self.sound_check, 0, row, 2, 1)
        row += 1

        grid.attach(self._label("ملف الصوت:"), 0, row, 1, 1)
        sound_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.sound_entry = Gtk.Entry()
        self.sound_entry.set_text(self.cfg.get("sound_file", ""))
        self.sound_entry.set_placeholder_text("اتركه فارغاً لاستخدام نغمة النظام")
        self.sound_entry.set_hexpand(True)
        browse = Gtk.Button(label="اختيار…")
        browse.connect("clicked", self._on_browse_sound)
        preview = Gtk.Button(label="تجربة")
        preview.connect("clicked", self._on_preview_sound)
        sound_box.pack_start(self.sound_entry, True, True, 0)
        sound_box.pack_start(browse, False, False, 0)
        sound_box.pack_start(preview, False, False, 0)
        grid.attach(sound_box, 1, row, 1, 1)
        row += 1

        grid.attach(self._hint(
            "أي ملف صوتي (mp3 / ogg / wav). يُشغَّل عبر مشغّل النظام."), 0, row, 2, 1)

        self._sync_alert_sensitivity()
        return self._scrolled(grid)

    def _sync_alert_sensitivity(self, *_args):
        on = self.notify_check.get_active()
        for widget in (self.notify_at_check, self.before_spin):
            widget.set_sensitive(on)
        for chk in self.prayer_checks.values():
            chk.set_sensitive(on)
        sound_on = self.sound_check.get_active()
        self.sound_entry.set_sensitive(sound_on)

    def _on_browse_sound(self, _button):
        dialog = Gtk.FileChooserDialog(
            title="اختر ملف الأذان", parent=self,
            action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons("إلغاء", Gtk.ResponseType.CANCEL,
                           "اختيار", Gtk.ResponseType.OK)
        audio_filter = Gtk.FileFilter()
        audio_filter.set_name("ملفات صوتية")
        for pattern in ("*.mp3", "*.ogg", "*.wav", "*.oga", "*.m4a", "*.flac"):
            audio_filter.add_pattern(pattern)
        dialog.add_filter(audio_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            self.sound_entry.set_text(dialog.get_filename() or "")
        dialog.destroy()

    def _on_preview_sound(self, _button):
        from .sound import play
        play(self.sound_entry.get_text().strip())

    # ------------------------------------------------------ صفحة العرض

    def _page_display(self):
        grid = self._grid()
        row = 0

        grid.attach(self._label("الشريط العلوي", bold=True), 0, row, 2, 1)
        row += 1

        self.show_name_check = Gtk.CheckButton(label="عرض اسم الصلاة القادمة")
        self.show_name_check.set_active(bool(self.cfg.get("show_prayer_name", True)))
        grid.attach(self.show_name_check, 0, row, 2, 1)
        row += 1

        self.countdown_check = Gtk.CheckButton(
            label="عرض العدّاد التنازلي بدل وقت الصلاة")
        self.countdown_check.set_active(bool(self.cfg.get("show_countdown", True)))
        grid.attach(self.countdown_check, 0, row, 2, 1)
        row += 1

        self.format24_check = Gtk.CheckButton(label="نظام ٢٤ ساعة")
        self.format24_check.set_active(bool(self.cfg.get("time_format_24h", True)))
        grid.attach(self.format24_check, 0, row, 2, 1)
        row += 1

        self.arabic_num_check = Gtk.CheckButton(label="أرقام عربية-هندية (٠١٢٣)")
        self.arabic_num_check.set_active(bool(self.cfg.get("arabic_numerals", False)))
        grid.attach(self.arabic_num_check, 0, row, 2, 1)
        row += 1

        grid.attach(self._label("التشغيل", bold=True), 0, row, 2, 1)
        row += 1

        self.autostart_check = Gtk.CheckButton(
            label="تشغيل البرنامج تلقائياً عند بدء الجهاز")
        # أول تشغيل: الملف غير موجود بعد، فنعتمد القيمة الافتراضية
        self.autostart_check.set_active(
            bool(self.cfg.get("autostart", True)) if self.first_run
            else config.autostart_enabled())
        grid.attach(self.autostart_check, 0, row, 2, 1)
        row += 1

        grid.attach(self._hint(
            f"ملف الإعدادات: {config.CONFIG_PATH}"), 0, row, 2, 1)
        return self._scrolled(grid)

    # ------------------------------------------------------ شريط الأزرار

    def _action_bar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(6)
        box.set_margin_bottom(12)
        box.set_margin_start(14)
        box.set_margin_end(14)

        save = Gtk.Button(label="حفظ")
        save.get_style_context().add_class("suggested-action")
        save.connect("clicked", lambda *_: self._save())

        cancel = Gtk.Button(label="إغلاق بدون حفظ")
        cancel.connect("clicked", lambda *_: self.destroy())

        box.pack_end(save, False, False, 0)
        box.pack_end(cancel, False, False, 0)
        return box

    def _on_key(self, _widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False

    # ------------------------------------------------------ الحفظ

    def _collect(self):
        cfg = dict(self.cfg)

        cfg["latitude"] = round(self.lat_spin.get_value(), 6)
        cfg["longitude"] = round(self.lng_spin.get_value(), 6)
        cfg["elevation"] = round(self.elev_spin.get_value(), 1)
        cfg["timezone"] = self.tz_combo.get_child().get_text().strip()
        cfg["city"] = getattr(self, "_selected_city", self.cfg.get("city", ""))

        cfg["method"] = self._method_keys[max(0, self.method_combo.get_active())]
        cfg["asr"] = self._asr_keys[max(0, self.asr_combo.get_active())]
        cfg["high_lats"] = self._hl_keys[max(0, self.hl_combo.get_active())]
        cfg["hijri_offset"] = int(self.hijri_spin.get_value())

        cfg["offsets"] = {p: int(s.get_value()) for p, s in self.offset_spins.items()}

        cfg["notify_enabled"] = self.notify_check.get_active()
        cfg["notify_at_time"] = self.notify_at_check.get_active()
        cfg["notify_before_minutes"] = int(self.before_spin.get_value())
        cfg["notify_prayers"] = {p: c.get_active()
                                 for p, c in self.prayer_checks.items()}
        cfg["sound_enabled"] = self.sound_check.get_active()
        cfg["sound_file"] = self.sound_entry.get_text().strip()

        cfg["show_prayer_name"] = self.show_name_check.get_active()
        cfg["show_countdown"] = self.countdown_check.get_active()
        cfg["time_format_24h"] = self.format24_check.get_active()
        cfg["arabic_numerals"] = self.arabic_num_check.get_active()
        cfg["autostart"] = self.autostart_check.get_active()

        cfg["configured"] = True
        return cfg

    def _validate(self, cfg):
        if cfg["timezone"] not in self._tz_list:
            return f"المنطقة الزمنية «{cfg['timezone']}» غير معروفة."
        return None

    def _save(self):
        cfg = self._collect()
        error = self._validate(cfg)
        if error:
            dialog = Gtk.MessageDialog(
                transient_for=self, modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK, text=error)
            dialog.run()
            dialog.destroy()
            self.notebook.set_current_page(0)
            return

        config.save(cfg)
        config.set_autostart(cfg["autostart"])
        self.cfg = cfg

        if self.on_saved:
            GLib.idle_add(self.on_saved, cfg)
        self.destroy()
