from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
CSS_FILE = BASE_DIR / "styles" / "institutional.css"


def apply_styles() -> None:
    if CSS_FILE.exists():
        st.markdown(CSS_FILE.read_text(encoding="utf-8"), unsafe_allow_html=True)


def header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <section class="sipca-header">
          <div class="institution-line">Universidad del Tolima · IDEAD</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def footer() -> None:
    st.markdown(
        """
        <div class="footer">
        SIPCA IDEAD · Sistema Inteligente para la Planeación de Cobertura Académica · Versión 1.0
        </div>
        """,
        unsafe_allow_html=True,
    )
