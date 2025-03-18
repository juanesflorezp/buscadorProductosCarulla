from fastapi import FastAPI, UploadFile, File
import pandas as pd
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

app = FastAPI()

def buscar_productos(df):
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.carulla.com")

    for index, row in df.iterrows():
        codigo_barras = str(row["Cód. Barras"]).strip()

        try:
            search_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/header/section/div/div[1]/div[2]/form/input'))
            )
            search_field.clear()
            search_field.send_keys(codigo_barras)
            search_field.send_keys(Keys.ENTER)
            time.sleep(2)

            articlename_element = WebDriverWait(driver, 22).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/a/div/h3'))
            )
            prices_element = driver.find_element(By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/div/div/div[2]/p')

            df.at[index, "Descripción_Carulla"] = articlename_element.text
            df.at[index, "Precio_Carulla"] = prices_element.text

        except Exception:
            df.at[index, "Descripción_Carulla"] = "No encontrado"
            df.at[index, "Precio_Carulla"] = "No encontrado"

    driver.quit()
    return df

@app.post("/buscar_productos/")
async def process_file(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))
    df_resultado = buscar_productos(df)
    return df_resultado.to_dict(orient="records")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
