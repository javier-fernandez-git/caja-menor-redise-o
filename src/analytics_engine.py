"""
analytics_engine.py — CAPA ANALITICA / MOTOR CAUSAL (Etapa 2)

Responde automaticamente preguntas gerenciales sobre la capa de eventos:

    motor_causal()        -> "¿por que subio el costo del contrato?"
    motor_correlaciones() -> correlaciones multivariable entre series diarias

Todo se calcula sobre eventos_corporativos (event sourcing), agrupando por
fecha (Regla #4). Sin dependencias externas: solo biblioteca estandar.
"""

from collections import defaultdict
from math import sqrt

import config
import event_engine


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------

def _gastos_por_item(eventos):
    """Suma de valor por item canonico (solo GASTO/AJUSTE)."""
    acum = defaultdict(float)
    for e in eventos:
        sub = (e["subtipo_evento"] or "").upper()
        if sub in ("GASTO", "AJUSTE"):
            clave = e["descripcion_normalizada"] or "SIN_ITEM"
            acum[clave] += e["valor"] or 0
    return acum


def _clasificar_totales(gastos_por_item):
    """Reparte el gasto total entre directos / indirectos / no clasificado."""
    totales = {"DIRECTO": 0.0, "INDIRECTO": 0.0, "NO_CLASIFICADO": 0.0}
    for item, valor in gastos_por_item.items():
        totales[config.clasificar_costo(item)] += valor
    return totales


# ----------------------------------------------------------------------
# MOTOR CAUSAL
# ----------------------------------------------------------------------

def motor_causal(contrato_id=None, centro_costo_id=None,
                 periodo_actual=None, periodo_anterior=None, top=5):
    """
    Explica la variacion de costo entre dos periodos.

    periodo_actual / periodo_anterior: dict {"ini": fecha, "fin": fecha}.
    Si no se entregan, se compara automaticamente la segunda mitad contra la
    primera mitad del rango de fechas disponible.

    Retorna:
        {
          "costo_anterior", "costo_actual", "variacion", "variacion_pct",
          "por_clasificacion": { directos/indirectos: {anterior, actual, var} },
          "causas": [ {item, anterior, actual, variacion, clasificacion}, ... ],
          "resumen": str
        }
    """
    periodo_actual, periodo_anterior = _resolver_periodos(
        contrato_id, centro_costo_id, periodo_actual, periodo_anterior
    )
    if not periodo_actual or not periodo_anterior:
        return {"resumen": "Datos insuficientes para el analisis causal.",
                "causas": []}

    ev_ant = event_engine.consultar_eventos(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        tipo_evento=event_engine.TIPO_FINANCIERO,
        fecha_ini=periodo_anterior["ini"], fecha_fin=periodo_anterior["fin"])
    ev_act = event_engine.consultar_eventos(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        tipo_evento=event_engine.TIPO_FINANCIERO,
        fecha_ini=periodo_actual["ini"], fecha_fin=periodo_actual["fin"])

    gi_ant = _gastos_por_item(ev_ant)
    gi_act = _gastos_por_item(ev_act)

    costo_ant = sum(gi_ant.values())
    costo_act = sum(gi_act.values())
    variacion = costo_act - costo_ant
    variacion_pct = (variacion / costo_ant) if costo_ant else None

    # variacion por item
    items = set(gi_ant) | set(gi_act)
    causas = []
    for item in items:
        a, b = gi_ant.get(item, 0), gi_act.get(item, 0)
        causas.append({
            "item": item,
            "anterior": a,
            "actual": b,
            "variacion": b - a,
            "clasificacion": config.clasificar_costo(item),
        })
    # ordenar por mayor aumento
    causas.sort(key=lambda c: c["variacion"], reverse=True)
    causas_top = [c for c in causas if c["variacion"] > 0][:top]

    tot_ant = _clasificar_totales(gi_ant)
    tot_act = _clasificar_totales(gi_act)
    por_clasificacion = {
        clase: {
            "anterior": tot_ant[clase],
            "actual": tot_act[clase],
            "variacion": tot_act[clase] - tot_ant[clase],
        }
        for clase in ("DIRECTO", "INDIRECTO", "NO_CLASIFICADO")
    }

    return {
        "periodo_anterior": periodo_anterior,
        "periodo_actual": periodo_actual,
        "costo_anterior": costo_ant,
        "costo_actual": costo_act,
        "variacion": variacion,
        "variacion_pct": variacion_pct,
        "por_clasificacion": por_clasificacion,
        "causas": causas_top,
        "resumen": _narrar_causa(variacion, variacion_pct, por_clasificacion,
                                 causas_top),
    }


