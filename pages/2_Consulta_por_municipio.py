import streamlit as st

from components.ui import apply_styles, footer, header, sidebar_info
from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.consultas import SIPCAQueries

#st.set_page_config(page_title="Consulta por municipio · SIPCA", page_icon="📍", layout="wide")
apply_styles()
sidebar_info(show_author=True)


@st.cache_resource(show_spinner=False)
def get_queries() -> SIPCAQueries:
    return SIPCAQueries(SIPCADatabase(EXCEL_FILE))


queries = get_queries()
db = queries.db

header(
    "Consulta por municipio",
    "Qué programas se ofertan, cuáles son pertinentes y cuáles podrían incorporarse.",
)

municipalities = db.obtener_municipios()
selected = st.selectbox(
    "Municipio",
    municipalities["Municipio"].tolist(),
    index=None,
    placeholder="Seleccione un municipio",
)

if selected:
    result = queries.consulta_municipio(selected)
    municipality = result["municipio"]

    classification = queries.clasificacion_municipal(selected)
    portfolio = classification["portafolio"]
    recommendations = classification["recomendaciones"]

    # Programas pertinentes que todavía no tienen oferta en el municipio
    portfolio_pertinente = portfolio.loc[
        portfolio["Estado territorial"]
        .astype(str)
        .str.strip()
        .str.casefold()
        == "pertinente sin oferta"
    ].copy()

    st.subheader(f"{municipality['Municipio']} · {municipality['Departamento']}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CAT", len(result["cat"]))
    c2.metric("Programas ofertados", classification["oferta"]["Programa_id"].nunique())
    c3.metric("Portafolio territorial", portfolio["Programa base"].nunique())
    c4.metric("Programas recomendados", recommendations["Programa base"].nunique())
    
    tab_profile, tab_offer, tab_portfolio, tab_recommendations, tab_indicators = st.tabs([
        "Perfil territorial",
        "Oferta vigente",
        "Portafolio territorial",
        "Recomendaciones",
        "Indicadores",
    ])

    with tab_profile:
        if result["perfil"].empty:
            st.warning("No existe perfil territorial registrado.")
        else:
            profile = result["perfil"].iloc[0]
            st.markdown("#### Perfil territorial")
            st.write(profile["Perfil territorial integrado"])
            st.markdown("#### Necesidades formativas prioritarias")
            st.write(profile["Necesidades formativas prioritarias"])

    with tab_offer:
        offer = result["oferta"].merge(
            result["cat"][["CAT_id", "Nombre_cat"]].drop_duplicates(),
            how="left",
            on="CAT_id",
        )
        if offer.empty:
            st.info("El municipio no registra oferta vigente.")
        else:
            st.dataframe(
                offer[["Nombre_oficial", "Nombre_cat", "Modalidad", "Estado_oferta"]],
                use_container_width=True,
                hide_index=True,
            )

    with tab_portfolio:
        st.caption(
            "Programas académicos del IDEAD con pertinencia territorial "
            "identificada que todavía no registran oferta en el municipio."
        )

        if portfolio.empty:
            st.info(
                "No se identificaron programas del IDEAD pertinentes "
                "sin oferta vigente para este municipio."
            )
        else:
            st.dataframe(
                portfolio[[
                    "Programa base",
                    "Nivel de pertinencia",
                    "Nivel de prioridad",
                    "Énfasis territorial",
                    "Justificación",
                ]],
                use_container_width=True,
                hide_index=True,
            )

    with tab_recommendations:
        st.caption("Programas recomendados para el municipio que no forman " "parte del portafolio académico actual del IDEAD."
    )
        if recommendations.empty:
            st.info("No existen programas recomendados registrados.")
        else:
            st.dataframe(
                recommendations[[
                    "Programa base", "Énfasis territorial", "Nivel de prioridad",
                    "Horizonte sugerido", "Modalidad recomendada",
                    "Viabilidad institucional preliminar",
                    "Justificación técnica Municipio–programa",
                ]],
                use_container_width=True,
                hide_index=True,
            )

    with tab_indicators:
        indicators = result["indicadores"]
        if indicators.empty:
            st.info("No existen indicadores registrados para el municipio.")
        else:
            st.dataframe(indicators, use_container_width=True, hide_index=True)
else:
    st.info("Seleccione un municipio para consultar su ficha.")

footer()
