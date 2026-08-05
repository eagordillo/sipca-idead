from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.dashboard import SIPCADashboard


def run() -> None:
    dashboard = SIPCADashboard(SIPCADatabase(EXCEL_FILE))

    summary = dashboard.resumen()
    assert summary["programas"] == 12
    assert summary["cat"] == 25
    assert summary["municipios_catalogo"] == 24
    assert summary["municipios_con_cat"] == 23

    coverage = dashboard.cobertura_por_programa()
    assert not coverage.empty
    assert coverage["Programa_id"].nunique() == 12

    opportunities = dashboard.oportunidades_por_programa()
    assert not opportunities.empty

    recommendations = dashboard.recomendaciones_por_municipio()
    assert not recommendations.empty

    relevance = dashboard.distribucion_pertinencia()
    assert not relevance.empty

    priority = dashboard.distribucion_prioridad()
    assert not priority.empty

    indicators = dashboard.indicadores_clave(year=2024)
    assert not indicators.empty

    matrix = dashboard.matriz_programa_territorio()
    assert len(matrix) == 12

    print("Pruebas del Módulo 4 superadas.")
    print(summary)


if __name__ == "__main__":
    run()
