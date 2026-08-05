from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.visualizaciones import SIPCAVisualizations


def run() -> None:
    visuals = SIPCAVisualizations(SIPCADatabase(EXCEL_FILE))
    data = visuals.mapa_cat()
    assert not data.empty
    assert data["Latitud"].dtype.kind == "f"
    assert data["Longitud"].dtype.kind == "f"

    tourism = visuals.mapa_cat(
        program="Administración de Empresas Turísticas y Hoteleras"
    )
    summary = visuals.resumen_cobertura(tourism)
    assert summary["oferta"] == 5
    assert summary["oportunidades"] > 0

    indicators = visuals.indicadores_municipales(
        "Ibagué", ["TTI", "COBERTURA"]
    )
    assert not indicators.empty

    print("Pruebas del Módulo 3.2 superadas.")
    print(summary)


if __name__ == "__main__":
    run()
