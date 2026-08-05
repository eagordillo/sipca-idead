from __future__ import annotations

from datetime import datetime
from io import BytesIO
from html import escape
import re
from typing import Iterable

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.database import SIPCADatabase
from services.consultas import SIPCAQueries


class SIPCAReports:
    """Genera informes descargables sin modificar el Excel maestro."""

    GREEN = colors.HexColor('#1F6F43')
    DARK_GREEN = colors.HexColor('#174F32')
    LIGHT_GREEN = colors.HexColor('#EAF5EE')
    LIGHT_GRAY = colors.HexColor('#F3F4F6')
    DARK = colors.HexColor('#1F2937')
    MUTED = colors.HexColor('#6B7280')

    def __init__(self, database: SIPCADatabase) -> None:
        self.db = database.load()
        self.queries = SIPCAQueries(self.db)
        self.styles = self._styles()

    @staticmethod
    def safe_filename(value: str) -> str:
        text = re.sub(r'[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñ_-]+', '_', str(value).strip())
        return re.sub(r'_+', '_', text).strip('_') or 'informe'

    @staticmethod
    def _text(value) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ''
        return str(value).strip()

    def _styles(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='SIPCATitle', parent=styles['Title'], fontName='Helvetica-Bold',
            fontSize=22, leading=26, textColor=self.DARK_GREEN,
            alignment=TA_CENTER, spaceAfter=12,
        ))
        styles.add(ParagraphStyle(
            name='SIPCASubtitle', parent=styles['Normal'], fontName='Helvetica',
            fontSize=11, leading=15, textColor=self.MUTED,
            alignment=TA_CENTER, spaceAfter=18,
        ))
        styles.add(ParagraphStyle(
            name='SIPCAH1', parent=styles['Heading1'], fontName='Helvetica-Bold',
            fontSize=15, leading=19, textColor=self.DARK_GREEN,
            spaceBefore=10, spaceAfter=8,
        ))
        styles.add(ParagraphStyle(
            name='SIPCAH2', parent=styles['Heading2'], fontName='Helvetica-Bold',
            fontSize=11, leading=14, textColor=self.GREEN,
            spaceBefore=7, spaceAfter=5,
        ))
        styles.add(ParagraphStyle(
            name='SIPCABody', parent=styles['BodyText'], fontName='Helvetica',
            fontSize=9, leading=13, textColor=self.DARK, spaceAfter=6,
        ))
        styles.add(ParagraphStyle(
            name='SIPCASmall', parent=styles['BodyText'], fontName='Helvetica',
            fontSize=7.5, leading=10, textColor=self.DARK,
        ))
        styles.add(ParagraphStyle(
            name='SIPCAFooter', parent=styles['BodyText'], fontName='Helvetica',
            fontSize=7, leading=9, textColor=self.MUTED,
            alignment=TA_CENTER,
        ))
        return styles

    def _page(self, canvas, doc) -> None:
        canvas.saveState()
        width, height = doc.pagesize
        canvas.setStrokeColor(self.GREEN)
        canvas.setLineWidth(0.8)
        canvas.line(1.5 * cm, 1.35 * cm, width - 1.5 * cm, 1.35 * cm)
        canvas.setFillColor(self.MUTED)
        canvas.setFont('Helvetica', 7)
        canvas.drawString(1.5 * cm, 0.85 * cm, 'SIPCA IDEAD - Universidad del Tolima')
        canvas.drawRightString(width - 1.5 * cm, 0.85 * cm, f'Página {doc.page}')
        canvas.restoreState()

    def _cover(self, title: str, subtitle: str, scope: str) -> list:
        now = datetime.now()
        return [
            Spacer(1, 1.6 * cm),
            Paragraph('UNIVERSIDAD DEL TOLIMA', self.styles['SIPCAH2']),
            Paragraph('INSTITUTO DE EDUCACIÓN A DISTANCIA - IDEAD', self.styles['SIPCAH2']),
            Spacer(1, 1.2 * cm),
            Paragraph(title, self.styles['SIPCATitle']),
            Paragraph(subtitle, self.styles['SIPCASubtitle']),
            Spacer(1, 0.8 * cm),
            self._metadata_table([
                ('Sistema', 'SIPCA - Sistema Inteligente para la Planeación de Cobertura Académica'),
                ('Alcance', scope),
                ('Modelo de datos', 'SIPCA - Modelo de Datos v1.0'),
                ('Fecha de generación', now.strftime('%Y-%m-%d %H:%M')),
                ('Carácter', 'Documento de apoyo a la planeación. Las recomendaciones requieren validación institucional.'),
            ]),
            PageBreak(),
        ]

    def _metadata_table(self, rows: list[tuple[str, str]]) -> Table:
        data = [[Paragraph(f'<b>{escape(k)}</b>', self.styles['SIPCASmall']),
                 Paragraph(escape(v), self.styles['SIPCASmall'])] for k, v in rows]
        table = Table(data, colWidths=[4.2 * cm, 12.0 * cm], hAlign='CENTER')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.LIGHT_GREEN),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D9E4DD')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        return table

    def _paragraph(self, text: str) -> Paragraph:
        return Paragraph(escape(self._text(text)).replace('\n', '<br/>'), self.styles['SIPCABody'])

    def _table(
        self,
        dataframe: pd.DataFrame,
        columns: list[str],
        labels: dict[str, str] | None = None,
        widths: list[float] | None = None,
        font_size: float = 6.8,
    ) -> Table | Paragraph:
        if dataframe.empty:
            return Paragraph('No existen registros disponibles.', self.styles['SIPCABody'])
        labels = labels or {}
        available = [column for column in columns if column in dataframe.columns]
        data = [[Paragraph(f'<b>{escape(labels.get(c, c))}</b>', self.styles['SIPCASmall']) for c in available]]
        for _, row in dataframe[available].iterrows():
            data.append([
                Paragraph(escape(self._text(row[column])), ParagraphStyle(
                    name=f'table_{font_size}', parent=self.styles['SIPCASmall'],
                    fontSize=font_size, leading=font_size + 2,
                ))
                for column in available
            ])
        if widths is not None:
            total_width = sum(widths)
            col_widths = [w / total_width * 25.8 * cm for w in widths]
        else:
            col_widths = [25.8 * cm / len(available)] * len(available)
        table = Table(data, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#D1D5DB')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_GRAY]),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return table

    def _source_table(self) -> pd.DataFrame:
        sources = self.db.table('fuentes').copy()
        rename = {'fuente_id': 'ID', 'nombre': 'Fuente', 'tipo': 'Tipo', 'url': 'URL'}
        sources = sources.rename(columns=rename)
        return sources[[c for c in ['ID', 'Fuente', 'Tipo', 'URL'] if c in sources.columns]]

    def _metric_rows(self, indicators: pd.DataFrame) -> list[tuple[str, str]]:
        if indicators.empty:
            return []
        data = indicators.copy()
        data['Año'] = pd.to_numeric(data['Año'], errors='coerce')
        data['Valor'] = pd.to_numeric(data['Valor'], errors='coerce')
        data = data.dropna(subset=['Valor']).sort_values('Año')
        rows = []
        for code, label in [('TTI', 'Tasa de tránsito inmediato'), ('COBERTURA', 'Cobertura en educación superior'), ('BACH_G11', 'Bachilleres de grado 11')]:
            current = data[data['Indicador_codigo'] == code]
            if current.empty:
                continue
            record = current.iloc[-1]
            value = float(record['Valor'])
            year = '' if pd.isna(record['Año']) else f" ({int(record['Año'])})"
            display = f'{value:,.2f} %' if self._text(record['Unidad']) == '%' else f'{value:,.0f}'
            rows.append((label + year, display))
        return rows

    def pdf_municipio(self, municipality: str) -> bytes:
        result = self.queries.consulta_municipio(municipality)
        portfolio = self.queries.portafolio_municipal(municipality)
        municipality_row = result['municipio']
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=landscape(A4), rightMargin=1.3 * cm,
            leftMargin=1.3 * cm, topMargin=1.3 * cm, bottomMargin=1.7 * cm,
            title=f'Informe territorial - {municipality}', author='SIPCA IDEAD',
        )
        story = self._cover(
            f'Informe territorial: {municipality}',
            f"{municipality_row.get('Departamento', '')} - {municipality_row.get('Región', '')}",
            'Perfil, oferta vigente, portafolio territorial, recomendaciones e indicadores.',
        )
        story.append(Paragraph('1. Síntesis territorial', self.styles['SIPCAH1']))
        if not result['perfil'].empty:
            profile = result['perfil'].iloc[0]
            story.append(Paragraph('Perfil territorial', self.styles['SIPCAH2']))
            story.append(self._paragraph(profile.get('Perfil territorial integrado', '')))
            story.append(Paragraph('Necesidades formativas prioritarias', self.styles['SIPCAH2']))
            story.append(self._paragraph(profile.get('Necesidades formativas prioritarias', '')))
        else:
            story.append(self._paragraph('No existe perfil territorial registrado.'))

        metrics = self._metric_rows(result['indicadores'])
        if metrics:
            story.append(Paragraph('Indicadores clave', self.styles['SIPCAH2']))
            story.append(self._metadata_table(metrics))

        story.append(Paragraph('2. Oferta vigente', self.styles['SIPCAH1']))
        offer = result['oferta'].merge(
            result['cat'][['CAT_id', 'Nombre_cat']].drop_duplicates(),
            how='left', on='CAT_id',
        )
        story.append(self._table(
            offer,
            ['Nombre_oficial', 'Nombre_cat', 'Modalidad', 'Estado_oferta'],
            labels={'Nombre_oficial': 'Programa', 'Nombre_cat': 'CAT'},
            widths=[5, 3, 2, 2], font_size=7.2,
        ))

        story.append(Paragraph('3. Portafolio territorial', self.styles['SIPCAH1']))
        story.append(self._table(
            portfolio,
            ['Programa base', 'Estado territorial', 'Nivel de pertinencia', 'Nivel de prioridad', 'Énfasis territorial', 'Justificación'],
            widths=[4, 2.2, 2, 1.7, 3, 7], font_size=6.2,
        ))

        story.append(Paragraph('4. Programas recomendados', self.styles['SIPCAH1']))
        story.append(self._table(
            result['recomendaciones'],
            ['Programa base', 'Énfasis territorial', 'Nivel de prioridad', 'Horizonte sugerido', 'Modalidad recomendada', 'Viabilidad institucional preliminar', 'Justificación técnica Municipio–programa'],
            widths=[3.2, 2.8, 1.5, 1.5, 2, 2, 7], font_size=6.1,
        ))

        story.append(Paragraph('5. Indicadores disponibles', self.styles['SIPCAH1']))
        indicators = result['indicadores'].copy()
        story.append(self._table(
            indicators,
            ['Indicador_nombre', 'Año', 'Valor', 'Unidad', 'Fuente_id', 'Observaciones'],
            labels={'Indicador_nombre': 'Indicador', 'Fuente_id': 'Fuente'},
            widths=[4, 1.1, 1.3, 1.2, 1.4, 6], font_size=6.5,
        ))

        story.append(Paragraph('6. Fuentes registradas', self.styles['SIPCAH1']))
        story.append(self._table(
            self._source_table(), ['ID', 'Fuente', 'Tipo', 'URL'],
            widths=[1.4, 3, 2.5, 8], font_size=6.4,
        ))
        doc.build(story, onFirstPage=self._page, onLaterPages=self._page)
        return buffer.getvalue()

    def pdf_programa(self, program: str) -> bytes:
        result = self.queries.consulta_programa(program)
        opportunities = self.queries.ranking_oportunidades_programa(program)
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=landscape(A4), rightMargin=1.3 * cm,
            leftMargin=1.3 * cm, topMargin=1.3 * cm, bottomMargin=1.7 * cm,
            title=f'Informe por programa - {program}', author='SIPCA IDEAD',
        )
        story = self._cover(
            f'Informe de cobertura y expansión',
            program,
            'Oferta vigente, oportunidades de ampliación, recomendaciones y evidencia territorial.',
        )
        story.append(Paragraph('1. Oferta vigente', self.styles['SIPCAH1']))
        story.append(self._table(
            result['oferta'],
            ['Nombre_cat', 'Municipio de oferta', 'Modalidad', 'Estado_oferta'],
            labels={'Nombre_cat': 'CAT', 'Municipio de oferta': 'Municipio'},
            widths=[3, 3, 2, 2], font_size=7,
        ))

        story.append(Paragraph('2. Oportunidades de ampliación', self.styles['SIPCAH1']))
        story.append(self._table(
            opportunities,
            ['Nombre_cat', 'Municipio', 'Departamento', 'Estado territorial', 'Nivel de pertinencia', 'Nivel de prioridad', 'Énfasis territorial', 'Bachilleres grado 11 (2023)', 'Justificación'],
            widths=[2.4, 2.2, 2, 2.3, 1.8, 1.5, 3, 1.6, 6], font_size=5.9,
        ))

        story.append(Paragraph('3. Recomendaciones relacionadas', self.styles['SIPCAH1']))
        story.append(self._table(
            result['recomendaciones'],
            ['Municipio', 'Departamento', 'Programa base', 'Énfasis territorial', 'Nivel de prioridad', 'Horizonte sugerido', 'Modalidad recomendada', 'Viabilidad institucional preliminar', 'Justificación técnica Municipio–programa'],
            widths=[2, 2, 3, 2.8, 1.4, 1.5, 1.8, 1.8, 6], font_size=5.8,
        ))

        story.append(Paragraph('4. Fuentes registradas', self.styles['SIPCAH1']))
        story.append(self._table(
            self._source_table(), ['ID', 'Fuente', 'Tipo', 'URL'],
            widths=[1.4, 3, 2.5, 8], font_size=6.4,
        ))
        doc.build(story, onFirstPage=self._page, onLaterPages=self._page)
        return buffer.getvalue()

    @staticmethod
    def _write_workbook(sheets: dict[str, pd.DataFrame], title: str) -> bytes:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            title_format = workbook.add_format({
                'bold': True, 'font_size': 16, 'font_color': '#174F32',
                'align': 'left', 'valign': 'vcenter',
            })
            header_format = workbook.add_format({
                'bold': True, 'font_color': 'white', 'bg_color': '#1F6F43',
                'border': 1, 'align': 'center', 'valign': 'vcenter',
                'text_wrap': True,
            })
            body_format = workbook.add_format({
                'border': 1, 'valign': 'top', 'text_wrap': True,
            })
            metadata = pd.DataFrame({
                'Elemento': ['Sistema', 'Informe', 'Modelo de datos', 'Fecha de generación'],
                'Valor': ['SIPCA IDEAD', title, 'SIPCA - Modelo de Datos v1.0', datetime.now().strftime('%Y-%m-%d %H:%M')],
            })
            metadata.to_excel(writer, sheet_name='00_RESUMEN', index=False, startrow=2)
            ws = writer.sheets['00_RESUMEN']
            ws.write(0, 0, title, title_format)
            ws.set_column(0, 0, 24)
            ws.set_column(1, 1, 70)
            ws.freeze_panes(3, 0)
            for col, value in enumerate(metadata.columns):
                ws.write(2, col, value, header_format)
            for row in range(3, 3 + len(metadata)):
                ws.set_row(row, 35)
                for col in range(2):
                    ws.write(row, col, metadata.iloc[row - 3, col], body_format)

            for sheet_name, dataframe in sheets.items():
                safe_name = sheet_name[:31]
                data = dataframe.copy()
                data.to_excel(writer, sheet_name=safe_name, index=False)
                ws = writer.sheets[safe_name]
                ws.freeze_panes(1, 0)
                ws.autofilter(0, 0, max(len(data), 1), max(len(data.columns) - 1, 0))
                for col, column in enumerate(data.columns):
                    ws.write(0, col, column, header_format)

                    # Calcula un ancho robusto incluso cuando la columna está
                    # completamente vacía o utiliza tipos anulables de pandas.
                    if data.empty:
                        percentile_length = 0
                    else:
                        lengths = data[column].map(
                            lambda value: 0
                            if value is None or pd.isna(value)
                            else len(str(value))
                        )
                        q90 = lengths.quantile(0.90) if not lengths.empty else 0
                        percentile_length = 0 if pd.isna(q90) else int(q90)

                    max_len = max(len(str(column)), min(45, percentile_length))
                    ws.set_column(
                        col,
                        col,
                        max(11, min(max_len + 2, 45)),
                        body_format,
                    )
                for row in range(1, len(data) + 1):
                    ws.set_row(row, 32)
        return output.getvalue()

    def excel_municipio(self, municipality: str) -> bytes:
        result = self.queries.consulta_municipio(municipality)
        portfolio = self.queries.portafolio_municipal(municipality)
        offer = result['oferta'].merge(
            result['cat'][['CAT_id', 'Nombre_cat']].drop_duplicates(),
            how='left', on='CAT_id',
        )
        municipality_df = pd.DataFrame([result['municipio']])
        return self._write_workbook({
            '01_MUNICIPIO': municipality_df,
            '02_PERFIL': result['perfil'],
            '03_OFERTA': offer,
            '04_PORTAFOLIO': portfolio,
            '05_RECOMENDACIONES': result['recomendaciones'],
            '06_INDICADORES': result['indicadores'],
            '07_FUENTES': self._source_table(),
        }, f'Informe territorial - {municipality}')

    def excel_programa(self, program: str) -> bytes:
        result = self.queries.consulta_programa(program)
        opportunities = self.queries.ranking_oportunidades_programa(program)
        program_df = pd.DataFrame([result['programa']])
        return self._write_workbook({
            '01_PROGRAMA': program_df,
            '02_OFERTA': result['oferta'],
            '03_OPORTUNIDADES': opportunities,
            '04_RECOMENDACIONES': result['recomendaciones'],
            '05_FUENTES': self._source_table(),
        }, f'Informe por programa - {program}')
