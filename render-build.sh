#!/bin/bash

# Instalar dependencias básicas
apt-get update && apt-get install -y wget curl unzip 

# Instalar Google Chrome
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt install -y ./google-chrome-stable_current_amd64.deb

# Verificar instalación de Chrome
google-chrome --version

# Instalar ChromeDriver compatible con la versión de Chrome
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1)
LATEST_DRIVER=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -q "https://chromedriver.storage.googleapis.com/$LATEST_DRIVER/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip -d /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

# Verificar instalación de ChromeDriver
chromedriver --version
