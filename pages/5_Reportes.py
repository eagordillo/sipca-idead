import streamlit as st
from components.ui import aplicar_estilos, encabezado, pie_pagina
st.set_page_config(page_title="Reportes · SIPCA",page_icon="📄",layout="wide")
aplicar_estilos()
encabezado("Reportes","Generación de informes ejecutivos descargables.")
st.info("Este módulo está preparado en la arquitectura y será desarrollado en la siguiente fase.")
pie_pagina()
