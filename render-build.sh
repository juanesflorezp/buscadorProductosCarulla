#!/bin/bash
set -e

echo "📦 Instalando Chromium..."
apt-get update && apt-get install -y chromium

echo "📦 Instalando ChromeDriver..."
CHROME_VERSION=$(curl -sL https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
curl -fsSL "https://chromedriver.storage.googleapis.com/${CHROME_VERSION}/chromedriver_linux64.zip" -o chromedriver.zip
unzip chromedriver.zip
mv chromedriver /opt/render/project/chromedriver
chmod +x /opt/render/project/chromedriver

echo "✅ Instalación completada."
