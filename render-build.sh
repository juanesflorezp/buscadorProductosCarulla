#!/bin/bash
echo "📦 Instalando Chromium y ChromeDriver..."

# Descargar Chromium (si no está preinstalado)
if [ ! -f /opt/chrome/chrome ]; then
    mkdir -p /opt/chrome
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O /opt/chrome/chrome.deb
    dpkg -x /opt/chrome/chrome.deb /opt/chrome/
fi

# Descargar ChromeDriver
mkdir -p /opt/chromedriver
wget https://chromedriver.storage.googleapis.com/$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip -O /opt/chromedriver/chromedriver.zip
unzip /opt/chromedriver/chromedriver.zip -d /opt/chromedriver/
chmod +x /opt/chromedriver/chromedriver

echo "✅ Instalación completada"
