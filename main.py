from fastapi import FastAPI, File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import time
import tempfile
import os
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def kill_existing_chrome():
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if 'chrome' in proc.info['name'].lower():
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/procesar-excel/")
async def procesar_archivo(file: UploadFile = File(...)):
    driver = None
    try:
        contents = await file.read()
        df_original = pd.read_excel(io.BytesIO(contents), 
            usecols=[0, 1, 2, 3, 4, 5, 6], 
            names=["Descripción", "Cód. Barras", "Referencia", "CONSULTA", "NETO", "LINEA", "PROVEEDOR"], 
            skiprows=1
        )

        if df_original.empty:
            return {"error": "El archivo Excel está vacío o tiene un formato incorrecto"}

        row_count = len(df_original)
        print(f"📊 Cantidad de filas en el archivo: {row_count}")
        
        df = df_original.copy()
        df["Descripción_Carulla"] = None
        df["Precio_Carulla"] = None

        # Configuración del navegador Chromium
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")  
        chrome_options.add_argument("--disable-dev-shm-usage")  
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")  # Ahora el navegador es sin interfaz gráfica
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--timeout=180")
        
        # Eliminar procesos previos de Chrome
        kill_existing_chrome()
        
        # Ubicación de Chromium
        chromium_path = "/usr/bin/chromium"
        chrome_options.binary_location = chromium_path

        # Inicializar el WebDriver sin conflictos
        try:
            service = Service("/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print(f"✅ Chromium cargado correctamente desde: {chromium_path}")
        except WebDriverException as e:
            print(f"❌ Error al iniciar WebDriver: {e}")
            return {"error": "No se pudo iniciar el WebDriver"}

        driver.get('https://www.carulla.com')
        time.sleep(5)

        for index, row in df.iterrows():
            codigo_barras = str(row["Cód. Barras"]).strip()
            print(f"🔍 Buscando código de barras: {codigo_barras}")

            try:
                search_field = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/header/section/div/div[1]/div[2]/form/input'))
                )
                search_field.clear()
                search_field.send_keys(codigo_barras)  
                search_field.send_keys(Keys.ENTER)
                time.sleep(5)

                product = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/a/div/h3'))
                )
                
                articlename_element = driver.find_element(By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/a/div/h3')
                prices_element = driver.find_element(By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/div/div/div[2]/p')

                df.at[index, "Descripción_Carulla"] = articlename_element.text
                df.at[index, "Precio_Carulla"] = prices_element.text

            except TimeoutException:
                df.at[index, "Descripción_Carulla"] = "No encontrado"
                df.at[index, "Precio_Carulla"] = "No encontrado"
            except Exception as e:
                df.at[index, "Descripción_Carulla"] = "Error"
                df.at[index, "Precio_Carulla"] = "Error"
                print(f"⚠️ Error en la búsqueda: {e}")

        driver.quit()
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Resultados')
        output.seek(0)
        
        return {
            "row_count": row_count,
            "download_url": "/descargar-excel/"
        }

    except Exception as e:
        if driver:
            driver.quit()
        return {"error": str(e)}

@app.get("/descargar-excel/")
def descargar_excel():
    output = io.BytesIO()
    df = pd.DataFrame({"Mensaje": ["Archivo generado correctamente"]})
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    output.seek(0)
    
    headers = {
        "Content-Disposition": "attachment; filename=resultado_carulla.xlsx",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    return Response(content=output.getvalue(), headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
