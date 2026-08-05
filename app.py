import streamlit as st

from components.ui import apply_styles, footer, header, sidebar_info
from config import APP_NAME, APP_VERSION, EXCEL_FILE, MODEL_VERSION
from core.database import SIPCADatabase, SIPCADataError

st.set_page_config(
    page_title="Inicio · SIPCA",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()
sidebar_info()


@st.cache_resource(show_spinner=False)
def get_database() -> SIPCADatabase:
    return SIPCADatabase(EXCEL_FILE).load()


header(
    "SIPCA IDEAD",
    "Sistema Inteligente para la Planeación de la Cobertura Académica",
)

try:
    db = get_database()
except SIPCADataError as exc:
    st.error(str(exc))
    st.stop()

summary = db.resumen()

st.markdown(
    """
    SIPCA integra información territorial, académica, educativa y socioeconómica
    para apoyar la planeación de la cobertura del IDEAD de la Universidad del Tolima.
    """
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Programas", summary["programas"])
c2.metric("Municipios", summary["municipios"])
c3.metric("CAT", summary["cat"])
c4.metric("Indicadores", summary["indicadores"])

st.success(f"{MODEL_VERSION} cargado correctamente.")

st.markdown("### Funcionalidades disponibles")

st.write(
    """
    - Consulta territorial por programa académico.
    - Consulta integral por municipio.
    - Análisis de cobertura territorial.
    - Visualización de indicadores educativos.
    - Dashboard ejecutivo.
    - Generación de informes y exportaciones.
    """
)

with st.expander("Diagnóstico técnico del modelo"):
    st.dataframe(
        db.health_report(),
        use_container_width=True,
        hide_index=True,
    )

st.caption(f"Aplicación {APP_VERSION}")
footer()