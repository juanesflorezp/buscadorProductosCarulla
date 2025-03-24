#!/bin/bash
set -e

echo "📦 Instalando Chromium..."
apt-get update && apt-get install -y chromium-driver chromium

echo "📦 Instalando ChromeDriver..."
CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
curl -fsSL "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -o chromedriver.zip
unzip chromedriver.zip
mv chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver

echo "✅ Instalación completada."
