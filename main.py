from fastapi import FastAPI, File, UploadFile, Response
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

app = FastAPI()

# Función para configurar Selenium con Chrome en Render
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Importante para servidores
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())  # Instalar automáticamente ChromeDriver
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
    
    time.sleep(3)  # Esperar a que carguen los elementos (optimizable con WebDriverWait)
    
    productos = driver.find_elements(By.CSS_SELECTOR, ".product__item")  # Selector de productos
    
    resultados = []
    for producto in productos[:5]:  # Tomar solo los primeros 5 resultados
        try:
            titulo = producto.find_element(By.CSS_SELECTOR, ".product__item-title").text
            precio = producto.find_element(By.CSS_SELECTOR, ".price").text
            resultados.append({"nombre": titulo, "precio": precio})
        except Exception as e:
            print(f"Error obteniendo datos de producto: {e}")
    
    driver.quit()
    return {"productos": resultados}
