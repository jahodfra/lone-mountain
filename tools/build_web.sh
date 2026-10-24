#!/bin/sh
# Build the browser version with pygbag into build/web/ (serve it over https, or localhost).
#   tools/build_web.sh          # build only
#   tools/build_web.sh serve    # build and serve on http://localhost:8000
set -e
cd "$(dirname "$0")/.."
APP=build/hobbit
rm -rf "$APP"
mkdir -p "$APP"
cp web/main.py "$APP/"
cp -r hobbit "$APP/"
rm -rf "$APP/hobbit/__pycache__"
find "$APP" -name "._*" -delete     # macOS metadata files
if [ "$1" = "serve" ]; then
    exec python -m pygbag --ume_block 0 "$APP"
fi
python -m pygbag --build --ume_block 0 "$APP"
echo "built: $APP/build/web/"
