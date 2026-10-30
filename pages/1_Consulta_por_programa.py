import streamlit as st

from components.ui import apply_styles, footer, header
from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.consultas import SIPCAQueries

#st.set_page_config(page_title="Consulta por programa · SIPCA", page_icon="🎓", layout="wide")
apply_styles()


@st.cache_resource(show_spinner=False)
def get_queries() -> SIPCAQueries:
    return SIPCAQueries(SIPCADatabase(EXCEL_FILE))


queries = get_queries()
db = queries.db

header(
    "Consulta por programa",
    "Dónde se oferta actualmente y en qué CAT existe oportunidad de ampliación.",
)

programs = db.obtener_programas()
selected = st.selectbox(
    "Programa académico",
    programs["Nombre_oficial"].tolist(),
    index=None,
    placeholder="Seleccione un programa",
)

if selected:
    result = queries.consulta_programa(selected)
    offer = result["oferta"]
    recommendations = result["recomendaciones"]
    opportunities = queries.ranking_oportunidades_programa(selected)

    c1, c2, c3 = st.columns(3)
    c1.metric("CAT con oferta", offer["CAT_id"].nunique())
    c2.metric("Municipios con oferta", offer["Municipio_id"].nunique())
    c3.metric("CAT potenciales", opportunities["CAT_id"].nunique())

    st.caption(
        "Las oportunidades de ampliación integran los territorios pertinentes "
        "y los municipios recomendados donde el programa aún no se oferta."
    )

    tab_offer, tab_opportunities, tab_recommendations = st.tabs([
        "Oferta vigente",
        "Oportunidades de ampliación",
        "Recomendaciones relacionadas",
    ])

    with tab_offer:
        if offer.empty:
            st.info("El programa no registra oferta vigente en los CAT analizados.")
        else:
            st.dataframe(
                offer[["Nombre_cat", "Municipio de oferta", "Modalidad", "Estado_oferta"]],
                use_container_width=True,
                hide_index=True,
            )

    with tab_opportunities:
        if opportunities.empty:
            st.info("No se identificaron CAT adicionales con los criterios actuales.")
        else:
            st.dataframe(
                opportunities[[
                    "Nombre_cat", "Municipio", "Departamento", "Estado territorial",
                    "Nivel de pertinencia", "Nivel de prioridad", "Énfasis territorial",
                    "Modalidad sugerida", "TTI municipal 2024 (%)",
                    "Cobertura municipal 2024 (%)", "Bachilleres grado 11 (2023)",
                    "Justificación",
                ]],
                use_container_width=True,
                hide_index=True,
            )

    with tab_recommendations:
        if recommendations.empty:
            st.info("No existen recomendaciones equivalentes registradas para este programa.")
        else:
            st.dataframe(
                recommendations[[
                    "Municipio", "Departamento", "Programa base", "Énfasis territorial",
                    "Nivel de prioridad", "Horizonte sugerido", "Modalidad recomendada",
                    "Viabilidad institucional preliminar",
                    "Justificación técnica Municipio–programa",
                ]],
                use_container_width=True,
                hide_index=True,
            )
else:
    st.info("Seleccione un programa para iniciar la consulta.")

footer()
