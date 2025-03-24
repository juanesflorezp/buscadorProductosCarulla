#!/bin/bash
set -e

echo "📦 Descargando Chromium..."
mkdir -p /opt/render/project/chrome
curl -fsSL https://github.com/macchrome/linux-snapshots/releases/download/v118.0.5993.70-r1161727/chrome-linux.zip -o chrome-linux.zip
unzip chrome-linux.zip -d /opt/render/project/chrome
mv /opt/render/project/chrome/chrome-linux /opt/render/project/chrome/chromium

echo "📦 Instalando ChromeDriver..."
CHROMEDRIVER_VERSION=$(curl -sL https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
curl -fsSL "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -o chromedriver.zip
unzip chromedriver.zip
mv chromedriver /opt/render/project/chromedriver
chmod +x /opt/render/project/chromedriver

echo "✅ Instalación completada."
