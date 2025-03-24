#!/bin/bash
set -e

echo "📦 Instalando Google Chrome..."
curl -fsSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o google-chrome.deb
dpkg -x google-chrome.deb /tmp/google-chrome
mv /tmp/google-chrome/opt/google/chrome /opt/render/project/chrome

echo "📦 Instalando ChromeDriver..."
CHROME_VERSION=$(curl -sL https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
curl -fsSL "https://chromedriver.storage.googleapis.com/${CHROME_VERSION}/chromedriver_linux64.zip" -o chromedriver.zip
unzip chromedriver.zip
mv chromedriver /opt/render/project/chromedriver
chmod +x /opt/render/project/chromedriver

echo "✅ Instalación completada."
