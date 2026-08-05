from __future__ import annotations

import pandas as pd

from core.database import SIPCADatabase


class SIPCAVisualizations:
    STATUS_ORDER = {
        "Oferta vigente": 1,
        "Pertinente y recomendado": 2,
        "Recomendado para apertura": 3,
        "Pertinente sin oferta": 4,
        "CAT activo": 5,
    }

    STATUS_COLOR = {
        "Oferta vigente": [31, 111, 67, 210],
        "Pertinente y recomendado": [30, 136, 229, 210],
        "Recomendado para apertura": [212, 167, 44, 210],
        "Pertinente sin oferta": [230, 105, 45, 210],
        "CAT activo": [107, 114, 128, 170],
    }

    def __init__(self, database: SIPCADatabase) -> None:
        self.db = database.load()

    def mapa_cat(
        self,
        program: str | None = None,
        region: str | None = None,
        department: str | None = None,
    ) -> pd.DataFrame:
        municipalities = self.db.table("municipios").copy()
        cats = self.db.table("cat").copy()
        offer = self.db.table("oferta").copy()

        municipalities["Latitud"] = pd.to_numeric(
            municipalities["Latitud"], errors="coerce"
        )
        municipalities["Longitud"] = pd.to_numeric(
            municipalities["Longitud"], errors="coerce"
        )

        data = cats.merge(
            municipalities[[
                "Municipio_id", "Región", "Latitud", "Longitud"
            ]],
            how="left",
            on="Municipio_id",
        )

        data["Estado territorial"] = "CAT activo"
        data["Programa"] = ""
        data["Nivel de pertinencia"] = ""
        data["Nivel de prioridad"] = ""
        data["Énfasis territorial"] = ""

        if program:
            program_id = self.db.resolver_programa(program)
            offered = set(
                offer.loc[
                    offer["Programa_id"] == program_id, "CAT_id"
                ].dropna().astype(str)
            )
            opportunities = self.db.oportunidades_por_programa(program)
            opportunity_by_cat = (
                opportunities.set_index("CAT_id").to_dict("index")
                if not opportunities.empty else {}
            )

            data["Programa"] = program
            for index, row in data.iterrows():
                cat_id = str(row.get("CAT_id", ""))
                if cat_id in offered:
                    data.at[index, "Estado territorial"] = "Oferta vigente"
                elif cat_id in opportunity_by_cat:
                    current = opportunity_by_cat[cat_id]
                    data.at[index, "Estado territorial"] = current.get(
                        "Estado territorial", "Pertinente sin oferta"
                    )
                    data.at[index, "Nivel de pertinencia"] = current.get(
                        "Nivel de pertinencia", ""
                    )
                    data.at[index, "Nivel de prioridad"] = current.get(
                        "Nivel de prioridad", ""
                    )
                    data.at[index, "Énfasis territorial"] = current.get(
                        "Énfasis territorial", ""
                    )

        if region and region != "Todas":
            data = data[data["Región"] == region]
        if department and department != "Todos":
            data = data[data["Departamento"] == department]

        data = data.dropna(subset=["Latitud", "Longitud"]).copy()
        data["Latitud"] = data["Latitud"].astype(float)
        data["Longitud"] = data["Longitud"].astype(float)
        data["color"] = data["Estado territorial"].map(
            self.STATUS_COLOR
        ).apply(lambda value: value or [107, 114, 128, 170])
        data["radio"] = data["Estado territorial"].map({
            "Oferta vigente": 17000,
            "Pertinente y recomendado": 15000,
            "Recomendado para apertura": 14000,
            "Pertinente sin oferta": 13000,
            "CAT activo": 9000,
        }).fillna(9000)

        data["orden_estado"] = data["Estado territorial"].map(
            self.STATUS_ORDER
        ).fillna(99)

        return (
            data.sort_values([
                "orden_estado", "Departamento", "Municipio", "Nombre_cat"
            ])
            .drop(columns="orden_estado")
            .reset_index(drop=True)
        )

    def resumen_cobertura(self, data: pd.DataFrame) -> dict[str, int]:
        opportunities = data[data["Estado territorial"].isin([
            "Pertinente y recomendado",
            "Recomendado para apertura",
            "Pertinente sin oferta",
        ])]
        return {
            "cat": int(data["CAT_id"].nunique()) if not data.empty else 0,
            "municipios": int(data["Municipio_id"].nunique()) if not data.empty else 0,
            "departamentos": int(data["Departamento"].nunique()) if not data.empty else 0,
            "oferta": int(
                data.loc[
                    data["Estado territorial"] == "Oferta vigente", "CAT_id"
                ].nunique()
            ) if not data.empty else 0,
            "oportunidades": int(opportunities["CAT_id"].nunique()),
        }

    def indicadores_municipales(
        self,
        municipality: str,
        codes: list[str] | None = None,
    ) -> pd.DataFrame:
        municipality_id = self.db.resolver_municipio(municipality)
        data = self.db.indicadores_territorio(municipality_id, codes=codes)
        data = data.copy()
        data["Año"] = pd.to_numeric(data["Año"], errors="coerce")
        data["Valor"] = pd.to_numeric(data["Valor"], errors="coerce")
        return data.dropna(subset=["Año", "Valor"]).reset_index(drop=True)
