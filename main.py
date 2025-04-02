import os
from flask import Flask, request, send_file, jsonify
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
from random import uniform

app = Flask(__name__)

def configure_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    try:
        # Usa webdriver-manager para evitar rutas fijas
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=chrome_options
        )
        return driver
    except Exception as e:
        raise RuntimeError(f"Error al iniciar Chrome: {str(e)}")

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """Endpoint principal con mejor manejo de errores y tiempo de respuesta"""
    try:
        # Validación del archivo
        if 'file' not in request.files:
            return jsonify({"error": "No se envió archivo"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nombre de archivo vacío"}), 400

        try:
            df = pd.read_excel(file)
            if "Cód. Barras" not in df.columns:
                return jsonify({"error": "El archivo debe contener columna 'Cód. Barras'"}), 400
        except Exception as e:
            return jsonify({"error": f"Error al leer archivo: {str(e)}"}), 400

        # Limitar cantidad de productos para evitar timeout
        if len(df) > 10:
            return jsonify({"error": "Máximo 10 productos por request (límite de Render)"}), 400

        df["Descripción_Carulla"] = None
        df["Precio_Carulla"] = None
        
        try:
            driver = configure_selenium()
            driver.get('https://www.carulla.com')
            time.sleep(2)

            for index, row in df.iterrows():
                codigo = str(row["Cód. Barras"]).strip()
                try:
                    # Búsqueda con timeout reducido
                    search = WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']"))
                    )
                    search.clear()
                    search.send_keys(codigo + Keys.ENTER)
                    time.sleep(uniform(1.0, 2.5))  # Delay aleatorio

                    # Extracción de datos con selectores robustos
                    nombre = WebDriverWait(driver, 8).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "h3[itemprop='name'], h3[data-testid='product-title']"))
                    ).text
                    precio = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "span[itemprop='price'], span[data-testid='product-price']"))
                    ).text

                    df.at[index, "Descripción_Carulla"] = nombre
                    df.at[index, "Precio_Carulla"] = precio

                except (NoSuchElementException, TimeoutException):
                    df.at[index, "Descripción_Carulla"] = "No encontrado"
                    df.at[index, "Precio_Carulla"] = "No encontrado"
                
                time.sleep(uniform(1.0, 3.0))  # Delay aleatorio anti-bloqueo

            # Generación segura del Excel
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
            return jsonify({"error": f"Error durante el scraping: {str(e)}"}), 500

        finally:
            if 'driver' in locals():
                driver.quit()

    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@app.route('/')
def home():
    return "API Scraping Carulla - Enviar POST a /api/scrape con archivo Excel (Máx. 10 productos)"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
