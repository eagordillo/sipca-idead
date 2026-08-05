import streamlit as st

from components.ui import apply_styles, footer, header
from config import APP_NAME, APP_VERSION, EXCEL_FILE, MODEL_VERSION
from core.database import SIPCADatabase, SIPCADataError

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_styles()


@st.cache_resource(show_spinner=False)
def get_database() -> SIPCADatabase:
    return SIPCADatabase(EXCEL_FILE).load()


header(
    "SIPCA IDEAD",
    "Módulo 5 · Informes y exportaciones",
)

try:
    db = get_database()
except SIPCADataError as exc:
    st.error(str(exc))
    st.stop()

summary = db.resumen()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Programas", summary["programas"])
c2.metric("Municipios", summary["municipios"])
c3.metric("CAT", summary["cat"])
c4.metric("Indicadores", summary["indicadores"])

st.success(f"{MODEL_VERSION} cargado correctamente.")
st.markdown("### Capacidades del módulo")
st.write(
    "La consulta por programa diferencia la oferta vigente de los CAT potenciales. "
    "La consulta por municipio integra oferta, pertinencia y recomendaciones, y "
    "reconoce como un solo programa las recomendaciones que incorporan énfasis territoriales."
)

with st.expander("Diagnóstico técnico del modelo"):
    st.dataframe(db.health_report(), use_container_width=True, hide_index=True)

st.caption(f"Aplicación {APP_VERSION}")
footer()
