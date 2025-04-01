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

        # Agregar columnas que se van a buscar
        df_original["Descripción_Carulla"] = None
        df_original["Precio_Carulla"] = None
        df_original["Encontrado"] = None  # Nueva columna para marcar productos encontrados

        # Crear el archivo Excel de respuesta
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_original.to_excel(writer, index=False, sheet_name='Datos a Buscar')
        output.seek(0)

        # Regresar el archivo Excel con los datos a buscar
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=datos_a_buscar.xlsx"
            }
        )

    except Exception as e:
        return {"error": str(e)}

