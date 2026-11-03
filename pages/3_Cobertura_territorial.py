from html import escape

import pydeck as pdk
import streamlit as st

from components.ui import apply_styles, footer, header, sidebar_info
from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.visualizaciones import SIPCAVisualizations

#st.set_page_config(
    #page_title="Cobertura territorial · SIPCA",
    #page_icon="🗺️",
    #layout="wide",
#)
apply_styles()
sidebar_info(show_author=True)

@st.cache_resource(show_spinner=False)
def get_visualizations() -> SIPCAVisualizations:
    return SIPCAVisualizations(SIPCADatabase(EXCEL_FILE))


visuals = get_visualizations()
db = visuals.db

header(
    "Cobertura territorial",
    "Presencia actual del IDEAD y oportunidades de ampliación por programa académico.",
)

programs = ["Todos los programas"] + db.obtener_programas()[
    "Nombre_oficial"
].tolist()
municipalities = db.obtener_municipios()
regions = ["Todas"] + sorted(
    municipalities["Región"].dropna().unique().tolist()
)

f1, f2, f3 = st.columns(3)
with f1:
    selected_program = st.selectbox("Programa académico", programs)
with f2:
    selected_region = st.selectbox("Región", regions)
with f3:
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

program_filter = (
    None if selected_program == "Todos los programas" else selected_program
)
map_data = visuals.mapa_cat(
    program=program_filter,
    region=selected_region,
    department=selected_department,
)
summary = visuals.resumen_cobertura(map_data)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("CAT visibles", summary["cat"])
m2.metric("Municipios", summary["municipios"])
m3.metric("Departamentos", summary["departamentos"])
m4.metric("CAT con oferta", summary["oferta"])
m5.metric("CAT potenciales", summary["oportunidades"])

if map_data.empty:
    st.warning(
        "No existen CAT con coordenadas válidas para los filtros seleccionados."
    )
else:
    center_lat = float(map_data["Latitud"].mean())
    center_lon = float(map_data["Longitud"].mean())

    lat_span = float(map_data["Latitud"].max() - map_data["Latitud"].min())
    lon_span = float(map_data["Longitud"].max() - map_data["Longitud"].min())
    geographic_span = max(lat_span, lon_span)

    if geographic_span <= 1.5:
        map_zoom = 7.0
    elif geographic_span <= 3.0:
        map_zoom = 6.2
    elif geographic_span <= 6.0:
        map_zoom = 5.5
    else:
        map_zoom = 5.0

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[Longitud, Latitud]",
        get_fill_color="color",
        get_radius="radio",
        pickable=True,
        auto_highlight=True,
        stroked=True,
        get_line_color=[255, 255, 255, 220],
        line_width_min_pixels=1,
    )

    
    tooltip = {
        "html": """
            <div style="
                max-width: 240px;
                box-sizing: border-box;
                white-space: normal;
                overflow-wrap: anywhere;
                font-size: 12px;
                line-height: 1.5;
            ">
                <strong>{Nombre_cat}</strong>
                <div>Municipio: {Municipio}</div>
                <div>Departamento: {Departamento}</div>
                <div>Región: {Región}</div>
                <div>Estado: {Estado territorial}</div>
                <div>Pertinencia: {Nivel de pertinencia}</div>
                <div>Prioridad: {Nivel de prioridad}</div>
                <div>Énfasis: {Énfasis territorial}</div>
            </div>
        """,
        "style": {
            "backgroundColor": "#174F32",
            "color": "white",
            "borderRadius": "8px",
            "padding": "8px",
            "maxWidth": "220px",
            "whiteSpace": "normal",
            "overflowWrap": "anywhere",
            "pointerEvents": "none",
        },
    }


    deck = pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=map_zoom,
            pitch=0,
        ),
        layers=[layer],
        tooltip=tooltip,
    )
    st.pydeck_chart(deck, use_container_width=True)

    
    st.markdown("### Convenciones")

    legend = (
        map_data[["Estado territorial", "color"]]
        .drop_duplicates(subset=["Estado territorial"])
        .sort_values("Estado territorial")
    )

    legend_html = []

    for _, item in legend.iterrows():
        estado = str(item["Estado territorial"])
        color = item["color"]

        # Los colores del mapa se encuentran en formato RGB o RGBA.
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            rgb = [int(c) for c in color[:3]]
            color_css = f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
        else:
            color_css = "#808080"

        legend_html.append(
            '<div style="display:flex;align-items:center;'
            'gap:10px;padding:7px 0;">'
            f'<span style="display:inline-block;'
            f'width:14px;height:14px;'
            f'border-radius:50%;'
            f'background-color:{color_css};'
            f'border:1px solid #dfe3e8;'
            f'flex-shrink:0;"></span>'
            f'<span>{escape(estado)}</span>'
            '</div>'
        )

    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;'
        'column-gap:28px;row-gap:4px;'
        'padding:12px 16px;'
        'background-color:#ffffff;'
        'border:1px solid #e1e4e9;'
        'border-radius:10px;">'
        + "".join(legend_html)
        + '</div>',
        unsafe_allow_html=True,
    )


    
    
    st.markdown("### Detalle territorial")

    columnas_base = [
        "Nombre_cat",
        "Municipio",
        "Departamento",
        "Región",
        "Estado territorial",
    ]

    columnas_analisis = [
        "Nivel de pertinencia",
        "Nivel de prioridad",
        "Énfasis territorial",
    ]

    # Los indicadores de pertinencia y prioridad
    # corresponden a relaciones municipio-programa.
    if program_filter is None:
        columnas = columnas_base
    else:
        columnas = columnas_base + columnas_analisis

    detalle = map_data[columnas].copy()

    st.dataframe(
        detalle,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nombre_cat": st.column_config.TextColumn(
                "Centro de Atención Tutorial",
                width="large",
            ),
            "Municipio": st.column_config.TextColumn(
                "Municipio",
                width="medium",
            ),
            "Departamento": st.column_config.TextColumn(
                "Departamento",
                width="medium",
            ),
            "Región": st.column_config.TextColumn(
                "Región",
                width="medium",
            ),
            "Estado territorial": st.column_config.TextColumn(
                "Estado territorial",
                width="medium",
            ),
            "Nivel de pertinencia": st.column_config.TextColumn(
                "Pertinencia",
                width="medium",
            ),
            "Nivel de prioridad": st.column_config.TextColumn(
                "Prioridad",
                width="medium",
            ),
            "Énfasis territorial": st.column_config.TextColumn(
                "Énfasis territorial",
                width="large",
            ),
        },
    )
