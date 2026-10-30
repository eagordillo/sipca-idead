import plotly.express as px
import streamlit as st

from components.ui import apply_styles, footer, header
from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.dashboard import SIPCADashboard

#st.set_page_config(
    #page_title="Dashboard ejecutivo · SIPCA",
    #page_icon="📊",
    #layout="wide",
#)
apply_styles()


@st.cache_resource(show_spinner=False)
def get_dashboard() -> SIPCADashboard:
    return SIPCADashboard(SIPCADatabase(EXCEL_FILE))


dashboard = get_dashboard()
db = dashboard.db
municipalities = db.obtener_municipios()

header(
    "Dashboard ejecutivo",
    "Panorama institucional de cobertura, pertinencia y oportunidades de ampliación.",
)

regions = ["Todas"] + sorted(
    municipalities["Región"].dropna().unique().tolist()
)

f1, f2 = st.columns(2)
with f1:
    selected_region = st.selectbox("Región", regions)
with f2:
    if selected_region == "Todas":
        department_options = ["Todos"] + sorted(
            municipalities["Departamento"].dropna().unique().tolist()
        )
    else:
        department_options = ["Todos"] + sorted(
            municipalities.loc[
                municipalities["Región"] == selected_region,
                "Departamento",
            ].dropna().unique().tolist()
        )
    selected_department = st.selectbox("Departamento", department_options)

summary = dashboard.resumen(selected_region, selected_department)

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Programas activos", summary["programas"])
m2.metric("CAT", summary["cat"])
m3.metric("Municipios del modelo", summary["municipios_catalogo"])
m4.metric("Municipios con CAT", summary["municipios_con_cat"])
m5.metric("Pertinencias", summary["pertinencias"])
m6.metric("Recomendaciones", summary["recomendaciones"])

coverage = dashboard.cobertura_por_programa(
    selected_region, selected_department
)
opportunities = dashboard.oportunidades_por_programa(
    selected_region, selected_department
)
recommendations = dashboard.recomendaciones_por_municipio(
    selected_region, selected_department
)
relevance = dashboard.distribucion_pertinencia(
    selected_region, selected_department
)
priority = dashboard.distribucion_prioridad(
    selected_region, selected_department
)
matrix = dashboard.matriz_programa_territorio(
    selected_region, selected_department
)

tab_summary, tab_programs, tab_territories, tab_indicators = st.tabs([
    "Resumen estratégico",
    "Programas",
    "Territorios",
    "Indicadores educativos",
])

with tab_summary:
    left, right = st.columns(2)

    with left:
        st.markdown("### Cobertura actual por programa")
        if coverage.empty:
            st.info("No existe oferta para los filtros seleccionados.")
        else:
            figure = px.bar(
                coverage.head(12),
                x="CAT_con_oferta",
                y="Nombre_oficial",
                orientation="h",
                text_auto=True,
                labels={
                    "CAT_con_oferta": "CAT con oferta",
                    "Nombre_oficial": "Programa",
                },
            )
            figure.update_layout(
                yaxis={"categoryorder": "total ascending"},
                showlegend=False,
            )
            st.plotly_chart(figure, use_container_width=True)

    with right:
        st.markdown("### Oportunidades de ampliación")
        if opportunities.empty:
            st.info("No existen oportunidades con los filtros seleccionados.")
        else:
            figure = px.bar(
                opportunities.head(12),
                x="CAT_potenciales",
                y="Programa",
                orientation="h",
                text_auto=True,
                labels={
                    "CAT_potenciales": "CAT potenciales",
                    "Programa": "Programa",
                },
            )
            figure.update_layout(
                yaxis={"categoryorder": "total ascending"},
                showlegend=False,
            )
            st.plotly_chart(figure, use_container_width=True)

    left, right = st.columns(2)

    with left:
        st.markdown("### Distribución de la pertinencia")
        if relevance.empty:
            st.info("No existen relaciones de pertinencia.")
        else:
            figure = px.pie(
                relevance,
                names="Nivel de pertinencia",
                values="Relaciones",
                hole=0.45,
            )
            figure.update_traces(
                textposition="inside",
                textinfo="percent+label",
            )
            st.plotly_chart(figure, use_container_width=True)

    with right:
        st.markdown("### Prioridad de las recomendaciones")
        if priority.empty:
            st.info("No existen recomendaciones.")
        else:
            figure = px.pie(
                priority,
                names="Nivel de prioridad",
                values="Recomendaciones",
                hole=0.45,
            )
            figure.update_traces(
                textposition="inside",
                textinfo="percent+label",
            )
            st.plotly_chart(figure, use_container_width=True)

