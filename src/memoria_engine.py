"""
memoria_engine.py — MEMORIA ORGANIZACIONAL CONSULTABLE (Etapa 6)

Convierte la actividad humana fragmentada (eventos homologados) en
inteligencia organizacional consultable.

    consultar(texto)  -> entiende una pregunta en lenguaje natural acotado,
                         resuelve contrato y periodo, y narra la respuesta.
    narrar(...)       -> reconstruccion narrativa de la cronologia corporativa.
    exportar(...)     -> memoria en Markdown o JSON.

No usa modelos externos: parser de intencion + entidades por reglas sobre el
catalogo maestro (MDM) y el repositorio de eventos.
"""

import re
import json
from collections import defaultdict

import db
import mdm
import event_engine
import contabilidad
import analytics_engine
import predictive_engine


# Palabras genericas que NO ayudan a identificar un contrato.
_STOP_CONTRATO = {"OT", "DE", "DEL", "LA", "EL", "LOS", "LAS", "Y", "CONTRATO",
                  "OBRA", "PROYECTO", "FRENTE", "EN"}

_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


# ----------------------------------------------------------------------
# PARSER DE PREGUNTA
# ----------------------------------------------------------------------

def _detectar_intencion(texto):
    t = texto.lower()
    if any(k in t for k in ("por que", "porque", "por qué", "causa", "subio",
                            "subió", "aumento", "aumentó")):
        return "causal"
    if any(k in t for k in ("produccion", "producción", "ejecuto", "ejecutó",
                            "avance", "unidades")):
        return "produccion"
    if any(k in t for k in ("cuanto", "cuánto", "gasto", "gastó", "gasté",
                            "saldo", "costo", "invirtio", "invirtió", "plata")):
        return "financiero"
    return "timeline"


def _detectar_periodo(texto):
    """Extrae (fecha_ini, fecha_fin) de la pregunta, o (None, None)."""
    fechas = re.findall(r"\d{4}-\d{2}-\d{2}", texto)
    if len(fechas) >= 2:
        return min(fechas[:2]), max(fechas[:2])
    if len(fechas) == 1:
        return fechas[0], fechas[0]

    # "YYYY-MM" -> mes completo
    ym = re.findall(r"(\d{4})-(\d{2})\b", texto)
    if ym:
        anio, mes = ym[0]
        return _rango_mes(int(anio), int(mes))

    # "<mes> de <anio>" o "<mes> <anio>"
    t = texto.lower()
    for nombre, mes in _MESES.items():
        if nombre in t:
            m_anio = re.search(r"(20\d{2})", texto)
            if m_anio:
                return _rango_mes(int(m_anio.group(1)), mes)
    return None, None


def _rango_mes(anio, mes):
    ini = f"{anio:04d}-{mes:02d}-01"
    if mes == 12:
        fin = f"{anio:04d}-12-31"
    else:
        # ultimo dia = dia anterior al 1ro del mes siguiente
        import datetime
        siguiente = datetime.date(anio, mes, 28) + datetime.timedelta(days=4)
        ultimo = siguiente - datetime.timedelta(days=siguiente.day)
        fin = ultimo.isoformat()
    return ini, fin


def _detectar_contrato(texto):
    """
    Identifica el contrato mencionado comparando los tokens de la pregunta
    contra los maestros de contrato (overlap de tokens significativos).
    """
    tokens_q = {w for w in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ0-9]+", texto.upper())
                if w not in _STOP_CONTRATO and len(w) > 2}
    if not tokens_q:
        return None

    mejor, mejor_score = None, 0
    for m in mdm.listar_maestros(dominio="contrato"):
        tokens_m = {w for w in re.findall(r"[A-Z0-9]+", m["nombre_canonico"].upper())
                    if w not in _STOP_CONTRATO and len(w) > 2}
        overlap = len(tokens_q & tokens_m)
        if overlap > mejor_score:
            mejor, mejor_score = m, overlap
    return mejor if mejor_score > 0 else None


