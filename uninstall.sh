#!/usr/bin/env bash
# إزالة «أوقات الصلاة». مرّر --purge لحذف الإعدادات أيضاً.
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local}"

echo "==> إيقاف البرنامج إن كان يعمل"
pkill -x prayer-times 2>/dev/null || true
ps -eo pid,cmd --no-headers | grep -E "python3 [^ ]*prayer-times/run\.py" | grep -v grep \
  | awk '{print $1}' | xargs -r kill 2>/dev/null || true

echo "==> حذف الملفات"
rm -rf  "$PREFIX/share/prayer-times"
rm -f   "$PREFIX/bin/prayer-times"
rm -f   "$PREFIX/share/icons/hicolor/scalable/apps/prayer-times.svg"
rm -f   "$PREFIX/share/applications/prayer-times.desktop"
rm -f   "${XDG_CONFIG_HOME:-$HOME/.config}/autostart/prayer-times.desktop"
gtk-update-icon-cache -f -t "$PREFIX/share/icons/hicolor" 2>/dev/null || true

if [ "${1:-}" = "--purge" ]; then
  rm -rf "${XDG_CONFIG_HOME:-$HOME/.config}/prayer-times"
  echo "==> حُذفت الإعدادات أيضاً"
else
  echo "==> أُبقيت الإعدادات في ${XDG_CONFIG_HOME:-$HOME/.config}/prayer-times"
  echo "    لحذفها: $0 --purge"
fi
echo "==> تمت الإزالة."
