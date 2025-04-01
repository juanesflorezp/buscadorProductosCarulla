import os
from flask import Flask, request, jsonify, send_file
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import io
import tempfile

app = Flask(__name__)

def configure_selenium():
    """Configura Selenium para Render"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """Endpoint para scraping de Carulla"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No se proporcionó archivo"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nombre de archivo vacío"}), 400

        # Leer el archivo Excel
        df = pd.read_excel(file)
        df["Descripción_Carulla"] = None
        df["Precio_Carulla"] = None

        # Configurar Selenium
        driver = configure_selenium()
        driver.get('https://www.carulla.com')

        for index, row in df.iterrows():
            codigo_barras = str(row["Cód. Barras"]).strip()
            try:
                # Búsqueda en Carulla
                search_field = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//input[@type="search"]'))
                search_field.clear()
                search_field.send_keys(codigo_barras + Keys.ENTER)
                time.sleep(2)

                # Extraer datos
                nombre = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, '//h3[contains(@class, "product-name")]'))).text
                precio = driver.find_element(By.XPATH, '//span[contains(@class, "price")]').text

                df.at[index, "Descripción_Carulla"] = nombre
                df.at[index, "Precio_Carulla"] = precio

            except (NoSuchElementException, TimeoutException):
                df.at[index, "Descripción_Carulla"] = "No encontrado"
                df.at[index, "Precio_Carulla"] = "No encontrado"
            time.sleep(1)  # Delay entre búsquedas

        # Generar archivo de respuesta
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='resultados_carulla.xlsx'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'driver' in locals():
            driver.quit()

@app.route('/')
def home():
    return "API de Scraping Carulla - Envíe un POST a /api/scrape con un archivo Excel"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
