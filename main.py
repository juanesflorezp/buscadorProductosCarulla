from flask import Flask, request, jsonify, send_file
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import io
import tempfile
import os

app = Flask(__name__)

def configure_selenium():
    """Configura Selenium para funcionar en entorno server"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_carulla_data(excel_content):
    """Realiza el scraping de Carulla con los datos del Excel"""
    # Leer el Excel desde bytes
    df_original = pd.read_excel(io.BytesIO(excel_content),
                            usecols=[0, 1, 2, 3, 4, 5, 6],  
                            names=["Descripción", "Cód. Barras", "Referencia", "CONSULTA", "NETO", "LINEA", "PROVEEDOR"],  
                            skiprows=1)
    
    df = df_original.copy()
    df["Descripción_Carulla"] = None
    df["Precio_Carulla"] = None

    driver = configure_selenium()
    driver.get('https://www.carulla.com')

    try:
        for index, row in df.iterrows():
            codigo_barras = str(row["Cód. Barras"]).strip()
            print(f"🔍 Buscando código de barras: {codigo_barras}")

            try:
                search_field = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/header/section/div/div[1]/div[2]/form/input'))
                )
                search_field.clear()
                time.sleep(2)

                for _ in range(21):  
                    search_field.send_keys(Keys.BACKSPACE)
                    time.sleep(0.5)

                search_field.send_keys(codigo_barras)  
                search_field.send_keys(Keys.ENTER)
                time.sleep(1)

                product = WebDriverWait(driver, 22).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li[1]/article/div[1]/div[2]/a/div/p'))
                )
                time.sleep(1)

                articlename_element = driver.find_element(By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/a/div/h3')
                prices_element = driver.find_element(By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/div/div/div[2]/p')

                df.at[index, "Descripción_Carulla"] = articlename_element.text
                df.at[index, "Precio_Carulla"] = prices_element.text
                time.sleep(1)
                print(f"✅ Producto encontrado ({codigo_barras}): {articlename_element.text} | Precio: {prices_element.text}")

            except TimeoutException:
                print(f"❌ No se encontró el código de barras: {codigo_barras}")
                df.at[index, "Descripción_Carulla"] = "No encontrado"
                df.at[index, "Precio_Carulla"] = "No encontrado"

            except Exception as e:
                print(f"⚠️ Error al buscar '{codigo_barras}': {str(e)}")
                df.at[index, "Descripción_Carulla"] = "Error"
                df.at[index, "Precio_Carulla"] = "Error"

            time.sleep(2)

    finally:
        driver.quit()

    return df

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """Endpoint principal para el scraping"""
    if 'file' not in request.files:
        return jsonify({"error": "No se proporcionó archivo"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({"error": "Solo se aceptan archivos Excel (.xlsx)"}), 400

    try:
        # Procesar el archivo
        excel_content = file.read()
        result_df = scrape_carulla_data(excel_content)
        
        # Crear archivo temporal para la respuesta
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            result_df.to_excel(tmp.name, index=False)
            tmp.seek(0)
            return send_file(
                tmp.name,
                as_attachment=True,
                download_name='resultados_carulla.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Limpiar archivo temporal si existe
        if 'tmp' in locals() and os.path.exists(tmp.name):
            os.unlink(tmp.name)

@app.route('/')
def index():
    return """
    <h1>API de Scraping Carulla</h1>
    <p>Envía un archivo Excel via POST a /api/scrape</p>
    <form action="/api/scrape" method="post" enctype="multipart/form-data">
      <input type="file" name="file" accept=".xlsx">
      <button type="submit">Procesar</button>
    </form>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
