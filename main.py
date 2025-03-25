from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

app = FastAPI()

# Configuración para Selenium en Render
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
CHROME_BINARY_PATH = "/usr/bin/google-chrome"

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Modo sin interfaz gráfica
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = CHROME_BINARY_PATH  # Especificar la ruta de Chrome

    service = Service(CHROMEDRIVER_PATH)  # Usar ChromeDriver instalado manualmente
    driver = webdriver.Chrome(service=service, options=options)
    return driver

@app.get("/")
def read_root():
    return {"message": "API funcionando correctamente"}

@app.get("/buscar-producto/{nombre}")
def buscar_producto(nombre: str):
    driver = get_driver()
    url = f"https://www.carulla.com/catalogsearch/result/?q={nombre}"
    driver.get(url)

    try:
        # Esperar a que los productos estén visibles
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product__item"))
        )

        productos = driver.find_elements(By.CSS_SELECTOR, ".product__item")

        resultados = []
        for producto in productos[:5]:  # Tomar solo los primeros 5 resultados
            try:
                titulo = producto.find_element(By.CSS_SELECTOR, ".product__item-title").text
                precio = producto.find_element(By.CSS_SELECTOR, ".price").text
                resultados.append({"nombre": titulo, "precio": precio})
            except Exception:
                continue  # Si hay un error en un producto, pasar al siguiente

    except Exception as e:
        return {"error": f"Error al obtener productos: {str(e)}"}
    
    finally:
        driver.quit()  # Cerrar el navegador al final

    return {"productos": resultados}
