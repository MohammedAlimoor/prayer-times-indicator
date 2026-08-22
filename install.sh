#!/usr/bin/env bash
# تثبيت «أوقات الصلاة» للمستخدم الحالي (بدون sudo).
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PREFIX="${PREFIX:-$HOME/.local}"
LIB_DIR="$PREFIX/share/prayer-times"
BIN_DIR="$PREFIX/bin"
ICON_DIR="$PREFIX/share/icons/hicolor/scalable/apps"
DESKTOP_DIR="$PREFIX/share/applications"

echo "==> تثبيت أوقات الصلاة في $PREFIX"

# ١) التحقّق من المتطلبات
missing=()
python3 - <<'PY' 2>/dev/null || missing+=("python3-gi / gir1.2-gtk-3.0")
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
PY
python3 - <<'PY' 2>/dev/null || missing+=("gir1.2-ayatanaappindicator3-0.1")
import gi
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3
PY
python3 - <<'PY' 2>/dev/null || missing+=("gir1.2-notify-0.7")
import gi
gi.require_version("Notify", "0.7")
from gi.repository import Notify
PY

if [ ${#missing[@]} -gt 0 ]; then
  echo "!! حزم ناقصة: ${missing[*]}"
  echo "   ثبّتها بـ:"
  echo "   sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 gir1.2-notify-0.7"
  exit 1
fi

# ٢) نسخ ملفات البرنامج
rm -rf "$LIB_DIR"
mkdir -p "$LIB_DIR" "$BIN_DIR" "$ICON_DIR" "$DESKTOP_DIR"
cp -r "$SRC/prayertimes" "$LIB_DIR/"
cp "$SRC/run.py" "$LIB_DIR/"
find "$LIB_DIR" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

# ٣) سكربت التشغيل
cat > "$BIN_DIR/prayer-times" <<EOF
#!/usr/bin/env bash
exec python3 "$LIB_DIR/run.py" "\$@"
EOF
chmod +x "$BIN_DIR/prayer-times"

# ٤) الأيقونة
cp "$SRC/data/prayer-times.svg" "$ICON_DIR/prayer-times.svg"
gtk-update-icon-cache -f -t "$PREFIX/share/icons/hicolor" 2>/dev/null || true

# ٥) مُدخَل قائمة التطبيقات
cat > "$DESKTOP_DIR/prayer-times.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=أوقات الصلاة
Name[en]=Prayer Times
Comment=عرض أوقات الصلاة في الشريط العلوي
Comment[en]=Prayer times in the top bar
Exec=$BIN_DIR/prayer-times
Icon=prayer-times
Terminal=false
Categories=Utility;
StartupNotify=false
EOF
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

# ٦) إضافة الشريط العلوي مطلوبة لعرض الأيقونة في جنوم
if command -v gnome-extensions >/dev/null 2>&1; then
  if ! gnome-extensions list --enabled 2>/dev/null | grep -q "appindicator"; then
    echo "!! تنبيه: إضافة AppIndicator غير مفعّلة — الأيقونة لن تظهر."
    echo "   فعّلها بـ: gnome-extensions enable ubuntu-appindicators@ubuntu.com"
  fi
fi

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "!! $BIN_DIR ليس ضمن PATH — أضِفه إلى ~/.profile" ;;
esac

echo "==> تم التثبيت."
echo "    التشغيل الآن:  prayer-times"
echo "    الإزالة:       $SRC/uninstall.sh"
