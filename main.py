from fastapi import FastAPI
import shutil
import subprocess

app = FastAPI()

@app.get("/chromedriver-path/")
def get_chromedriver_path():
    chromedriver_path = shutil.which("chromedriver")
    if chromedriver_path:
        return {"chromedriver_path": chromedriver_path}
    else:
        return {"error": "Chromedriver no encontrado en el sistema"}
