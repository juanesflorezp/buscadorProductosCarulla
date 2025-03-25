from fastapi import FastAPI, File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/procesar-excel/")
async def procesar_archivo(file: UploadFile = File(...)):
    driver = None  # Inicializamos driver como None por si no se puede crear
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

        # Configuración del navegador Chromium para Render
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Aquí estamos intentando usar la ubicación predeterminada de Chromium en el entorno Render
        chromium_path = shutil.which("chromium")
        if chromium_path:
            print(f"Chromium encontrado en: {chromium_path}")
            chrome_options.binary_location = chromium_path
        else:
            # Si no se encuentra, intentamos rutas comunes en entornos de contenedor
            chromium_binary_locations = [
                "/usr/bin/chromium-browser",
                "/usr/local/bin/chromium",
                "/opt/chromium/chrome"
            ]
            for path in chromium_binary_locations:
                try:
                    chrome_options.binary_location = path
                    # Intentamos iniciar el driver con la ruta configurada
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    print(f"Chromium cargado correctamente desde: {path}")
                    break
                except Exception as e:
                    print(f"Error al cargar desde {path}: {str(e)}")

        # Si driver sigue siendo None, significa que no se pudo iniciar Chromium
        if driver is None:
            return {"error": "No se pudo iniciar Chromium, verifique la configuración del entorno"}

        driver.get('https://www.carulla.com')

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
                    EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/a/div/h3'))
                )
                time.sleep(1)

                articlename_element = driver.find_element(By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/a/div/h3')
                prices_element = driver.find_element(By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/div/div/div[2]/p')

                df.at[index, "Descripción_Carulla"] = articlename_element.text
                df.at[index, "Precio_Carulla"] = prices_element.text
                time.sleep(1)

            except TimeoutException:
                df.at[index, "Descripción_Carulla"] = "No encontrado"
                df.at[index, "Precio_Carulla"] = "No encontrado"

            except Exception as e:
                df.at[index, "Descripción_Carulla"] = "Error"
                df.at[index, "Precio_Carulla"] = "Error"

            time.sleep(2)

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
