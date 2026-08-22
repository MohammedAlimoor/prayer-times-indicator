#!/usr/bin/env bash
# Build prayer-times-indicator_<version>_all.deb into dist/.
#
#   packaging/build-deb.sh [output-dir]
#
# The package is architecture independent: pure Python plus PyGObject
# bindings that come from apt.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/dist}"

PKG="prayer-times-indicator"
VERSION="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$ROOT/prayertimes/__init__.py")"
MAINTAINER="Mohammed Alimoor <ameral.java@gmail.com>"

[ -n "$VERSION" ] || { echo "!! could not read __version__" >&2; exit 1; }

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

LIB="$STAGE/usr/lib/$PKG"
mkdir -p "$LIB" \
         "$STAGE/usr/bin" \
         "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/icons/hicolor/scalable/apps" \
         "$STAGE/usr/share/doc/$PKG" \
         "$STAGE/DEBIAN"

cp -r "$ROOT/prayertimes" "$LIB/"
cp "$ROOT/run.py" "$LIB/"
find "$LIB" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

cat > "$STAGE/usr/bin/prayer-times" <<'WRAP'
#!/usr/bin/env bash
exec python3 /usr/lib/prayer-times-indicator/run.py "$@"
WRAP
chmod 755 "$STAGE/usr/bin/prayer-times"

cp "$ROOT/data/prayer-times.svg" \
   "$STAGE/usr/share/icons/hicolor/scalable/apps/prayer-times.svg"

cat > "$STAGE/usr/share/applications/prayer-times.desktop" <<'DESK'
[Desktop Entry]
Type=Application
Name=أوقات الصلاة
Name[en]=Prayer Times
Comment=عرض أوقات الصلاة في الشريط العلوي
Comment[en]=Prayer times in the GNOME top bar
Exec=/usr/bin/prayer-times
Icon=prayer-times
Terminal=false
Categories=Utility;
StartupNotify=false
DESK

cp "$ROOT/LICENSE" "$STAGE/usr/share/doc/$PKG/copyright"

cat > "$STAGE/DEBIAN/control" <<CTRL
Package: $PKG
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.9), python3-gi, gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, gir1.2-notify-0.7
Recommends: gnome-shell-extension-appindicator
Maintainer: $MAINTAINER
Homepage: https://github.com/MohammedAlimoor/prayer-times-indicator
Description: Prayer times in the GNOME top bar
 A small tray indicator that shows the next prayer and the countdown to it,
 with the full day's schedule and a settings panel behind the icon.
 .
 Times are computed locally from the sun's position, so the program needs
 no internet connection and sends no data anywhere. 18 calculation methods,
 130+ built-in cities, per-prayer minute adjustments, pre-adhan notifications
 and an optional adhan sound are all supported.
CTRL

cat > "$STAGE/DEBIAN/postinst" <<'POST'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t /usr/share/icons/hicolor >/dev/null 2>&1 || true
    fi
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
    fi
fi
POST
chmod 755 "$STAGE/DEBIAN/postinst"

cat > "$STAGE/DEBIAN/postrm" <<'PRM'
#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
PRM
chmod 755 "$STAGE/DEBIAN/postrm"

find "$STAGE" -type d -exec chmod 755 {} +
find "$STAGE/usr/lib" "$STAGE/usr/share" -type f -exec chmod 644 {} +

mkdir -p "$OUT"
DEB="$OUT/${PKG}_${VERSION}_all.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$DEB" >/dev/null
# stable filename so release "latest/download" links never break
cp "$DEB" "$OUT/${PKG}.deb"

echo "$DEB"
