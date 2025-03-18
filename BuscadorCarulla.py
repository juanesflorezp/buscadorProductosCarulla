import streamlit as st
import pandas as pd
import requests

st.title("Buscador de Productos en Carulla")

uploaded_file = st.file_uploader("Sube un archivo CSV o Excel con los productos", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    st.dataframe(df.head())

    if st.button("Buscar Productos"):
        st.write("⏳ Procesando... Esto puede tardar unos minutos.")
        
        files = {"file": uploaded_file.getvalue()}
        response = requests.post("http://localhost:8000/buscar_productos/", files=files)

        if response.status_code == 200:
            df_resultado = pd.DataFrame(response.json())
            st.dataframe(df_resultado)
            
            df_resultado.to_csv("resultados.csv", index=False)
            df_resultado.to_excel("resultados.xlsx", index=False)

            with open("resultados.xlsx", "rb") as file:
                st.download_button("Descargar Resultados en Excel", file, file_name="resultados.xlsx")
        else:
            st.error("Hubo un error al procesar la solicitud.")
