#!/bin/bash

# Instalar Google Chrome
echo "📦 Instalando Google Chrome..."
wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i google-chrome.deb || apt-get -f install -y
rm google-chrome.deb

# Instalar ChromeDriver
echo "📦 Instalando ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION)
wget -q -O chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver.zip
mv chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver
rm chromedriver.zip

echo "✅ Instalación de Chrome y ChromeDriver completada."