# ----------------------------------------------------------------------
# RESUMEN DE PERIODO (base de la narrativa)
# ----------------------------------------------------------------------

def _resumen(contrato_id=None, centro_costo_id=None, fecha_ini=None, fecha_fin=None):
    eventos = event_engine.consultar_eventos(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    fechas = sorted({e["fecha"] for e in eventos if e["fecha"]})
    estado = contabilidad.estado_completo(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    gasto_por_item = estado["obra"]["costo_por_item"]
    top = sorted(gasto_por_item.items(), key=lambda kv: kv[1], reverse=True)[:5]

    produccion = defaultdict(float)
    for e in eventos:
        if e["tipo_evento"] == event_engine.TIPO_TECNICO:
            produccion[e["descripcion_normalizada"] or "PRODUCCION"] += e["cantidad"] or 0

    return {
        "n_eventos": len(eventos),
        "desde": fechas[0] if fechas else None,
        "hasta": fechas[-1] if fechas else None,
        "saldo_caja": estado["caja"]["saldo"],
        "costo_obra": estado["obra"]["costo_obra"],
        "top_gastos": [{"item": k, "valor": v} for k, v in top],
        "produccion": dict(produccion),
        "produccion_total": sum(produccion.values()),
    }


def _nombre_contrato(contrato_id):
    if not contrato_id:
        return "todos los contratos"
    for o in db.obtener_obras():
        if o["id"] == contrato_id:
            return o["nombre"]
    return f"contrato #{contrato_id}"


def _frase_periodo(fecha_ini, fecha_fin):
    if fecha_ini and fecha_fin and fecha_ini != fecha_fin:
        return f"entre {fecha_ini} y {fecha_fin}"
    if fecha_ini:
        return f"el {fecha_ini}"
    return "en todo el historico"


def _pesos(n):
    return f"$ {n:,.0f}"


# ----------------------------------------------------------------------
# NARRATIVA
# ----------------------------------------------------------------------

def narrar(contrato_id=None, centro_costo_id=None, fecha_ini=None, fecha_fin=None):
    """Reconstruccion narrativa de la cronologia corporativa."""
    r = _resumen(contrato_id, centro_costo_id, fecha_ini, fecha_fin)
    nombre = _nombre_contrato(contrato_id)
    periodo = _frase_periodo(fecha_ini or r["desde"], fecha_fin or r["hasta"])

    if r["n_eventos"] == 0:
        return f"No hay eventos registrados para {nombre} {periodo}."

    partes = [
        f"En {nombre}, {periodo}, se registraron {r['n_eventos']} eventos "
        f"homologados.",
        f"La inversion en obra fue de {_pesos(r['costo_obra'])} y el saldo de "
        f"caja quedo en {_pesos(r['saldo_caja'])}.",
    ]
    if r["top_gastos"]:
        detalle = ", ".join(f"{g['item']} ({_pesos(g['valor'])})"
                            for g in r["top_gastos"])
        partes.append(f"Los principales conceptos de gasto fueron: {detalle}.")
    if r["produccion_total"] > 0:
        partes.append(f"La produccion ejecutada sumo {r['produccion_total']:g} "
                      f"unidades.")
    return " ".join(partes)


# ----------------------------------------------------------------------
# CONSULTA EN LENGUAJE NATURAL
# ----------------------------------------------------------------------

def consultar(texto):
    """Entiende una pregunta acotada y devuelve una respuesta narrada."""
    texto = (texto or "").strip()
    if not texto:
        return {"pregunta": texto, "respuesta": "Formula una pregunta.",
                "intencion": None}

    intencion = _detectar_intencion(texto)
    fecha_ini, fecha_fin = _detectar_periodo(texto)
    contrato = _detectar_contrato(texto)
    contrato_id = contrato["catalogo_id"] if contrato else None

    base = {
        "pregunta": texto,
        "intencion": intencion,
        "contrato": {"id": contrato_id, "nombre": contrato["nombre_canonico"]}
                    if contrato else None,
        "periodo": {"ini": fecha_ini, "fin": fecha_fin}
                   if (fecha_ini or fecha_fin) else None,
    }

    if intencion == "causal":
        causal = analytics_engine.motor_causal(contrato_id=contrato_id)
        base["respuesta"] = causal.get("resumen", "Sin datos para el analisis.")
        base["datos"] = causal
        return base

    resumen = _resumen(contrato_id, None, fecha_ini, fecha_fin)
    nombre = _nombre_contrato(contrato_id)
    periodo = _frase_periodo(fecha_ini, fecha_fin)

    if intencion == "financiero":
        base["respuesta"] = (
            f"En {nombre}, {periodo}, la inversion en obra fue "
            f"{_pesos(resumen['costo_obra'])} y el saldo de caja "
            f"{_pesos(resumen['saldo_caja'])} ({resumen['n_eventos']} eventos).")
    elif intencion == "produccion":
        if resumen["produccion_total"] > 0:
            det = ", ".join(f"{k}: {v:g}" for k, v in resumen["produccion"].items())
            base["respuesta"] = (f"En {nombre}, {periodo}, la produccion sumo "
                                 f"{resumen['produccion_total']:g} unidades ({det}).")
        else:
            base["respuesta"] = (f"No hay produccion registrada para {nombre} "
                                 f"{periodo}.")
    else:  # timeline
        base["respuesta"] = narrar(contrato_id, None, fecha_ini, fecha_fin)

    base["datos"] = resumen
    return base


# ----------------------------------------------------------------------
# EXPORTACION DE MEMORIA
# ----------------------------------------------------------------------

def exportar(contrato_id=None, centro_costo_id=None, fecha_ini=None,
             fecha_fin=None, formato="md"):
    """Exporta la memoria del contrato (narrativa + resumen + cronologia)."""
    import timeline_engine

    r = _resumen(contrato_id, centro_costo_id, fecha_ini, fecha_fin)
    narrativa = narrar(contrato_id, centro_costo_id, fecha_ini, fecha_fin)
    timeline = timeline_engine.reconstruir_timeline(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    if formato == "json":
        return json.dumps({
            "contrato": _nombre_contrato(contrato_id),
            "periodo": {"ini": fecha_ini, "fin": fecha_fin},
            "narrativa": narrativa, "resumen": r, "timeline": timeline,
        }, ensure_ascii=False, indent=2)

    # Markdown
    lineas = [
        f"# Memoria organizacional — {_nombre_contrato(contrato_id)}",
        f"\n_Periodo: {_frase_periodo(fecha_ini or r['desde'], fecha_fin or r['hasta'])}_\n",
        "## Narrativa\n", narrativa, "\n## Indicadores\n",
        f"- Eventos: {r['n_eventos']}",
        f"- Costo de obra: {_pesos(r['costo_obra'])}",
        f"- Saldo de caja: {_pesos(r['saldo_caja'])}",
        f"- Produccion total: {r['produccion_total']:g}",
        "\n## Cronologia\n",
    ]
    for dia in timeline:
        lineas.append(f"### {dia['fecha']}  (gasto {_pesos(dia['gasto_dia'])}, "
                      f"produccion {dia['produccion_dia']:g})")
        for ev in dia["eventos"]:
            quien = ev["responsable"] or ev["fuente"]
            if ev["tipo_evento"] == event_engine.TIPO_TECNICO:
                lineas.append(f"- {quien}: ejecuto {ev['descripcion']} x{ev['cantidad']:g}")
            else:
                lineas.append(f"- {quien}: {ev['subtipo_evento']} {ev['descripcion']} "
                              f"{_pesos(ev['valor'])}")
        lineas.append("")
    return "\n".join(lineas)


if __name__ == "__main__":
    db.inicializar()
    for q in [
        "que ocurrio en el contrato libano",
        "cuanto se gasto en coralina del sol",
        "por que subio el costo",
        "produccion de libano 2000",
    ]:
        res = consultar(q)
        print(f"\nQ: {q}\n  intencion={res['intencion']} contrato="
              f"{res['contrato']}\n  -> {res['respuesta']}")
