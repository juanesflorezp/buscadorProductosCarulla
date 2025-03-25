# Usa una imagen base con Python
FROM python:3.9-slim

# Actualizamos el sistema e instalamos Chromium
RUN apt-get update && \
    apt-get install -y chromium chromium-driver

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos los archivos de nuestra aplicación al contenedor
COPY . /app

# Instalamos las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Exponemos el puerto para la aplicación FastAPI
EXPOSE 8000

# Comando para ejecutar FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
