from __future__ import annotations

from typing import Any
import pandas as pd

from core.database import SIPCADatabase


class SIPCAQueries:
    """Motor inteligente de consultas territoriales de SIPCA.

    Distingue la presencia actual de la oportunidad de expansión. La oferta se
    analiza por CAT; la pertinencia y las recomendaciones se analizan por
    municipio y se proyectan sobre los CAT activos de ese territorio.
    """

    RELEVANCE_ORDER = {
        "alta preliminar": 1,
        "media-alta preliminar": 2,
        "media preliminar": 3,
        "baja preliminar": 4,
    }
    PRIORITY_ORDER = {
        "alta": 1,
        "alta condicionada": 2,
        "media-alta": 3,
        "media": 4,
        "baja": 5,
    }

    def __init__(self, database: SIPCADatabase) -> None:
        self.db = database.load()

    def consulta_programa(self, program: str) -> dict[str, Any]:
        return self.db.ficha_programa_inteligente(program)

    def consulta_municipio(self, municipality: str) -> dict[str, Any]:
        return self.db.ficha_municipio_inteligente(municipality)

    def ranking_pertinencia(self, program: str) -> pd.DataFrame:
        data = self.db.pertinencia_por_programa(program).copy()
        data["orden_pertinencia"] = (
            data["Nivel de pertinencia"].str.casefold()
            .map(self.RELEVANCE_ORDER).fillna(99)
        )
        return (
            data.sort_values(["orden_pertinencia", "Departamento", "Municipio"])
            .drop(columns="orden_pertinencia")
            .reset_index(drop=True)
        )

    def ranking_oportunidades_programa(self, program: str) -> pd.DataFrame:
        data = self.db.oportunidades_por_programa(program).copy()
        if data.empty:
            return data
        data["orden_pertinencia"] = (
            data["Nivel de pertinencia"].str.casefold()
            .map(self.RELEVANCE_ORDER).fillna(99)
        )
        data["orden_prioridad"] = (
            data["Nivel de prioridad"].str.casefold()
            .map(self.PRIORITY_ORDER).fillna(99)
        )
        return (
            data.sort_values([
                "orden_prioridad", "orden_pertinencia", "Departamento",
                "Municipio", "Nombre_cat",
            ])
            .drop(columns=["orden_pertinencia", "orden_prioridad"])
            .reset_index(drop=True)
        )

    def portafolio_municipal(self, municipality: str) -> pd.DataFrame:
        data = self.db.portafolio_por_municipio(municipality).copy()
        if data.empty:
            return data
        state_order = {
            "Oferta vigente": 1,
            "Pertinente sin oferta": 2,
            "Recomendado para apertura": 3,
            "Pertinente y recomendado": 2,
        }
        data["orden_estado"] = data["Estado territorial"].map(state_order).fillna(99)
        return (
            data.sort_values(["orden_estado", "Programa base"])
            .drop(columns="orden_estado")
            .reset_index(drop=True)
        )
