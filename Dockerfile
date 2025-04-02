FROM python:3.9-slim

# 1. Instala dependencias del sistema (incluyendo curl)
RUN apt-get update && \
    apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# 2. Instala dependencias de Python
RUN pip install --upgrade pip && \
    pip install numpy==1.24.4 && \
    pip install -r requirements.txt

# 3. Instala ChromeDriver (versión compatible con el Chrome instalado)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1) && \
    wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}" -O LATEST_RELEASE && \
    wget -q "https://chromedriver.storage.googleapis.com/$(cat LATEST_RELEASE)/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/ && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver_linux64.zip LATEST_RELEASE

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:$PORT", "--timeout", "120"]
