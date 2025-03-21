# Usar una imagen base de Python
FROM python:3.9

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    wget \
    chromium \
    chromium-driver

# Configurar variables de entorno para Chrome y Selenium
ENV PATH="/usr/lib/chromium/:${PATH}"
ENV CHROME_BIN="/usr/lib/chromium/chrome"

# Crear directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Ejecutar la API con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
