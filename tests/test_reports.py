from pathlib import Path
from io import BytesIO
import zipfile

import pandas as pd

from config import EXCEL_FILE
from core.database import SIPCADatabase
from services.reportes import SIPCAReports


def run() -> None:
    reports = SIPCAReports(SIPCADatabase(EXCEL_FILE))

    pdf_municipality = reports.pdf_municipio('Ibagué')
    assert pdf_municipality.startswith(b'%PDF')
    assert len(pdf_municipality) > 5000

    excel_municipality = reports.excel_municipio('Ibagué')
    assert excel_municipality.startswith(b'PK')
    with zipfile.ZipFile(BytesIO(excel_municipality)) as archive:
        assert 'xl/workbook.xml' in archive.namelist()

    pdf_program = reports.pdf_programa('Ingeniería de Sistemas')
    assert pdf_program.startswith(b'%PDF')
    assert len(pdf_program) > 5000

    excel_program = reports.excel_programa('Ingeniería de Sistemas')
    assert excel_program.startswith(b'PK')

    # Regresión: una columna completamente vacía no debe romper el cálculo
    # automático del ancho en el archivo Excel.
    nullable_excel = reports._write_workbook(
        {'01_NULOS': pd.DataFrame({'campo_vacio': [None, pd.NA, None]})},
        'Prueba de columnas vacías',
    )
    assert nullable_excel.startswith(b'PK')
    with zipfile.ZipFile(BytesIO(nullable_excel)) as archive:
        assert 'xl/workbook.xml' in archive.namelist()

    output_dir = Path('reports')
    output_dir.mkdir(exist_ok=True)
    (output_dir / 'prueba_informe_municipio.pdf').write_bytes(pdf_municipality)
    (output_dir / 'prueba_informe_programa.pdf').write_bytes(pdf_program)

    print('Pruebas del Módulo 5 superadas.')
    print({
        'pdf_municipio_bytes': len(pdf_municipality),
        'excel_municipio_bytes': len(excel_municipality),
        'pdf_programa_bytes': len(pdf_program),
        'excel_programa_bytes': len(excel_program),
    })


if __name__ == '__main__':
    run()
