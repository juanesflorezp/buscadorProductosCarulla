FROM python:3.9-slim

# Instalar dependencias del sistema para Selenium
RUN apt-get update && apt-get install -y \
    wget \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["./start.sh"]
