#!/bin/bash

echo "📦 Instalando Chromium y ChromeDriver..."

# Descargar Chromium portátil en la carpeta del proyecto
mkdir -p chrome
curl -SL https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.128/linux64/chrome-linux64.zip -o chrome/chrome.zip
unzip chrome/chrome.zip -d chrome
chmod +x chrome/chrome-linux64/chrome

# Descargar ChromeDriver portátil en la carpeta del proyecto
mkdir -p chromedriver
curl -SL https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.128/linux64/chromedriver-linux64.zip -o chromedriver/chromedriver.zip
unzip chromedriver/chromedriver.zip -d chromedriver
chmod +x chromedriver/chromedriver-linux64/chromedriver

echo "✅ Instalación completada"

# Instalar dependencias con Poetry
poetry install --no-dev

# Ejecutar la API con Uvicorn
poetry run uvicorn main:app --host 0.0.0.0 --port 10000
