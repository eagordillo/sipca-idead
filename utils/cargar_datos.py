from __future__ import annotations
import re
import unicodedata
from pathlib import Path
from typing import Dict, List
import pandas as pd
from config import DEPARTAMENTO_POR_MUNICIPIO, HOJAS_TERRITORIALES, REGION_POR_DEPARTAMENTO

class ErrorDatosCobertura(Exception):
    pass

def limpiar_texto(valor) -> str:
    if pd.isna(valor):
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()

def clave_texto(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", limpiar_texto(valor).lower())
    return "".join(c for c in texto if not unicodedata.combining(c))

def dividir_programas(texto: str) -> List[str]:
    texto = limpiar_texto(texto)
    return [x.strip(" .") for x in texto.split(";") if x.strip(" .")] if texto else []

def validar_archivo(ruta: Path) -> None:
    if not ruta.exists():
        raise ErrorDatosCobertura(f"No se encontró el archivo: {ruta}")

def cargar_hoja_territorial(ruta: Path, hoja: str, cfg: Dict) -> pd.DataFrame:
    df = pd.read_excel(ruta, sheet_name=hoja, header=cfg["fila_encabezado"], engine="openpyxl")
    df = df.iloc[:, :4].copy()
    df.columns = ["municipio","perfil_necesidades","programas_idead","programas_recomendados"]
    for c in df.columns:
        df[c] = df[c].map(limpiar_texto)
    df = df[df["municipio"] != ""].copy()
    df["fuente_hoja"] = hoja
    df["departamento"] = cfg["departamento_default"] or df["municipio"].map(DEPARTAMENTO_POR_MUNICIPIO)
    df["region"] = cfg["region_default"] or df["departamento"].map(REGION_POR_DEPARTAMENTO)
    df["programas_idead_lista"] = df["programas_idead"].map(dividir_programas)
    df["programas_recomendados_lista"] = df["programas_recomendados"].map(dividir_programas)
    df["municipio_clave"] = df["municipio"].map(clave_texto)
    return df

def cargar_base_territorial(ruta: Path) -> pd.DataFrame:
    validar_archivo(ruta)
    marcos = [cargar_hoja_territorial(ruta, h, c) for h, c in HOJAS_TERRITORIALES.items()]
    base = pd.concat(marcos, ignore_index=True)
    base = base.drop_duplicates(["municipio_clave","departamento"])
    return base.sort_values(["departamento","municipio"]).reset_index(drop=True)

def cargar_indicadores(ruta: Path) -> pd.DataFrame:
    df = pd.read_excel(ruta, sheet_name="Indicadores nacionales", header=0, engine="openpyxl")
    df = df[df["Departamento"].notna() & df["Municipio"].notna()].copy()
    df = df.iloc[:, :13]
    df.columns = [
        "tti_nacional_2024","cobertura_nacional_2024","departamento",
        "tti_departamental_2023","tti_departamental_2024",
        "cobertura_departamental_2023","cobertura_departamental_2024",
        "municipio","tti_municipal_2023","tti_municipal_2024",
        "cobertura_municipal_2023","cobertura_municipal_2024",
        "bachilleres_grado_11_2023"
    ]
    df["municipio"] = df["municipio"].map(limpiar_texto)
    df["departamento"] = df["departamento"].map(limpiar_texto)
    df["municipio_clave"] = df["municipio"].map(clave_texto)
    return df

def construir_base_maestra(ruta: Path) -> pd.DataFrame:
    territorial = cargar_base_territorial(ruta)
    indicadores = cargar_indicadores(ruta)
    return territorial.merge(indicadores, how="left", on=["municipio_clave","departamento"], suffixes=("","_indicador"))

def crear_catalogo_programas(base: pd.DataFrame) -> List[str]:
    programas = set()
    for lista in base["programas_idead_lista"]:
        programas.update(lista)
    return sorted(programas, key=clave_texto)

def filtrar_por_programa(base: pd.DataFrame, programa: str) -> pd.DataFrame:
    objetivo = clave_texto(programa)
    mask = base["programas_idead_lista"].map(
        lambda lista: any(objetivo in clave_texto(x) or clave_texto(x) in objetivo for x in lista)
    )
    return base[mask].copy()
