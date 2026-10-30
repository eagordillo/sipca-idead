
from pathlib import Path
from base64 import b64encode
from html import escape

import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
CSS_FILE = BASE_DIR / "styles" / "institutional.css"
ASSETS_DIR = BASE_DIR / "assets"


def image_data_uri(filename: str) -> str:
    """Convierte una imagen local en una URI para mostrarla en HTML."""
    path = ASSETS_DIR / filename

    if not path.is_file():
        return ""

    extension = path.suffix.lower()
    media_type = "image/png" if extension == ".png" else "image/jpeg"

    encoded = b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def apply_styles() -> None:
    """Carga los estilos institucionales de SIPCA."""
    if CSS_FILE.exists():
        css = CSS_FILE.read_text(encoding="utf-8")
        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )



def header(title: str, subtitle: str) -> None:
    """Muestra el encabezado institucional de SIPCA."""

    university_logo = image_data_uri("universidad_tolima.png")
    idead_logo = image_data_uri("idead_territorios.png")

    university_html = (
        f'<img src="{university_logo}" alt="Universidad del Tolima">'
        if university_logo
        else '<span>Universidad del Tolima</span>'
    )

    idead_html = (
        f'<img src="{idead_logo}" alt="IDEAD en los territorios">'
        if idead_logo
        else '<span>IDEAD</span>'
    )

    html = f"""
<section class="sipca-header">
    <div class="sipca-branding">
        <div class="sipca-university-logo">
            {university_html}
        </div>
        <div class="sipca-idead-logo">
            {idead_html}
        </div>
    </div>
    <div class="sipca-header-content">
        <div class="institution-line">
            Universidad del Tolima · IDEAD
        </div>
        <h1>{escape(title)}</h1>
        <p>{escape(subtitle)}</p>
    </div>
</section>
"""

    st.markdown(html, unsafe_allow_html=True)


def sidebar_info() -> None:
    """Información institucional en la barra lateral."""

    st.sidebar.divider()
    st.sidebar.markdown("## SIPCA")

    st.sidebar.caption(
        "Sistema Inteligente para la Planeación de la Cobertura Académica"
    )

    st.sidebar.markdown(
        "**Universidad del Tolima**"
    )
    st.sidebar.caption("Instituto de Educación a Distancia")

    st.sidebar.divider()
    st.sidebar.caption("Desarrollado por")
    st.sidebar.markdown("**Andrés Gordillo**")
    st.sidebar.caption("Versión 1.1.0")


def footer() -> None:
    """Muestra el pie institucional."""

    st.markdown(
        """
        <div class="footer">
            <strong>SIPCA IDEAD</strong><br>
            Sistema Inteligente para la Planeación de la Cobertura Académica<br>
            Universidad del Tolima · Instituto de Educación a Distancia<br>
            Desarrollado por Andrés Gordillo · Versión 1.1.0
        </div>
        """,
        unsafe_allow_html=True,
    )