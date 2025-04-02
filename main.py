import os
from flask import Flask, request, jsonify, send_file
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import io
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def configure_selenium():
    """Configuración inteligente para Render y desarrollo local"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Configuración específica para Render
    if os.environ.get('RENDER'):
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service(executable_path="/usr/bin/chromedriver")
    else:  # Configuración para desarrollo local
        service = Service(ChromeDriverManager().install())
        chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """Endpoint principal para scraping"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No se proporcionó archivo"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nombre de archivo vacío"}), 400

        # Procesar archivo Excel
        try:
            df = pd.read_excel(file)
            if "Cód. Barras" not in df.columns:
                return jsonify({"error": "El archivo debe contener columna 'Cód. Barras'"}), 400
        except Exception as e:
            return jsonify({"error": f"Error al leer el archivo: {str(e)}"}), 400

        # Configurar scraping
        df["Descripción_Carulla"] = None
        df["Precio_Carulla"] = None
        driver = configure_selenium()

        try:
            driver.get('https://www.carulla.com')
            time.sleep(2)  # Espera inicial

            for index, row in df.iterrows():
                codigo = str(row["Cód. Barras"]).strip()
                try:
                    # Búsqueda del producto
                    search = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']"))
                    )
                    search.clear()
                    search.send_keys(codigo + Keys.ENTER)
                    time.sleep(2)

                    # Extraer datos
                    nombre = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h3.product-name"))
                    ).text
                    precio = driver.find_element(By.CSS_SELECTOR, "span.price").text

                    df.at[index, "Descripción_Carulla"] = nombre
                    df.at[index, "Precio_Carulla"] = precio

                except (NoSuchElementException, TimeoutException):
                    df.at[index, "Descripción_Carulla"] = "No encontrado"
                    df.at[index, "Precio_Carulla"] = "No encontrado"
                
                time.sleep(1.5)  # Delay anti-bloqueo

            # Generar respuesta
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='resultados_carulla.xlsx'
            )

        except Exception as e:
            return jsonify({"error": f"Error en scraping: {str(e)}"}), 500

        finally:
            driver.quit()

    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route('/')
def home():
    return """
    <h1>API Scraping Carulla</h1>
    <p>Envía un POST a /api/scrape con un archivo Excel que contenga códigos de barras</p>
    <form action="/api/scrape" method="post" enctype="multipart/form-data">
      <input type="file" name="file" accept=".xlsx, .xls">
      <button type="submit">Procesar</button>
    </form>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
