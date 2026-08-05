# SIPCA – Aplicación Web v1.0

## Módulo 2: motor inteligente de consultas territoriales

Este módulo amplía el núcleo del Módulo 1 y resuelve dos preguntas institucionales:

1. **Consulta por programa:** dónde se oferta actualmente y en qué CAT podría ampliarse.
2. **Consulta por municipio:** qué programas se ofertan, cuáles son pertinentes y cuáles se recomiendan.

### Funciones incorporadas

- Normalización de programas recomendados con énfasis territorial.
- Equivalencia entre `Administración Turística y Hotelera` y el nombre oficial del programa IDEAD.
- Extracción del énfasis como un dato independiente.
- Identificación de CAT potenciales sin confundirlos con la oferta vigente.
- Portafolio territorial consolidado por municipio.
- Separación entre:
  - Oferta vigente.
  - Pertinente sin oferta.
  - Recomendado para apertura.
  - Pertinente y recomendado.

### Instalación y ejecución

```powershell
python -m pip install -r requirements.txt
python -m tests.test_database
python -m streamlit run app.py
```

### Actualización sobre una instalación existente

Detenga Streamlit con `Ctrl + C`, conserve la carpeta `.venv` y copie el contenido de este proyecto sobre `D:\SIPCA_IDEAD`, reemplazando los archivos existentes.


## Módulo 2.1 — Ajuste de navegación

- Se eliminó la pestaña independiente de pertinencia en la consulta por programa.
- Las oportunidades de ampliación integran pertinencia y recomendaciones.
- La consulta por municipio se ordena así: Perfil territorial, Oferta vigente,
  Portafolio territorial, Recomendaciones e Indicadores.
- Se eliminó la pestaña municipal de pertinencia por ser redundante.


## Módulo 3.2 — Reconstrucción limpia

- Construido directamente sobre el Módulo 2.1.
- Se eliminó la página redundante de Cobertura nacional.
- El mapa utiliza PyDeck y no Plotly Express.
- Las coordenadas se convierten a `float` antes de la visualización.
- La carpeta `pages` contiene únicamente las páginas vigentes.


## Módulo 3.3 — Ajustes de cobertura

- Se eliminó definitivamente la página heredada de Cobertura nacional.
- El mapa territorial utiliza un zoom dinámico según la dispersión de los CAT visibles.
- La vista inicial queda centrada sobre los CAT y no sobre toda Sudamérica.
- La carpeta `pages` contiene una única página de cobertura.


## Módulo 4 — Dashboard ejecutivo

Incluye filtros por región y departamento, indicadores institucionales,
cobertura actual por programa, oportunidades de ampliación, distribución
de pertinencia, prioridades, matriz ejecutiva programa–territorio,
ranking de municipios e indicadores educativos de 2024.


## Módulo 5 - Informes y exportaciones

Incluye:

- informe territorial por municipio en PDF;
- anexos por municipio en Excel;
- informe de cobertura y expansión por programa en PDF;
- anexos por programa en Excel;
- perfil, oferta, portafolio, recomendaciones, indicadores y fuentes;
- generación en memoria, sin modificar el Excel maestro.

Dependencias adicionales:

```powershell
python -m pip install reportlab xlsxwriter
```


## Módulo 5.1 - Corrección de exportación Excel

- Se corrigió el cálculo automático del ancho para columnas completamente vacías.
- Se agregó una prueba de regresión con valores `None` y `pd.NA`.
- La generación de PDF y Excel por municipio y programa permanece sin cambios funcionales.
