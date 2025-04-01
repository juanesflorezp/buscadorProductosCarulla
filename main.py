from fastapi import FastAPI, File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import psutil
import tempfile
import shutil
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchWindowException, NoSuchElementException
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
        if 'chrome' in proc.info['name'].lower() or 'chromedriver' in proc.info['name'].lower():
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/chromium-path/")
def get_chromium_paths():
    chromium_path = shutil.which("chromium") or "Not found"
    chromedriver_path = shutil.which("chromedriver") or "Not found"
    return {"chromium_path": chromium_path, "chromedriver_path": chromedriver_path}

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
        
        # Limpiar la columna "Cód. Barras" para que contenga solo números sin espacios
        df_original["Cód. Barras"] = df_original["Cód. Barras"].astype(str).str.replace(r'\D', '', regex=True)

        # Agregar columnas para los resultados de búsqueda
        df_original["Descripción_Carulla"] = None
        df_original["Precio_Carulla"] = None
        df_original["Encontrado"] = None  # Nueva columna para marcar productos encontrados

        chromium_path = shutil.which("chromium") or "/usr/bin/chromium"
        chromedriver_path = shutil.which("chromedriver") or "/usr/bin/chromedriver"
        print(f"🔍 Chromium Path: {chromium_path}")
        print(f"🔍 ChromeDriver Path: {chromedriver_path}")

        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")  
        chrome_options.add_argument("--disable-dev-shm-usage")  
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")  
        chrome_options.binary_location = chromium_path
        
        temp_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")

        kill_existing_chrome()
        
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"✅ ChromeDriver cargado correctamente desde: {chromedriver_path}")

        driver.get('https://www.carulla.com')
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/header/section/div/div[1]/div[2]/form/input'))
        )

        # Procesar los productos en el archivo Excel
        for index, row in df_original.iterrows():
            codigo_barras = str(row["Cód. Barras"]).strip()
            print(f"🔍 Buscando código de barras: {codigo_barras}")

            try:
                search_field = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/header/section/div/div[1]/div[2]/form/input'))
                )
                search_field.clear()
                search_field.send_keys(codigo_barras)  
                search_field.send_keys(Keys.ENTER)
                
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]'))
                )

                # Verificar si no se encuentra el producto
                no_results_xpath = '//*[contains(text(), "No encontramos")]'
                if len(driver.find_elements(By.XPATH, no_results_xpath)) > 0:
                    df_original.at[index, "Descripción_Carulla"] = "No encontrado"
                    df_original.at[index, "Precio_Carulla"] = "No encontrado"
                    df_original.at[index, "Encontrado"] = "❌"
                    continue

                articlename_element = driver.find_element(By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/a/div/h3')
                prices_element = driver.find_element(By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/div/div/div[2]/p')

                df_original.at[index, "Descripción_Carulla"] = articlename_element.text
                df_original.at[index, "Precio_Carulla"] = prices_element.text
                df_original.at[index, "Encontrado"] = "✅"  # Marcar como encontrado

            except (TimeoutException, NoSuchWindowException, NoSuchElementException):
                df_original.at[index, "Descripción_Carulla"] = "No encontrado"
                df_original.at[index, "Precio_Carulla"] = "No encontrado"
                df_original.at[index, "Encontrado"] = "❌"
            except Exception as e:
                df_original.at[index, "Descripción_Carulla"] = "Error"
                df_original.at[index, "Precio_Carulla"] = "Error"
                df_original.at[index, "Encontrado"] = "❌"
                print(f"⚠️ Error en la búsqueda: {e}")

        driver.quit()

        # Crear el archivo Excel con los resultados de búsqueda
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_original.to_excel(writer, index=False, sheet_name='Resultados')
        output.seek(0)

        # Regresar el archivo Excel con los resultados
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=resultado_carulla.xlsx"
            }
        )

    except Exception as e:
        if driver:
            driver.quit()
        return {"error": str(e)}
