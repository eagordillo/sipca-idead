from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.consultas import SIPCAQueries


def main() -> None:
    db = SIPCADatabase(EXCEL_FILE).load()
    queries = SIPCAQueries(db)
    summary = db.resumen()
    assert summary["programas"] == 12
    assert summary["municipios"] == 24
    assert summary["cat"] == 25

    tourism = "Administración de Empresas Turísticas y Hoteleras"
    recommendations = db.recomendaciones_por_programa(tourism)
    assert len(recommendations) == 23
    assert recommendations["Programa base"].nunique() == 1
    assert "Pereira" in set(recommendations["Municipio"])

    opportunities = queries.ranking_oportunidades_programa(tourism)
    assert not opportunities.empty
    offered_cats = set(db.oferta_por_programa(tourism)["CAT_id"])
    assert not set(opportunities["CAT_id"]) & offered_cats
    assert "Pereira" in set(opportunities["Municipio"])

    municipal = queries.portafolio_municipal("Pereira")
    tourism_rows = municipal[
        municipal["Programa base"] == tourism
    ]
    assert not tourism_rows.empty
    assert tourism_rows.iloc[0]["Recomendado"]

    print("Pruebas del Módulo 2 superadas.")
    print(summary)
    print("Recomendaciones turísticas:", len(recommendations))
    print("CAT potenciales para turismo:", opportunities["CAT_id"].nunique())


if __name__ == "__main__":
    main()
