 import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

# Configurar Streamlit
st.title("Buscador de Productos en Carulla")

# Subir archivo con códigos de barras
uploaded_file = st.file_uploader("Sube un archivo CSV con los códigos de barras", type=["csv", "xlsx"])

def buscar_productos(df):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    driver.get('https://www.carulla.com')
    
    for index, row in df.iterrows():
        codigo_barras = str(row["Código de Barras"]).strip()
        st.write(f"🔍 Buscando código de barras: {codigo_barras}")
        
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
            
            articlename_element = WebDriverWait(driver, 22).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/a/div/h3'))
            )
            prices_element = driver.find_element(By.XPATH, '//*[@id="__next"]/main/section[3]/div/div[2]/div[2]/div[2]/ul/li/article/div[1]/div[2]/div/div/div[2]/p')
            
            df.at[index, "Descripción_Carulla"] = articlename_element.text
            df.at[index, "Precio_Carulla"] = prices_element.text
            st.success(f"✅ Producto encontrado: {articlename_element.text} | Precio: {prices_element.text}")
        
        except Exception:
            st.error(f"❌ No se encontró el código: {codigo_barras}")
            df.at[index, "Descripción_Carulla"] = "No encontrado"
            df.at[index, "Precio_Carulla"] = "No encontrado"
        
        time.sleep(2)
    
    driver.quit()
    return df

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    st.dataframe(df.head())
    if st.button("Buscar Productos"):
        df_resultado = buscar_productos(df)
        st.dataframe(df_resultado)
        df_resultado.to_csv("resultados.csv", index=False)
        df_resultado.to_excel("resultados.xlsx", index=False)
        
        with open("resultados.xlsx", "rb") as file:
            st.download_button("Descargar Resultados en Excel", file, file_name="resultados.xlsx")
