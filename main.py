from fastapi import FastAPI, File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

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
    try:
        # Leer el archivo Excel
        contents = await file.read()
        
        # Crear el DataFrame original a partir del archivo Excel
        df_original = pd.read_excel(io.BytesIO(contents), 
            usecols=[0, 1, 2, 3, 4, 5, 6], 
            names=["Descripción", "Cód. Barras", "Referencia", "CONSULTA", "NETO", "LINEA", "PROVEEDOR"], 
            skiprows=1
        )

        # Comprobar si el archivo está vacío
        if df_original.empty:
            return {"error": "El archivo Excel está vacío o tiene un formato incorrecto"}

        row_count = len(df_original)
        print(f"📊 Cantidad de filas en el archivo: {row_count}")

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
