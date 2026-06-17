"""
pdf_engine.py — MOTOR DE DOCUMENTOS PDF (Etapa 4)

Genera documentos corporativos sin dependencias nativas:
    - fpdf2 (PDF, puro Python)
    - segno (QR, puro Python)

Documentos:
    generar_liquidacion_pdf()   -> recibo con logo, firmas, QR y consecutivo PDF
    generar_reporte_financiero_pdf()
    generar_trazabilidad_pdf()  -> timeline corporativo por contrato

Cada funcion retorna `bytes` (el PDF), listo para enviar por HTTP o guardar.
"""

import io
from datetime import datetime
from pathlib import Path

import segno
from fpdf import FPDF

import db
import contabilidad
import timeline_engine

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
REPORTS_DIR = BASE_DIR / "reports"
LOGO_PNG = ASSETS_DIR / "logo.png"

EMPRESA = "SISTEMA DE RECONSTRUCCION OPERACIONAL-FINANCIERA"


def _pesos(n):
    try:
        return f"$ {n:,.0f}"
    except (TypeError, ValueError):
        return "$ 0"


def _qr_png_bytes(texto):
    """Genera un PNG de QR en memoria (segno, sin PIL)."""
    qr = segno.make(texto, error="m")
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=3, border=1)
    buffer.seek(0)
    return buffer


class _DocumentoPDF(FPDF):
    """PDF base con encabezado (logo opcional) y pie con paginacion."""

    def __init__(self, titulo, consecutivo_pdf):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.titulo = titulo
        self.consecutivo_pdf = consecutivo_pdf
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        if LOGO_PNG.exists():
            try:
                self.image(str(LOGO_PNG), x=10, y=8, w=22)
            except Exception:
                pass
        self.set_font("Helvetica", "B", 13)
        self.set_xy(10, 10)
        self.cell(0, 7, EMPRESA, ln=1, align="C")
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 6, self.titulo, ln=1, align="C")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, f"Documento No. PDF-{self.consecutivo_pdf:06d}   "
                        f"Generado: {datetime.now():%Y-%m-%d %H:%M}", ln=1,
                  align="C")
        self.ln(2)
        self.set_draw_color(150, 150, 150)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, f"PDF-{self.consecutivo_pdf:06d}  -  Pagina "
                        f"{self.page_no()}/{{nb}}", align="C")
        self.set_text_color(0, 0, 0)

    # -- helpers de contenido --
    def campo(self, etiqueta, valor):
        self.set_font("Helvetica", "B", 9)
        self.cell(40, 6, f"{etiqueta}:", ln=0)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, str(valor), ln=1)

    def seccion(self, texto):
        self.ln(2)
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(235, 235, 235)
        self.cell(0, 7, texto, ln=1, fill=True)
        self.ln(1)

    def fila_montos(self, etiqueta, valor, negrita=False):
        self.set_font("Helvetica", "B" if negrita else "", 9)
        self.cell(130, 6, str(etiqueta), ln=0)
        self.cell(0, 6, _pesos(valor), ln=1, align="R")


# ----------------------------------------------------------------------
# LIQUIDACION
# ----------------------------------------------------------------------

def generar_liquidacion_pdf(responsable_id, obra_id=None, cc_id=None,
                            fecha_ini=None, fecha_fin=None):
    """Recibo de liquidacion con logo, firmas, QR y consecutivo PDF."""
    consecutivo = db.siguiente_consecutivo_pdf()

    datos = db.liquidacion(responsable_id, obra_id, cc_id, fecha_ini, fecha_fin)
    resp = _nombre(db.obtener_responsables(), responsable_id)
    obra = _nombre(db.obtener_obras(), obra_id) if obra_id else "TODAS"
    centro = _nombre_cc(cc_id) if cc_id else "TODOS"

    total_reembolso = sum(datos["parcial"].values())

    pdf = _DocumentoPDF("RECIBO DE LIQUIDACION", consecutivo)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.campo("Responsable", resp)
    pdf.campo("Obra / Contrato", obra)
    pdf.campo("Centro de costos", centro)
    pdf.campo("Periodo", f"{fecha_ini or '-'}  a  {fecha_fin or '-'}")

    pdf.seccion("RESUMEN PARCIAL DE GASTOS POR ITEM (REEMBOLSO)")
    if datos["parcial"]:
        for item, monto in sorted(datos["parcial"].items()):
            pdf.fila_montos(item, monto)
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "(sin gastos para reembolso en el periodo)", ln=1)
    pdf.ln(1)
    pdf.fila_montos("(=) GASTOS PARA REEMBOLSO", total_reembolso, negrita=True)

    pdf.seccion("RESUMEN GENERAL")
    pdf.fila_montos("(+) Recibido en asignaciones", datos["total_asignaciones"])
    pdf.fila_montos("(+) Recibido en reembolsos", datos["total_reembolsos"])
    total_trabajador = datos["total_asignaciones"] + datos["total_reembolsos"]
    pdf.fila_montos("(=) Acumulado total trabajador", total_trabajador, negrita=True)
    pdf.fila_montos("(-) Ejecutado por el trabajador", datos["total_ejecutado"])
    pdf.fila_montos("(=) Neto", total_trabajador - datos["total_ejecutado"],
                    negrita=True)

    _firmas_y_qr(pdf, consecutivo, resp,
                 f"LIQ;PDF-{consecutivo:06d};{resp};{_pesos(total_reembolso)}"
                 f";{fecha_ini}..{fecha_fin}")

    return _salida(pdf)


