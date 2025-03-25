from fastapi import FastAPI
import shutil

app = FastAPI()

@app.get("/ubicacion-chrome")
def obtener_ubicacion_chrome():
    # Intentamos encontrar la ubicación de Chrome o Chromium
    chrome_path = shutil.which("chrome")
    chromium_path = shutil.which("chromium")

    if chrome_path:
        return {"chrome": chrome_path}
    elif chromium_path:
        return {"chromium": chromium_path}
    else:
        return {"error": "No se pudo encontrar Chrome ni Chromium en el entorno."}