with tab_programs:
    st.markdown("### Matriz ejecutiva por programa")
    st.caption(
        "Contrasta la presencia institucional actual con el potencial territorial."
    )
    st.dataframe(matrix, use_container_width=True, hide_index=True)

    program_options = matrix["Programa"].tolist() if not matrix.empty else []
    selected_program = st.selectbox(
        "Detalle de programa",
        program_options,
        index=None,
        placeholder="Seleccione un programa",
    )

    if selected_program:
        current = matrix[matrix["Programa"] == selected_program].iloc[0]
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("CAT con oferta", int(current["CAT_con_oferta"]))
        p2.metric("Municipios con oferta", int(current["Municipios_con_oferta"]))
        p3.metric("CAT potenciales", int(current["CAT_potenciales"]))
        p4.metric("Oportunidades altas", int(current["Prioridad_alta"]))

        detail = dashboard.queries.ranking_oportunidades_programa(
            selected_program
        )
        if selected_region != "Todas":
            valid_departments = set(
                municipalities.loc[
                    municipalities["Región"] == selected_region,
                    "Departamento",
                ].dropna()
            )
            detail = detail[detail["Departamento"].isin(valid_departments)]
        if selected_department != "Todos":
            detail = detail[detail["Departamento"] == selected_department]

        if detail.empty:
            st.info("No existen oportunidades territoriales adicionales.")
        else:
            st.dataframe(
                detail[[
                    "Nombre_cat", "Municipio", "Departamento",
                    "Estado territorial", "Nivel de pertinencia",
                    "Nivel de prioridad", "Énfasis territorial",
                    "Bachilleres grado 11 (2023)",
                ]],
                use_container_width=True,
                hide_index=True,
            )

with tab_territories:
    st.markdown("### Municipios con mayor número de recomendaciones")
    if recommendations.empty:
        st.info("No existen recomendaciones para los filtros seleccionados.")
    else:
        figure = px.bar(
            recommendations.head(15),
            x="Municipio",
            y="Programas_recomendados",
            text_auto=True,
            hover_data=["Departamento", "Región", "Prioridad_alta"],
            labels={"Programas_recomendados": "Programas recomendados"},
        )
        figure.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(figure, use_container_width=True)
        st.dataframe(
            recommendations,
            use_container_width=True,
            hide_index=True,
        )

with tab_indicators:
    indicators = dashboard.indicadores_clave(
        selected_region,
        selected_department,
        year=2024,
    )

    if indicators.empty:
        st.info(
            "No existen indicadores municipales de 2024 "
            "para los filtros seleccionados."
        )
    else:
        selected_indicator = st.radio(
            "Indicador",
            ["TTI", "COBERTURA"],
            horizontal=True,
        )
        current = indicators[
            indicators["Indicador_codigo"] == selected_indicator
        ].copy()

        figure = px.bar(
            current,
            x="Municipio",
            y="Valor",
            hover_data=["Departamento", "Región"],
            labels={"Valor": "Porcentaje", "Municipio": "Municipio"},
        )
        figure.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
        )
        st.plotly_chart(figure, use_container_width=True)
        st.dataframe(current, use_container_width=True, hide_index=True)

footer()
