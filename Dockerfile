FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y wget unzip gnupg && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN wget -q https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/ && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver_linux64.zip

RUN pip install --upgrade pip && \
    pip install numpy==1.24.4 && \
    pip install -r requirements.txt

ENV PORT=10000
CMD exec gunicorn --bind 0.0.0.0:$PORT --timeout 120 main:app
