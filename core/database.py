from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import re
import unicodedata

import pandas as pd

from core.program_rules import normalize_program_name, text_key


class SIPCADataError(RuntimeError):
    """Error controlado durante la lectura o validación del modelo de datos."""


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    component: str
    message: str
    count: int = 1


class SIPCADatabase:
    """Capa única de acceso al Modelo de Datos SIPCA v1.0.

    La interfaz y los servicios deben consultar esta clase en lugar de leer
    directamente las hojas de Excel. Esto permite sustituir Excel por otra
    fuente de datos en el futuro sin reescribir toda la aplicación.
    """

    SHEETS = {
        "control": "00_CONTROL",
        "regiones": "01_REGIONES",
        "departamentos": "02_DEPARTAMENTOS",
        "municipios": "03_MUNICIPIOS",
        "oferta": "04_PROGRAMAS OFERTADOS IDEAD",
        "cat": "05_CAT",
        "perfiles": "06_PERFILES_TERRITORIALES",
        "pertinencia": "07_PERTINENCIA_PROGRAMA",
        "recomendaciones": "08_PROGRAMAS_RECOMENDADOS",
        "indicadores": "09_INDICADORES",
        "fuentes": "10_FUENTES",
        "parametros": "11_PARAMETROS",
    }

    REQUIRED_COLUMNS = {
        "municipios": {
            "Municipio_id", "Municipio", "Departamento", "Región",
            "Latitud", "Longitud", "Activo"
        },
        "oferta": {
            "Programa_id", "Nombre_oficial", "Municipio_id",
            "Municipio de oferta", "Modalidad", "Estado_oferta", "CAT_id"
        },
        "cat": {
            "CAT_id", "Nombre_cat", "Municipio", "Departamento",
            "Municipio_id", "Estado_CAT"
        },
        "perfiles": {
            "Municipio", "Departamento", "Perfil territorial integrado",
            "Necesidades formativas prioritarias"
        },
        "pertinencia": {
            "pertinencia_id", "Programa IDEAD", "Municipio", "Departamento",
            "Nivel de pertinencia", "Programa_id", "Municipio_id"
        },
        "recomendaciones": {
            "recomendacion_id", "Programa recomendado", "Municipio",
            "Departamento", "Nivel de prioridad", "Municipio_id"
        },
        "indicadores": {
            "Indicador_registro_id", "Indicador_codigo", "Indicador_nombre",
            "Nivel_territorial", "Territorio", "Territorio_id", "Año",
            "Valor", "Unidad", "Fuente_id"
        },
    }

    def __init__(self, excel_path: str | Path) -> None:
        self.excel_path = Path(excel_path)
        self._tables: dict[str, pd.DataFrame] = {}
        self._loaded = False

    @staticmethod
    def _text(value: Any) -> str:
        if pd.isna(value):
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    @classmethod
    def _key(cls, value: Any) -> str:
        text = unicodedata.normalize("NFKD", cls._text(value).casefold())
        return "".join(char for char in text if not unicodedata.combining(char))

    @staticmethod
    def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
        clean = df.copy()
        clean.columns = [str(column).strip() for column in clean.columns]
        removable = [
            column for column in clean.columns
            if column.startswith("Unnamed:") or column.startswith("¿Qué contiene")
        ]
        if removable:
            clean = clean.drop(columns=removable)
        return clean.dropna(how="all").reset_index(drop=True)

    def load(self, force: bool = False) -> "SIPCADatabase":
        if self._loaded and not force:
            return self
        if not self.excel_path.exists():
            raise SIPCADataError(f"No se encontró el modelo de datos: {self.excel_path}")

        try:
            workbook = pd.ExcelFile(self.excel_path, engine="openpyxl")
        except Exception as exc:
            raise SIPCADataError("No fue posible abrir el archivo Excel de SIPCA.") from exc

        missing_sheets = sorted(set(self.SHEETS.values()) - set(workbook.sheet_names))
        if missing_sheets:
            raise SIPCADataError(
                "Faltan hojas obligatorias: " + ", ".join(missing_sheets)
            )

        loaded: dict[str, pd.DataFrame] = {}
        for alias, sheet_name in self.SHEETS.items():
            loaded[alias] = self._clean_columns(
                pd.read_excel(workbook, sheet_name=sheet_name)
            )

        self._tables = loaded
        self._prepare_relations()
        self._loaded = True
        return self

    def _prepare_relations(self) -> None:
        oferta = self._tables["oferta"].copy()
        oferta["Nombre_oficial"] = oferta["Nombre_oficial"].map(self._text)
        oferta["Programa_id"] = oferta["Programa_id"].map(self._text)
        oferta["Municipio_id"] = oferta["Municipio_id"].map(self._text)
        oferta["CAT_id"] = oferta["CAT_id"].map(self._text)
        oferta["programa_clave"] = oferta["Nombre_oficial"].map(self._key)
        self._tables["oferta"] = oferta

        catalogo = (
            oferta[["Programa_id", "Nombre_oficial", "Nivel_formacion", "Nombre_corto"]]
            .drop_duplicates(subset=["Programa_id", "Nombre_oficial"])
            .sort_values("Nombre_oficial")
            .reset_index(drop=True)
        )
        catalogo["programa_clave"] = catalogo["Nombre_oficial"].map(self._key)
        self._tables["programas"] = catalogo

        id_by_name = dict(zip(catalogo["programa_clave"], catalogo["Programa_id"]))

        # El nombre oficial es la referencia semántica para resolver posibles
        # IDs históricos que aún permanezcan en la matriz de pertinencia.
        pertinencia = self._tables["pertinencia"].copy()
        pertinencia["Programa IDEAD"] = pertinencia["Programa IDEAD"].map(self._text)
        pertinencia["programa_clave"] = pertinencia["Programa IDEAD"].map(self._key)
        pertinencia["Programa_id_original"] = pertinencia["Programa_id"].map(self._text)
        pertinencia["Programa_id_resuelto"] = pertinencia["programa_clave"].map(id_by_name)
        pertinencia["Programa_id"] = pertinencia["Programa_id_resuelto"].fillna(
            pertinencia["Programa_id_original"]
        )
        self._tables["pertinencia"] = pertinencia

        recomendaciones = self._tables["recomendaciones"].copy()
        recomendaciones["Programa recomendado"] = recomendaciones[
            "Programa recomendado"
        ].map(self._text)
        normalized = recomendaciones["Programa recomendado"].map(normalize_program_name)
        recomendaciones["Programa base"] = normalized.map(lambda item: item.base_name)
        recomendaciones["programa_base_clave"] = normalized.map(lambda item: item.base_key)
        recomendaciones["Énfasis territorial"] = normalized.map(lambda item: item.emphasis)
        recomendaciones["programa_recomendado_clave"] = recomendaciones[
            "Programa recomendado"
        ].map(self._key)
        self._tables["recomendaciones"] = recomendaciones

        for alias in ("municipios", "cat", "perfiles", "indicadores"):
            table = self._tables[alias].copy()
            for column in table.columns:
                if table[column].dtype == "object":
                    table[column] = table[column].map(
                        lambda value: self._text(value) if not pd.isna(value) else value
                    )
            self._tables[alias] = table

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def table(self, name: str) -> pd.DataFrame:
        self._ensure_loaded()
        if name not in self._tables:
            raise KeyError(f"Tabla no disponible: {name}")
        return self._tables[name].copy()

    def resumen(self) -> dict[str, int]:
        self._ensure_loaded()
        return {
            "programas": self._tables["programas"]["Programa_id"].nunique(),
            "municipios": self._tables["municipios"]["Municipio_id"].nunique(),
            "cat": self._tables["cat"]["CAT_id"].nunique(),
            "ofertas": len(self._tables["oferta"]),
            "pertinencias": len(self._tables["pertinencia"]),
            "recomendaciones": len(self._tables["recomendaciones"]),
            "indicadores": len(self._tables["indicadores"]),
        }

    def obtener_programas(self, solo_activos: bool = True) -> pd.DataFrame:
        self._ensure_loaded()
        programas = self._tables["programas"].copy()
        if solo_activos:
            activos = set(
                self._tables["oferta"]
                .loc[self._tables["oferta"]["Estado_oferta"].str.casefold() == "activo", "Programa_id"]
            )
            programas = programas[programas["Programa_id"].isin(activos)]
        return programas.sort_values("Nombre_oficial").reset_index(drop=True)

    def obtener_municipios(
        self,
        departamento: str | None = None,
        region: str | None = None,
        solo_activos: bool = True,
    ) -> pd.DataFrame:
        self._ensure_loaded()
        data = self._tables["municipios"].copy()
        if solo_activos and "Activo" in data.columns:
            data = data[data["Activo"].fillna(False).astype(bool)]
        if departamento:
            data = data[data["Departamento"].map(self._key) == self._key(departamento)]
        if region:
            data = data[data["Región"].map(self._key) == self._key(region)]
        return data.sort_values(["Departamento", "Municipio"]).reset_index(drop=True)

    def obtener_cat(self, municipio_id: str | None = None) -> pd.DataFrame:
        self._ensure_loaded()
        data = self._tables["cat"].copy()
        if municipio_id:
            data = data[data["Municipio_id"] == municipio_id]
        return data.sort_values("Nombre_cat").reset_index(drop=True)

    def resolver_programa(self, program: str) -> str:
        self._ensure_loaded()
        catalogo = self._tables["programas"]
        by_id = catalogo[catalogo["Programa_id"] == self._text(program)]
        if not by_id.empty:
            return str(by_id.iloc[0]["Programa_id"])
        by_name = catalogo[catalogo["programa_clave"] == self._key(program)]
        if by_name.empty:
            raise SIPCADataError(f"Programa no encontrado: {program}")
        return str(by_name.iloc[0]["Programa_id"])

    def resolver_municipio(self, municipality: str) -> str:
        self._ensure_loaded()
        municipios = self._tables["municipios"]
        by_id = municipios[municipios["Municipio_id"] == self._text(municipality)]
        if not by_id.empty:
            return str(by_id.iloc[0]["Municipio_id"])
        by_name = municipios[municipios["Municipio"].map(self._key) == self._key(municipality)]
        if by_name.empty:
            raise SIPCADataError(f"Municipio no encontrado: {municipality}")
        return str(by_name.iloc[0]["Municipio_id"])

    def oferta_por_programa(self, program: str) -> pd.DataFrame:
        program_id = self.resolver_programa(program)
        oferta = self._tables["oferta"]
        cat = self._tables["cat"][["CAT_id", "Nombre_cat"]].drop_duplicates()
        result = oferta[oferta["Programa_id"] == program_id].merge(
            cat, how="left", on="CAT_id"
        )
        columns = [
            "Programa_id", "Nombre_oficial", "CAT_id", "Nombre_cat",
            "Municipio_id", "Municipio de oferta", "Modalidad", "Estado_oferta"
        ]
        return result[columns].sort_values(
            ["Municipio de oferta", "Nombre_cat"]
        ).reset_index(drop=True)

    def pertinencia_por_programa(
        self,
        program: str,
        nivel: str | None = None,
    ) -> pd.DataFrame:
        program_id = self.resolver_programa(program)
        result = self._tables["pertinencia"]
        result = result[result["Programa_id"] == program_id].copy()
        if nivel:
            result = result[
                result["Nivel de pertinencia"].map(self._key).str.contains(
                    self._key(nivel), na=False
                )
            ]
        return result.sort_values(
            ["Nivel de pertinencia", "Departamento", "Municipio"]
        ).reset_index(drop=True)

    def recomendaciones_por_programa(self, program: str) -> pd.DataFrame:
        """Obtiene recomendaciones equivalentes al programa oficial seleccionado."""
        program_id = self.resolver_programa(program)
        program_row = self._tables["programas"].query(
            "Programa_id == @program_id"
        ).iloc[0]
        official_key = text_key(program_row["Nombre_oficial"])
        data = self._tables["recomendaciones"].copy()
        result = data[data["programa_base_clave"] == official_key].copy()
        return result.sort_values(
            ["Departamento", "Municipio", "Programa recomendado"]
        ).reset_index(drop=True)

    def oportunidades_por_programa(self, program: str) -> pd.DataFrame:
        """Proyecta pertinencia y recomendaciones sobre CAT sin oferta vigente."""
        program_id = self.resolver_programa(program)
        offer = self.oferta_por_programa(program_id)
        offered_cat = set(offer["CAT_id"].dropna().map(self._text))

        relevance = self.pertinencia_por_programa(program_id).copy()
        recommendations = self.recomendaciones_por_programa(program_id).copy()

        relevant_by_mun = {
            self._text(row["Municipio_id"]): row
            for _, row in relevance.iterrows()
        }
        recommended_by_mun = {
            self._text(row["Municipio_id"]): row
            for _, row in recommendations.iterrows()
            if self._text(row.get("Municipio_id"))
        }
        candidate_municipalities = set(relevant_by_mun) | set(recommended_by_mun)

        cats = self._tables["cat"].copy()
        cats = cats[
            cats["Estado_CAT"].map(self._key).eq(self._key("Activo"))
            & cats["Municipio_id"].isin(candidate_municipalities)
            & ~cats["CAT_id"].isin(offered_cat)
        ]

        rows: list[dict[str, Any]] = []
        for _, cat_row in cats.iterrows():
            municipality_id = self._text(cat_row["Municipio_id"])
            rel = relevant_by_mun.get(municipality_id)
            rec = recommended_by_mun.get(municipality_id)
            if rel is not None and rec is not None:
                status = "Pertinente y recomendado"
            elif rec is not None:
                status = "Recomendado para apertura"
            else:
                status = "Pertinente sin oferta"

            rows.append({
                "CAT_id": cat_row.get("CAT_id", ""),
                "Nombre_cat": cat_row.get("Nombre_cat", ""),
                "Municipio_id": municipality_id,
                "Municipio": cat_row.get("Municipio", ""),
                "Departamento": cat_row.get("Departamento", ""),
                "Estado territorial": status,
                "Nivel de pertinencia": rel.get("Nivel de pertinencia", "") if rel is not None else "",
                "Nivel de prioridad": rec.get("Nivel de prioridad", "") if rec is not None else "",
                "Énfasis territorial": rec.get("Énfasis territorial", "") if rec is not None else "",
                "Modalidad sugerida": (
                    rec.get("Modalidad recomendada", "") if rec is not None
                    else rel.get("Modalidad sugerida", "") if rel is not None else ""
                ),
                "TTI municipal 2024 (%)": (
                    rel.get("TTI municipal 2024 (%)", None) if rel is not None
                    else rec.get("TTI municipal 2024 (%)", None) if rec is not None else None
                ),
                "Cobertura municipal 2024 (%)": (
                    rel.get("Cobertura municipal 2024 (%)", None) if rel is not None
                    else rec.get("Cobertura municipal 2024 (%)", None) if rec is not None else None
                ),
                "Bachilleres grado 11 (2023)": (
                    rel.get("Bachilleres grado 11 (2023)", None) if rel is not None
                    else rec.get("Bachilleres grado 11 (2023)", None) if rec is not None else None
                ),
                "Justificación": (
                    rec.get("Justificación técnica Municipio–programa", "") if rec is not None
                    else rel.get("Justificación específica municipio–programa", "") if rel is not None else ""
                ),
            })

        columns = [
            "CAT_id", "Nombre_cat", "Municipio_id", "Municipio", "Departamento",
            "Estado territorial", "Nivel de pertinencia", "Nivel de prioridad",
            "Énfasis territorial", "Modalidad sugerida", "TTI municipal 2024 (%)",
            "Cobertura municipal 2024 (%)", "Bachilleres grado 11 (2023)",
            "Justificación",
        ]
        return pd.DataFrame(rows, columns=columns)

    def portafolio_por_municipio(self, municipality: str) -> pd.DataFrame:
        """Integra oferta, pertinencia y recomendaciones para un municipio."""
        municipality_id = self.resolver_municipio(municipality)
        offer = self.oferta_por_municipio(municipality_id)
        relevance = self.pertinencia_por_municipio(municipality_id)
        recommendations = self.recomendaciones_por_municipio(municipality_id)

        entries: dict[str, dict[str, Any]] = {}

        for _, row in offer.iterrows():
            name = self._text(row["Nombre_oficial"])
            key = text_key(name)
            entry = entries.setdefault(key, {
                "Programa base": name, "Programa_id": row.get("Programa_id", ""),
                "Oferta vigente": False, "Pertinente": False, "Recomendado": False,
                "CAT con oferta": [], "Nivel de pertinencia": "",
                "Nivel de prioridad": "", "Énfasis territorial": "",
                "Justificación": "",
            })
            entry["Oferta vigente"] = True
            cat_id = self._text(row.get("CAT_id"))
            if cat_id and cat_id not in entry["CAT con oferta"]:
                entry["CAT con oferta"].append(cat_id)

        for _, row in relevance.iterrows():
            name = self._text(row["Programa IDEAD"])
            key = text_key(name)
            entry = entries.setdefault(key, {
                "Programa base": name, "Programa_id": row.get("Programa_id", ""),
                "Oferta vigente": False, "Pertinente": False, "Recomendado": False,
                "CAT con oferta": [], "Nivel de pertinencia": "",
                "Nivel de prioridad": "", "Énfasis territorial": "",
                "Justificación": "",
            })
            entry["Pertinente"] = True
            entry["Nivel de pertinencia"] = row.get("Nivel de pertinencia", "")
            entry["Justificación"] = row.get("Justificación específica municipio–programa", "")

        for _, row in recommendations.iterrows():
            name = self._text(row["Programa base"])
            key = text_key(name)
            entry = entries.setdefault(key, {
                "Programa base": name, "Programa_id": "",
                "Oferta vigente": False, "Pertinente": False, "Recomendado": False,
                "CAT con oferta": [], "Nivel de pertinencia": "",
                "Nivel de prioridad": "", "Énfasis territorial": "",
                "Justificación": "",
            })
            entry["Recomendado"] = True
            entry["Nivel de prioridad"] = row.get("Nivel de prioridad", "")
            entry["Énfasis territorial"] = row.get("Énfasis territorial", "")
            entry["Justificación"] = row.get("Justificación técnica Municipio–programa", "") or entry["Justificación"]

        rows = []
        for entry in entries.values():
            if entry["Oferta vigente"]:
                status = "Oferta vigente"
            elif entry["Pertinente"] and entry["Recomendado"]:
                status = "Pertinente y recomendado"
            elif entry["Pertinente"]:
                status = "Pertinente sin oferta"
            else:
                status = "Recomendado para apertura"
            rows.append({
                **entry,
                "CAT con oferta": ", ".join(entry["CAT con oferta"]),
                "Estado territorial": status,
            })

        columns = [
            "Programa base", "Programa_id", "Estado territorial",
            "Oferta vigente", "Pertinente", "Recomendado", "CAT con oferta",
            "Nivel de pertinencia", "Nivel de prioridad", "Énfasis territorial",
            "Justificación",
        ]
        return pd.DataFrame(rows, columns=columns)

    def ficha_programa_inteligente(self, program: str) -> dict[str, Any]:
        base = self.ficha_programa(program)
        base["recomendaciones"] = self.recomendaciones_por_programa(program)
        base["oportunidades"] = self.oportunidades_por_programa(program)
        return base

    def ficha_municipio_inteligente(self, municipality: str) -> dict[str, Any]:
        base = self.ficha_municipio(municipality)
        base["portafolio"] = self.portafolio_por_municipio(municipality)
        return base

    def ficha_programa(self, program: str) -> dict[str, Any]:
        program_id = self.resolver_programa(program)
        program_row = self._tables["programas"].query(
            "Programa_id == @program_id"
        ).iloc[0].to_dict()
        return {
            "programa": program_row,
            "oferta": self.oferta_por_programa(program_id),
            "pertinencia": self.pertinencia_por_programa(program_id),
        }

    def perfil_municipio(self, municipality: str) -> pd.DataFrame:
        municipality_id = self.resolver_municipio(municipality)
        municipality_row = self._tables["municipios"].query(
            "Municipio_id == @municipality_id"
        ).iloc[0]
        result = self._tables["perfiles"]
        mask = (
            result["Municipio"].map(self._key)
            == self._key(municipality_row["Municipio"])
        )
        return result[mask].reset_index(drop=True)

    def oferta_por_municipio(self, municipality: str) -> pd.DataFrame:
        municipality_id = self.resolver_municipio(municipality)
        result = self._tables["oferta"]
        result = result[result["Municipio_id"] == municipality_id]
        return result.sort_values(["Nombre_oficial", "CAT_id"]).reset_index(drop=True)

    def pertinencia_por_municipio(self, municipality: str) -> pd.DataFrame:
        municipality_id = self.resolver_municipio(municipality)
        result = self._tables["pertinencia"]
        result = result[result["Municipio_id"] == municipality_id]
        return result.sort_values(["Nivel de pertinencia", "Programa IDEAD"]).reset_index(drop=True)

    def recomendaciones_por_municipio(self, municipality: str) -> pd.DataFrame:
        municipality_id = self.resolver_municipio(municipality)
        result = self._tables["recomendaciones"]
        result = result[result["Municipio_id"] == municipality_id]
        return result.sort_values(
            ["Nivel de prioridad", "Programa recomendado"]
        ).reset_index(drop=True)

    def indicadores_territorio(
        self,
        territory: str,
        codes: Iterable[str] | None = None,
    ) -> pd.DataFrame:
        self._ensure_loaded()
        data = self._tables["indicadores"].copy()
        territory_text = self._text(territory)
        mask = (
            (data["Territorio_id"] == territory_text)
            | (data["Territorio"].map(self._key) == self._key(territory_text))
        )
        data = data[mask]
        if codes:
            normalized = {self._text(code).upper() for code in codes}
            data = data[data["Indicador_codigo"].str.upper().isin(normalized)]
        return data.sort_values(["Indicador_codigo", "Año"]).reset_index(drop=True)

    def ficha_municipio(self, municipality: str) -> dict[str, Any]:
        municipality_id = self.resolver_municipio(municipality)
        municipality_row = self._tables["municipios"].query(
            "Municipio_id == @municipality_id"
        ).iloc[0].to_dict()
        return {
            "municipio": municipality_row,
            "cat": self.obtener_cat(municipality_id),
            "perfil": self.perfil_municipio(municipality_id),
            "oferta": self.oferta_por_municipio(municipality_id),
            "pertinencia": self.pertinencia_por_municipio(municipality_id),
            "recomendaciones": self.recomendaciones_por_municipio(municipality_id),
            "indicadores": self.indicadores_territorio(municipality_id),
        }

    def validate(self) -> list[ValidationIssue]:
        self._ensure_loaded()
        issues: list[ValidationIssue] = []

        for alias, required in self.REQUIRED_COLUMNS.items():
            missing = required - set(self._tables[alias].columns)
            if missing:
                issues.append(ValidationIssue(
                    "critical", alias,
                    "Columnas obligatorias ausentes: " + ", ".join(sorted(missing)),
                    len(missing),
                ))

        municipios = set(self._tables["municipios"]["Municipio_id"].dropna())
        cats = set(self._tables["cat"]["CAT_id"].dropna())
        programas = set(self._tables["programas"]["Programa_id"].dropna())
        fuentes = set(self._tables["fuentes"]["fuente_id"].dropna())

        checks = [
            ("oferta", "Municipio_id", municipios, "municipios"),
            ("oferta", "CAT_id", cats, "CAT"),
            ("pertinencia", "Municipio_id", municipios, "municipios"),
            ("pertinencia", "Programa_id", programas, "programas"),
            ("recomendaciones", "Municipio_id", municipios, "municipios"),
            ("indicadores", "Fuente_id", fuentes, "fuentes"),
        ]
        for alias, column, valid, target in checks:
            values = set(self._tables[alias][column].dropna())
            invalid = sorted(value for value in values if value not in valid and value != "")
            if invalid:
                issues.append(ValidationIssue(
                    "high", alias,
                    f"Referencias de {column} que no existen en {target}: {invalid}",
                    len(invalid),
                ))

        program_catalog = dict(zip(
            self._tables["programas"]["programa_clave"],
            self._tables["programas"]["Programa_id"],
        ))
        pertinencia = self._tables["pertinencia"]
        mismatches = pertinencia[
            pertinencia["programa_clave"].map(program_catalog)
            != pertinencia["Programa_id_original"]
        ]
        if not mismatches.empty:
            issues.append(ValidationIssue(
                "warning", "pertinencia",
                "Se detectaron IDs históricos de programa; SIPCADatabase los resuelve por nombre oficial durante la carga.",
                len(mismatches),
            ))

        duplicate_offer = self._tables["oferta"].duplicated(
            ["Programa_id", "Municipio_id", "CAT_id"], keep=False
        ).sum()
        if duplicate_offer:
            issues.append(ValidationIssue(
                "warning", "oferta",
                "Registros repetidos para la combinación programa–municipio–CAT.",
                int(duplicate_offer),
            ))

        duplicate_relevance = self._tables["pertinencia"].duplicated(
            ["Programa_id", "Municipio_id"], keep=False
        ).sum()
        if duplicate_relevance:
            issues.append(ValidationIssue(
                "warning", "pertinencia",
                "Relaciones repetidas para la combinación programa–municipio.",
                int(duplicate_relevance),
            ))

        missing_year = int(self._tables["indicadores"]["Año"].isna().sum())
        if missing_year:
            issues.append(ValidationIssue(
                "warning", "indicadores",
                "Indicadores sin año de referencia; no deben usarse en análisis temporales.",
                missing_year,
            ))

        return issues

    def health_report(self) -> pd.DataFrame:
        issues = self.validate()
        if not issues:
            return pd.DataFrame([{
                "severidad": "ok", "componente": "modelo",
                "mensaje": "El modelo superó las validaciones automáticas.", "cantidad": 0,
            }])
        return pd.DataFrame([
            {
                "severidad": issue.severity,
                "componente": issue.component,
                "mensaje": issue.message,
                "cantidad": issue.count,
            }
            for issue in issues
        ])
