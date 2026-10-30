import plotly.express as px
import streamlit as st

from components.ui import apply_styles, footer, header
from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.visualizaciones import SIPCAVisualizations

#st.set_page_config(
    #page_title="Indicadores territoriales · SIPCA",
    #page_icon="📈",
    #layout="wide",
#)
apply_styles()


@st.cache_resource(show_spinner=False)
def get_visualizations() -> SIPCAVisualizations:
    return SIPCAVisualizations(SIPCADatabase(EXCEL_FILE))


visuals = get_visualizations()
db = visuals.db

header(
    "Indicadores territoriales",
    "Evolución de cobertura, tránsito inmediato y mercado potencial municipal.",
)

municipalities = db.obtener_municipios()
selected = st.selectbox(
    "Municipio",
    municipalities["Municipio"].tolist(),
    index=None,
    placeholder="Seleccione un municipio",
)

if selected:
    data = visuals.indicadores_municipales(
        selected, codes=["TTI", "COBERTURA", "BACH_G11"]
    )

    if data.empty:
        st.info("No existen indicadores con año válido para el municipio.")
    else:
        latest = (
            data.sort_values("Año")
            .groupby("Indicador_codigo", as_index=False)
            .tail(1)
        )
        cols = st.columns(3)
        specs = [
            ("TTI", "TTI más reciente"),
            ("COBERTURA", "Cobertura más reciente"),
            ("BACH_G11", "Bachilleres grado 11"),
        ]
        for col, (code, label) in zip(cols, specs):
            row = latest[latest["Indicador_codigo"] == code]
            if row.empty:
                col.metric(label, "Sin dato")
            else:
                record = row.iloc[0]
                value = float(record["Valor"])
                display = (
                    f"{value:,.2f} %"
                    if record["Unidad"] == "%"
                    else f"{value:,.0f}"
                )
                col.metric(label, display, help=f"Año {int(record['Año'])}")

        trend = data[data["Indicador_codigo"].isin(["TTI", "COBERTURA"])]
        if not trend.empty:
            chart = px.line(
                trend,
                x="Año",
                y="Valor",
                color="Indicador_nombre",
                markers=True,
                labels={
                    "Valor": "Porcentaje",
                    "Indicador_nombre": "Indicador",
                },
            )
            chart.update_layout(xaxis_dtick=1)
            st.plotly_chart(chart, use_container_width=True)

        st.dataframe(data, use_container_width=True, hide_index=True)
else:
    st.info("Seleccione un municipio para visualizar sus indicadores.")

footer()
