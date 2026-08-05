from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
CSS_FILE = BASE_DIR / "styles" / "institutional.css"


def apply_styles() -> None:
    """Carga los estilos institucionales de SIPCA."""
    if CSS_FILE.exists():
        st.markdown(
            CSS_FILE.read_text(encoding="utf-8"),
            unsafe_allow_html=True,
        )


def header(title: str, subtitle: str) -> None:
    """Muestra el encabezado institucional."""
    st.markdown(
        f"""
        <section class="sipca-header">
            <div class="institution-line">
                Universidad del Tolima · IDEAD
            </div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def sidebar_info() -> None:
    """Información institucional en la barra lateral."""

    st.sidebar.divider()

    st.sidebar.markdown("## SIPCA")

    st.sidebar.caption(
        "Sistema Inteligente para la Planeación de la Cobertura Académica"
    )

    st.sidebar.markdown(
        """
**Universidad del Tolima**

Instituto de Educación a Distancia
"""
    )

    st.sidebar.divider()

    st.sidebar.caption("Desarrollado por")

    st.sidebar.markdown("**Andrés Gordillo**")

    st.sidebar.caption("Versión 1.1.0")


def footer() -> None:
    """Muestra el pie institucional."""
    st.markdown(
        """
        <div class="footer">
           Desarrollado por Andrés Gordillo
            SIPCA IDEAD · Sistema Inteligente para la Planeación de la
            Cobertura Académica · Versión 1.1.0
            <br>
                    </div>
        """,
        unsafe_allow_html=True,
    )