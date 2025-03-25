# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver

# Configurar las variables de entorno para Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH=$CHROME_BIN:$PATH
