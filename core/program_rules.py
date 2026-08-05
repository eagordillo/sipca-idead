from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


def clean_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def text_key(value: object) -> str:
    text = unicodedata.normalize("NFKD", clean_text(value).casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


@dataclass(frozen=True)
class NormalizedProgram:
    original_name: str
    base_name: str
    base_key: str
    emphasis: str


# Las equivalencias resuelven diferencias semánticas entre el catálogo oficial
# y los nombres usados en recomendaciones territoriales. Se mantienen fuera de
# la interfaz para que puedan ampliarse sin modificar las páginas de Streamlit.
PROGRAM_ALIASES = {
    text_key("Administración Turística y Hotelera"):
        "Administración de Empresas Turísticas y Hoteleras",
    text_key("Administración de Empresas Turisticas y Hoteleras"):
        "Administración de Empresas Turísticas y Hoteleras",
    text_key("Tecnología Protección y Recuperación de Ecosistemas Forestales"):
        "Tecnología en Protección y Recuperación de Ecosistemas Forestales",
}


_EMPHASIS_PATTERN = re.compile(
    r"\(\s*(?:énfasis|enfasis)\s+en\s+(.+?)\s*\)\s*$",
    flags=re.IGNORECASE,
)


def normalize_program_name(name: object) -> NormalizedProgram:
    original = clean_text(name)
    emphasis = ""
    base = original

    match = _EMPHASIS_PATTERN.search(original)
    if match:
        emphasis = clean_text(match.group(1))
        base = clean_text(original[: match.start()])

    canonical = PROGRAM_ALIASES.get(text_key(base), base)
    return NormalizedProgram(
        original_name=original,
        base_name=canonical,
        base_key=text_key(canonical),
        emphasis=emphasis,
    )
