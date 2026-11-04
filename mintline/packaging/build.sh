#!/usr/bin/env bash
# Builds the two downloads into mintline/dist/:
#   Mintline.zip            the app, with "Open Mintline.bat" for Windows
#   Mintline-extension.zip  the Chrome extension (Load unpacked)
set -euo pipefail
cd "$(dirname "$0")/.."
APP_FILES=(index.html styles.css indicators.js engine.js app.js tools.js icons)
rm -rf dist && mkdir -p dist/Mintline dist/Mintline-extension
cp -r "${APP_FILES[@]}" dist/Mintline/
cp packaging/windows/* dist/Mintline/
cp -r "${APP_FILES[@]}" dist/Mintline-extension/
cp packaging/extension/* dist/Mintline-extension/
# Neither package is served from a web address, so drop the web-app manifest link.
sed -i '/rel="manifest"/d' dist/Mintline/index.html dist/Mintline-extension/index.html
(cd dist && zip -qr Mintline.zip Mintline && zip -qr Mintline-extension.zip Mintline-extension)
echo "Built dist/Mintline.zip and dist/Mintline-extension.zip"
