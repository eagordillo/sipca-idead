import pydeck as pdk
import streamlit as st

from components.ui import apply_styles, footer, header
from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.visualizaciones import SIPCAVisualizations

#st.set_page_config(
    #page_title="Cobertura territorial · SIPCA",
    #page_icon="🗺️",
    #layout="wide",
#)
apply_styles()


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
        <b>{Nombre_cat}</b><br/>
        Municipio: {Municipio}<br/>
        Departamento: {Departamento}<br/>
        Región: {Región}<br/>
        Estado: {Estado territorial}<br/>
        Pertinencia: {Nivel de pertinencia}<br/>
        Prioridad: {Nivel de prioridad}<br/>
        Énfasis: {Énfasis territorial}
        """,
        "style": {
            "backgroundColor": "#174F32",
            "color": "white",
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
    legend = map_data[[
        "Estado territorial", "color"
    ]].drop_duplicates("Estado territorial")
    st.dataframe(
        legend[["Estado territorial"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Detalle territorial")
    st.dataframe(
        map_data[[
            "Nombre_cat",
            "Municipio",
            "Departamento",
            "Región",
            "Estado territorial",
            "Nivel de pertinencia",
            "Nivel de prioridad",
            "Énfasis territorial",
        ]],
        use_container_width=True,
        hide_index=True,
    )

footer()