def _resolver_periodos(contrato_id, centro_costo_id,
                       periodo_actual, periodo_anterior):
    if periodo_actual and periodo_anterior:
        return periodo_actual, periodo_anterior

    eventos = event_engine.consultar_eventos(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        tipo_evento=event_engine.TIPO_FINANCIERO)
    fechas = sorted({e["fecha"] for e in eventos if e["fecha"]})
    if len(fechas) < 2:
        return None, None

    mitad = len(fechas) // 2
    anterior = {"ini": fechas[0], "fin": fechas[mitad - 1]}
    actual = {"ini": fechas[mitad], "fin": fechas[-1]}
    return actual, anterior


def _narrar_causa(variacion, variacion_pct, por_clasificacion, causas):
    if variacion == 0:
        return "El costo se mantuvo estable entre los dos periodos."
    direccion = "subio" if variacion > 0 else "bajo"
    if variacion_pct is None:
        lineas = [
            f"Aparecio un costo de {abs(variacion):,.0f} "
            f"(no habia gasto registrado en el periodo anterior)."
        ]
    else:
        lineas = [
            f"El costo {direccion} {abs(variacion):,.0f} "
            f"({abs(variacion_pct) * 100:.1f}%)."
        ]
    ind = por_clasificacion["INDIRECTO"]["variacion"]
    dir_ = por_clasificacion["DIRECTO"]["variacion"]
    if ind > 0:
        lineas.append(f"Costos indirectos aumentaron {ind:,.0f}.")
    if dir_ > 0:
        lineas.append(f"Costos directos aumentaron {dir_:,.0f}.")
    if causas:
        detalle = ", ".join(
            f"{c['item']} (+{c['variacion']:,.0f})" for c in causas
        )
        lineas.append(f"Causas principales: {detalle}.")
    return " ".join(lineas)


# ----------------------------------------------------------------------
# MOTOR DE CORRELACIONES (multivariable)
# ----------------------------------------------------------------------

def _pearson(xs, ys):
    """Coeficiente de correlacion de Pearson (sin numpy)."""
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return 0.0
    return cov / sqrt(vx * vy)


def construir_series_diarias(contrato_id=None, centro_costo_id=None,
                             fecha_ini=None, fecha_fin=None):
    """
    Series por dia para correlacionar:
        gasto_total, produccion, y gasto por cada item canonico relevante.
    """
    eventos = event_engine.consultar_eventos(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    dias = sorted({e["fecha"] for e in eventos if e["fecha"]})
    series = defaultdict(lambda: defaultdict(float))

    for e in eventos:
        fecha = e["fecha"]
        if not fecha:
            continue
        sub = (e["subtipo_evento"] or "").upper()
        if e["tipo_evento"] == event_engine.TIPO_FINANCIERO and sub in ("GASTO", "AJUSTE"):
            series["gasto_total"][fecha] += e["valor"] or 0
            item = e["descripcion_normalizada"] or "SIN_ITEM"
            series[f"gasto_{item}"][fecha] += e["valor"] or 0
        elif e["tipo_evento"] == event_engine.TIPO_TECNICO:
            series["produccion"][fecha] += e["cantidad"] or 0

    # vectores alineados por dia
    vectores = {
        nombre: [valores.get(d, 0.0) for d in dias]
        for nombre, valores in series.items()
    }
    return dias, vectores


def motor_correlaciones(contrato_id=None, centro_costo_id=None,
                        fecha_ini=None, fecha_fin=None, umbral=0.5):
    """
    Correlaciona todas las series diarias contra 'gasto_total' (y produccion).
    Devuelve los pares con |correlacion| >= umbral, ordenados por fuerza.
    """
    dias, vectores = construir_series_diarias(
        contrato_id, centro_costo_id, fecha_ini, fecha_fin)

    if len(dias) < 2:
        return {"dias": len(dias), "correlaciones": [],
                "nota": "Se requieren al menos 2 dias con datos."}

    objetivos = [n for n in ("gasto_total", "produccion") if n in vectores]
    correlaciones = []
    for objetivo in objetivos:
        for nombre, vector in vectores.items():
            if nombre == objetivo:
                continue
            r = _pearson(vectores[objetivo], vector)
            if abs(r) >= umbral:
                correlaciones.append({
                    "objetivo": objetivo,
                    "variable": nombre,
                    "correlacion": round(r, 3),
                    "relacion": "directa" if r > 0 else "inversa",
                })
    correlaciones.sort(key=lambda c: abs(c["correlacion"]), reverse=True)
    return {"dias": len(dias), "correlaciones": correlaciones}