# ----------------------------------------------------------------------
# REPORTE FINANCIERO
# ----------------------------------------------------------------------

def generar_reporte_financiero_pdf(contrato_id=None, centro_costo_id=None,
                                   responsable_id=None,
                                   fecha_ini=None, fecha_fin=None):
    consecutivo = db.siguiente_consecutivo_pdf()
    estado = contabilidad.estado_completo(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        responsable_id=responsable_id, fecha_ini=fecha_ini, fecha_fin=fecha_fin)
    caja = estado["caja"]
    obra = estado["obra"]

    pdf = _DocumentoPDF("REPORTE FINANCIERO", consecutivo)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.campo("Contrato", _nombre(db.obtener_obras(), contrato_id)
              if contrato_id else "TODOS")
    pdf.campo("Periodo", f"{fecha_ini or '-'}  a  {fecha_fin or '-'}")

    pdf.seccion("CONTABILIDAD DE CAJA (efectivo disponible)")
    pdf.fila_montos("(+) Asignaciones", caja["asignaciones"])
    pdf.fila_montos("(+) Reembolsos", caja["reembolsos"])
    pdf.fila_montos("(+) Ajustes positivos", caja["ajustes_positivos"])
    pdf.fila_montos("(-) Gastos", caja["gastos"])
    pdf.fila_montos("(-) Ajustes negativos", caja["ajustes_negativos"])
    pdf.fila_montos("(=) SALDO DE CAJA", caja["saldo"], negrita=True)

    pdf.seccion("CONTABILIDAD DE OBRA (inversion ejecutada)")
    pdf.fila_montos("Costo de obra (los reembolsos NO lo reducen)",
                    obra["costo_obra"], negrita=True)
    pdf.ln(1)
    for item, valor in sorted(obra["costo_por_item"].items(),
                              key=lambda kv: kv[1], reverse=True):
        pdf.fila_montos(f"   {item}", valor)

    _firmas_y_qr(pdf, consecutivo, responsable_id and
                 _nombre(db.obtener_responsables(), responsable_id) or "FINANZAS",
                 f"FIN;PDF-{consecutivo:06d};saldo={_pesos(caja['saldo'])}"
                 f";obra={_pesos(obra['costo_obra'])}")
    return _salida(pdf)


# ----------------------------------------------------------------------
# TRAZABILIDAD TEMPORAL (timeline)
# ----------------------------------------------------------------------

def generar_trazabilidad_pdf(contrato_id=None, centro_costo_id=None,
                             fecha_ini=None, fecha_fin=None, max_eventos=400):
    consecutivo = db.siguiente_consecutivo_pdf()
    timeline = timeline_engine.reconstruir_timeline(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    pdf = _DocumentoPDF("TRAZABILIDAD TEMPORAL", consecutivo)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.campo("Contrato", _nombre(db.obtener_obras(), contrato_id)
              if contrato_id else "TODOS")
    pdf.campo("Periodo", f"{fecha_ini or '-'}  a  {fecha_fin or '-'}")

    contador = 0
    for dia in timeline:
        if contador >= max_eventos:
            break
        pdf.seccion(f"{dia['fecha']}    gasto: {_pesos(dia['gasto_dia'])}    "
                    f"produccion: {dia['produccion_dia']:g}")
        pdf.set_font("Helvetica", "", 8)
        for ev in dia["eventos"]:
            if contador >= max_eventos:
                break
            quien = ev["responsable"] or ev["fuente"]
            if ev["tipo_evento"] == "TECNICO":
                linea = (f"  - {quien}: ejecuto {ev['descripcion']} "
                         f"x{ev['cantidad']:g}")
            else:
                linea = (f"  - {quien}: {ev['subtipo_evento']} "
                         f"{ev['descripcion']} {_pesos(ev['valor'])}")
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, linea)
            contador += 1

    return _salida(pdf)


# ----------------------------------------------------------------------
# Helpers compartidos
# ----------------------------------------------------------------------

def _firmas_y_qr(pdf, consecutivo, nombre_responsable, qr_texto):
    pdf.ln(14)
    y = pdf.get_y()
    pdf.line(20, y, 90, y)
    pdf.line(120, y, 190, y)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(20, y + 1)
    pdf.cell(70, 5, f"Responsable: {nombre_responsable}", align="C")
    pdf.set_xy(120, y + 1)
    pdf.cell(70, 5, "Supervisor", align="C")

    # QR de verificacion (abajo a la derecha)
    try:
        qr_buffer = _qr_png_bytes(qr_texto)
        pdf.image(qr_buffer, x=170, y=y + 8, w=24, h=24)
    except Exception:
        pass
    pdf.set_xy(10, y + 8)
    pdf.set_font("Helvetica", "I", 7)
    pdf.multi_cell(150, 4, "Documento generado automaticamente. El codigo QR "
                           "permite verificar el consecutivo y los totales.")


def _salida(pdf):
    return bytes(pdf.output())


def _nombre(lista, id_):
    for x in lista:
        if x["id"] == id_:
            return x["nombre"]
    return "-"


def _nombre_cc(cc_id):
    for x in db.obtener_centros_de_costos():
        if x["id"] == cc_id:
            return x["contrato"]
    return "-"


def guardar(nombre_archivo, contenido_bytes):
    """Guarda un PDF en reports/ y retorna la ruta."""
    REPORTS_DIR.mkdir(exist_ok=True)
    ruta = REPORTS_DIR / nombre_archivo
    ruta.write_bytes(contenido_bytes)
    return ruta
