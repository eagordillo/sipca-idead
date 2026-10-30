
import streamlit as st


st.set_page_config(
    page_title="SIPCA IDEAD",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)


pages = {
    "SIPCA IDEAD": [
        st.Page(
            "pages/0_Inicio.py",
            title="Inicio",
            icon="🏠",
            default=True,
        ),
        st.Page(
            "pages/1_Consulta_por_programa.py",
            title="Consulta por programa",
            icon="🎓",
        ),
        st.Page(
            "pages/2_Consulta_por_municipio.py",
            title="Consulta por municipio",
            icon="📍",
        ),
        st.Page(
            "pages/3_Cobertura_territorial.py",
            title="Cobertura territorial",
            icon="🗺️",
        ),
        st.Page(
            "pages/4_Indicadores_territoriales.py",
            title="Indicadores territoriales",
            icon="📊",
        ),
        st.Page(
            "pages/5_Dashboard_ejecutivo.py",
            title="Dashboard ejecutivo",
            icon="📈",
        ),
        st.Page(
            "pages/6_Informes_exportaciones.py",
            title="Informes y exportaciones",
            icon="📄",
        ),
    ]
}


navigation = st.navigation(pages)
navigation.run()