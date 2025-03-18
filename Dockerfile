# Usar una imagen de Python con Chrome y Selenium preinstalados
FROM python:3.9

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl unzip wget \
    && rm -rf /var/lib/apt/lists/*

# Instalar librerías necesarias
RUN pip install --no-cache-dir streamlit pandas selenium webdriver-manager

# Copiar todos los archivos del repo al contenedor
WORKDIR /app
COPY . .

# Ejecutar la aplicación con Streamlit
CMD ["streamlit", "run", "ScraperCarulla.py", "--server.port=8501", "--server.address=0.0.0.0"]
