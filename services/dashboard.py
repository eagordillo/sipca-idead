from __future__ import annotations

import pandas as pd

from core.database import SIPCADatabase
from services.consultas import SIPCAQueries


class SIPCADashboard:
    """Construye agregados ejecutivos sobre el Modelo de Datos SIPCA v1.0."""

    RELEVANCE_ORDER = {
        "Alta preliminar": 1,
        "Media-alta preliminar": 2,
        "Media preliminar": 3,
        "Baja preliminar": 4,
    }

    PRIORITY_ORDER = {
        "Alta": 1,
        "Alta condicionada": 2,
        "Media-alta": 3,
        "Media": 4,
        "Baja": 5,
    }

    def __init__(self, database: SIPCADatabase) -> None:
        self.db = database.load()
        self.queries = SIPCAQueries(self.db)

    @staticmethod
    def _filter(
        data: pd.DataFrame,
        region: str | None = None,
        department: str | None = None,
    ) -> pd.DataFrame:
        result = data.copy()
        if region and region != "Todas" and "Región" in result.columns:
            result = result[result["Región"] == region]
        if department and department != "Todos" and "Departamento" in result.columns:
            result = result[result["Departamento"] == department]
        return result

    def _municipalities(
        self,
        region: str | None,
        department: str | None,
    ) -> pd.DataFrame:
        return self._filter(
            self.db.obtener_municipios(solo_activos=True),
            region,
            department,
        )

    def resumen(
        self,
        region: str | None = None,
        department: str | None = None,
    ) -> dict[str, int]:
        municipalities = self._municipalities(region, department)
        municipality_ids = set(municipalities["Municipio_id"].dropna())

        cats = self.db.table("cat")
        cats = cats[cats["Municipio_id"].isin(municipality_ids)]

        offer = self.db.table("oferta")
        offer = offer[offer["Municipio_id"].isin(municipality_ids)]

        relevance = self.db.table("pertinencia")
        relevance = relevance[relevance["Municipio_id"].isin(municipality_ids)]

        recommendations = self.db.table("recomendaciones")
        recommendations = recommendations[
            recommendations["Municipio_id"].isin(municipality_ids)
        ]

        return {
            "programas": int(offer["Programa_id"].nunique()),
            "municipios_catalogo": int(municipalities["Municipio_id"].nunique()),
            "municipios_con_cat": int(cats["Municipio_id"].nunique()),
            "cat": int(cats["CAT_id"].nunique()),
            "departamentos": int(municipalities["Departamento"].nunique()),
            "ofertas": int(len(offer)),
            "pertinencias": int(len(relevance)),
            "recomendaciones": int(len(recommendations)),
        }

    def cobertura_por_programa(
        self,
        region: str | None = None,
        department: str | None = None,
    ) -> pd.DataFrame:
        municipalities = self._municipalities(region, department)
        municipality_ids = set(municipalities["Municipio_id"].dropna())
        offer = self.db.table("oferta")
        offer = offer[offer["Municipio_id"].isin(municipality_ids)]

        if offer.empty:
            return pd.DataFrame(columns=[
                "Programa_id", "Nombre_oficial", "CAT_con_oferta",
                "Municipios_con_oferta", "Registros_de_oferta",
            ])

        return (
            offer.groupby(["Programa_id", "Nombre_oficial"], as_index=False)
            .agg(
                CAT_con_oferta=("CAT_id", "nunique"),
                Municipios_con_oferta=("Municipio_id", "nunique"),
                Registros_de_oferta=("CAT_id", "size"),
            )
            .sort_values(
                ["CAT_con_oferta", "Municipios_con_oferta"],
                ascending=False,
            )
            .reset_index(drop=True)
        )

    def oportunidades_por_programa(
        self,
        region: str | None = None,
        department: str | None = None,
    ) -> pd.DataFrame:
        rows: list[dict] = []

        for _, program in self.db.obtener_programas().iterrows():
            name = program["Nombre_oficial"]
            data = self.queries.ranking_oportunidades_programa(name)
            data = self._filter(data, region, department)

            if data.empty:
                high_priority = 0
                cat_count = 0
                municipality_count = 0
            else:
                priority = data["Nivel de prioridad"].fillna("").astype(str)
                high_priority = int(
                    priority.str.casefold().str.startswith("alta").sum()
                )
                cat_count = int(data["CAT_id"].nunique())
                municipality_count = int(data["Municipio_id"].nunique())

            rows.append({
                "Programa_id": program["Programa_id"],
                "Programa": name,
                "CAT_potenciales": cat_count,
                "Municipios_potenciales": municipality_count,
                "Prioridad_alta": high_priority,
            })

        return (
            pd.DataFrame(rows)
            .sort_values(
                ["CAT_potenciales", "Prioridad_alta", "Programa"],
                ascending=[False, False, True],
            )
            .reset_index(drop=True)
        )

    def recomendaciones_por_municipio(
        self,
        region: str | None = None,
        department: str | None = None,
    ) -> pd.DataFrame:
        data = self._filter(
            self.db.table("recomendaciones"),
            region,
            department,
        )
        if data.empty:
            return pd.DataFrame(columns=[
                "Municipio", "Departamento", "Región",
                "Programas_recomendados", "Prioridad_alta",
            ])

        data = data.assign(
            es_alta=(
                data["Nivel de prioridad"].fillna("").astype(str)
                .str.casefold().str.startswith("alta").astype(int)
            )
        )
        return (
            data.groupby(
                ["Municipio_id", "Municipio", "Departamento", "Región"],
                as_index=False,
            )
            .agg(
                Programas_recomendados=("Programa recomendado", "nunique"),
                Prioridad_alta=("es_alta", "sum"),
            )
            .sort_values(
                ["Programas_recomendados", "Prioridad_alta", "Municipio"],
                ascending=[False, False, True],
            )
            .reset_index(drop=True)
        )

    def distribucion_pertinencia(
        self,
        region: str | None = None,
        department: str | None = None,
    ) -> pd.DataFrame:
        data = self._filter(
            self.db.table("pertinencia"),
            region,
            department,
        )
        if data.empty:
            return pd.DataFrame(columns=["Nivel de pertinencia", "Relaciones"])

        result = (
            data.groupby("Nivel de pertinencia", as_index=False)
            .agg(Relaciones=("pertinencia_id", "nunique"))
        )
        result["orden"] = (
            result["Nivel de pertinencia"]
            .map(self.RELEVANCE_ORDER)
            .fillna(99)
        )
        return result.sort_values("orden").drop(columns="orden").reset_index(drop=True)

    def distribucion_prioridad(
        self,
        region: str | None = None,
        department: str | None = None,
    ) -> pd.DataFrame:
        data = self._filter(
            self.db.table("recomendaciones"),
            region,
            department,
        )
        if data.empty:
            return pd.DataFrame(columns=["Nivel de prioridad", "Recomendaciones"])

        result = (
            data.groupby("Nivel de prioridad", as_index=False)
            .agg(Recomendaciones=("recomendacion_id", "nunique"))
        )
        result["orden"] = (
            result["Nivel de prioridad"]
            .map(self.PRIORITY_ORDER)
            .fillna(99)
        )
        return result.sort_values("orden").drop(columns="orden").reset_index(drop=True)

    def indicadores_clave(
        self,
        region: str | None = None,
        department: str | None = None,
        year: int = 2024,
    ) -> pd.DataFrame:
        municipalities = self._municipalities(region, department)
        municipality_ids = set(municipalities["Municipio_id"].dropna())

        data = self.db.table("indicadores")
        data["Año"] = pd.to_numeric(data["Año"], errors="coerce")
        data["Valor"] = pd.to_numeric(data["Valor"], errors="coerce")
        data = data[
            data["Territorio_id"].isin(municipality_ids)
            & data["Año"].eq(year)
            & data["Indicador_codigo"].isin(["TTI", "COBERTURA"])
        ]

        if data.empty:
            return data

        return (
            data.merge(
                municipalities[[
                    "Municipio_id", "Municipio", "Departamento", "Región"
                ]],
                left_on="Territorio_id",
                right_on="Municipio_id",
                how="left",
            )
            [[
                "Municipio", "Departamento", "Región",
                "Indicador_codigo", "Indicador_nombre",
                "Año", "Valor", "Unidad",
            ]]
            .sort_values(["Indicador_codigo", "Valor"], ascending=[True, False])
            .reset_index(drop=True)
        )

    def matriz_programa_territorio(
        self,
        region: str | None = None,
        department: str | None = None,
    ) -> pd.DataFrame:
        coverage = self.cobertura_por_programa(region, department)
        opportunities = self.oportunidades_por_programa(region, department)

        result = coverage.merge(
            opportunities,
            how="outer",
            left_on=["Programa_id", "Nombre_oficial"],
            right_on=["Programa_id", "Programa"],
        )
        result["Programa"] = result["Programa"].fillna(result["Nombre_oficial"])

        for column in [
            "CAT_con_oferta", "Municipios_con_oferta",
            "Registros_de_oferta", "CAT_potenciales",
            "Municipios_potenciales", "Prioridad_alta",
        ]:
            result[column] = (
                pd.to_numeric(result[column], errors="coerce")
                .fillna(0)
                .astype(int)
            )

        return (
            result[[
                "Programa_id", "Programa",
                "CAT_con_oferta", "Municipios_con_oferta",
                "CAT_potenciales", "Municipios_potenciales",
                "Prioridad_alta",
            ]]
            .sort_values(
                ["CAT_potenciales", "CAT_con_oferta", "Programa"],
                ascending=[False, False, True],
            )
            .reset_index(drop=True)
        )
