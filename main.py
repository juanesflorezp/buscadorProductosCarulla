import os
from flask import Flask, request, send_file
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

app = Flask(__name__)

def configure_selenium():
    """Configuración optimizada para Render"""
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(15)
    return driver

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """Endpoint principal para scraping"""
    try:
        if 'file' not in request.files:
            return {"error": "No se envió archivo"}, 400

        file = request.files['file']
        if file.filename == '':
            return {"error": "Nombre de archivo vacío"}, 400

        # Procesar archivo
        try:
            df = pd.read_excel(file)
            if "Cód. Barras" not in df.columns:
                return {"error": "El archivo debe contener columna 'Cód. Barras'"}, 400
        except Exception as e:
            return {"error": f"Error al leer archivo: {str(e)}"}, 400

        # Configurar resultados
        df["Descripción_Carulla"] = None
        df["Precio_Carulla"] = None
        driver = configure_selenium()

        try:
            driver.get('https://www.carulla.com')
            time.sleep(2)

            for index, row in df.iterrows():
                codigo = str(row["Cód. Barras"]).strip()
                try:
                    # Búsqueda
                    search = WebDriverWait(driver, 13).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']"))
                    )
                    search.clear()
                    search.send_keys(codigo + Keys.ENTER)
                    time.sleep(1.5)

                    # Extraer datos (selectores actualizados Oct 2023)
                    nombre = WebDriverWait(driver, 13).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h3[data-testid='product-title']"))
                    ).text
                    precio = driver.find_element(
                        By.CSS_SELECTOR, "span[data-testid='product-price']"
                    ).text

                    df.at[index, "Descripción_Carulla"] = nombre
                    df.at[index, "Precio_Carulla"] = precio

                except (NoSuchElementException, TimeoutException):
                    df.at[index, "Descripción_Carulla"] = "No encontrado"
                    df.at[index, "Precio_Carulla"] = "No encontrado"
                
                time.sleep(1)  # Delay anti-bloqueo

            # Generar Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)

            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='resultados_carulla.xlsx'
            )

        except Exception as e:
            return {"error": f"Error en scraping: {str(e)}"}, 500

        finally:
            driver.quit()

    except Exception as e:
        return {"error": f"Error interno: {str(e)}"}, 500

@app.route('/')
def home():
    return "API Scraping Carulla - Enviar POST a /api/scrape con archivo Excel"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
