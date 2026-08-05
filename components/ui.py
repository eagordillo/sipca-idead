from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
CSS_FILE = BASE_DIR / "styles" / "institutional.css"


def apply_styles() -> None:
    if CSS_FILE.exists():
        st.markdown(
            CSS_FILE.read_text(encoding="utf-8"),
            unsafe_allow_html=True,
        )


def header(title: str, subtitle: str) -> None:
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
    st.sidebar.divider()

    st.sidebar.markdown("### SIPCA")

    st.sidebar.caption(
        "Sistema Inteligente para la Planeación de la Cobertura Académica"
    )

    st.sidebar.markdown("**Universidad del Tolima**")
    st.sidebar.caption("Instituto de Educación a Distancia · IDEAD")

    st.sidebar.divider()

    st.sidebar.caption("Desarrollado por")
    st.sidebar.markdown("**Andrés Gordillo**")
    st.sidebar.caption("Versión 1.1.0")


def footer() -> None:
    st.markdown(
        """
        <div class="footer">
            SIPCA IDEAD · Sistema Inteligente para la Planeación de la
            Cobertura Académica · Versión 1.1.0
            <br>
            Desarrollado por Andrés Gordillo
        </div>
        """,
        unsafe_allow_html=True,
    )
