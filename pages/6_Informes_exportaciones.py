import streamlit as st

from components.ui import apply_styles, footer, header
from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.reportes import SIPCAReports

st.set_page_config(
    page_title='Informes y exportaciones · SIPCA',
    page_icon='📄',
    layout='wide',
)
apply_styles()


@st.cache_resource(show_spinner=False)
def get_reports() -> SIPCAReports:
    return SIPCAReports(SIPCADatabase(EXCEL_FILE))


reports = get_reports()
db = reports.db

header(
    'Informes y exportaciones',
    'Generación de documentos institucionales por municipio y programa académico.',
)

st.warning(
    'Los informes se generan a partir del Modelo de Datos SIPCA v1.0. '
    'Las recomendaciones son preliminares y requieren validación institucional.'
)

tab_municipality, tab_program = st.tabs([
    'Informe por municipio',
    'Informe por programa',
])

with tab_municipality:
    municipalities = db.obtener_municipios()['Municipio'].tolist()
    selected_municipality = st.selectbox(
        'Municipio',
        municipalities,
        index=None,
        placeholder='Seleccione un municipio',
        key='report_municipality',
    )

    if selected_municipality:
        result = reports.queries.consulta_municipio(selected_municipality)
        portfolio = reports.queries.portafolio_municipal(selected_municipality)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric('CAT', len(result['cat']))
        c2.metric('Programas ofertados', result['oferta']['Programa_id'].nunique())
        c3.metric('Portafolio territorial', portfolio['Programa base'].nunique())
        c4.metric('Recomendaciones', len(result['recomendaciones']))

        st.markdown('### Contenido del informe')
        st.write(
            'Perfil territorial, necesidades formativas, indicadores clave, '
            'oferta vigente, portafolio territorial, programas recomendados, '
            'indicadores disponibles y fuentes.'
        )

        pdf_bytes = reports.pdf_municipio(selected_municipality)
        excel_bytes = reports.excel_municipio(selected_municipality)
        filename = reports.safe_filename(selected_municipality)

        b1, b2 = st.columns(2)
        with b1:
            st.download_button(
                'Descargar informe PDF',
                data=pdf_bytes,
                file_name=f'SIPCA_Informe_Municipio_{filename}.pdf',
                mime='application/pdf',
                use_container_width=True,
            )
        with b2:
            st.download_button(
                'Descargar anexos Excel',
                data=excel_bytes,
                file_name=f'SIPCA_Informe_Municipio_{filename}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True,
            )
    else:
        st.info('Seleccione un municipio para preparar el informe.')

with tab_program:
    programs = db.obtener_programas()['Nombre_oficial'].tolist()
    selected_program = st.selectbox(
        'Programa académico',
        programs,
        index=None,
        placeholder='Seleccione un programa',
        key='report_program',
    )

    if selected_program:
        result = reports.queries.consulta_programa(selected_program)
        opportunities = reports.queries.ranking_oportunidades_programa(selected_program)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric('CAT con oferta', result['oferta']['CAT_id'].nunique())
        c2.metric('Municipios con oferta', result['oferta']['Municipio_id'].nunique())
        c3.metric('CAT potenciales', opportunities['CAT_id'].nunique())
        c4.metric('Recomendaciones relacionadas', len(result['recomendaciones']))

        st.markdown('### Contenido del informe')
        st.write(
            'Oferta vigente, oportunidades de ampliación, niveles de pertinencia, '
            'prioridades, énfasis territoriales, indicadores asociados, '
            'justificaciones y fuentes.'
        )

        pdf_bytes = reports.pdf_programa(selected_program)
        excel_bytes = reports.excel_programa(selected_program)
        filename = reports.safe_filename(selected_program)

        b1, b2 = st.columns(2)
        with b1:
            st.download_button(
                'Descargar informe PDF',
                data=pdf_bytes,
                file_name=f'SIPCA_Informe_Programa_{filename}.pdf',
                mime='application/pdf',
                use_container_width=True,
            )
        with b2:
            st.download_button(
                'Descargar anexos Excel',
                data=excel_bytes,
                file_name=f'SIPCA_Informe_Programa_{filename}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True,
            )
    else:
        st.info('Seleccione un programa para preparar el informe.')

footer()
