"""
predictive_engine.py — CAPA PREDICTIVA (Etapa 2)

Inferencias, proyecciones y deteccion de anomalias sobre la capa de eventos:

    predecir_gasto()
    predecir_facturacion()
    predecir_produccion()
    detectar_sobreconsumo()

Sin dependencias externas: regresion lineal por minimos cuadrados y
deteccion de anomalias por desviacion estandar, todo con stdlib.
"""

from collections import defaultdict
from math import sqrt

import config
import event_engine


# ----------------------------------------------------------------------
# Regresion lineal simple (minimos cuadrados): y = a + b*x
# ----------------------------------------------------------------------

def _regresion_lineal(ys):
    """ys es una serie ordenada en el tiempo (x = 0,1,2,...)."""
    n = len(ys)
    if n == 0:
        return 0.0, 0.0
    if n == 1:
        return ys[0], 0.0
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return my, 0.0
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    a = my - b * mx
    return a, b


def _proyectar(ys, pasos):
    """Proyecta `pasos` valores futuros con la tendencia lineal."""
    a, b = _regresion_lineal(ys)
    n = len(ys)
    return [max(a + b * (n + i), 0.0) for i in range(pasos)]


# ----------------------------------------------------------------------
# Series por dia
# ----------------------------------------------------------------------

def _serie_gasto_diario(contrato_id=None, centro_costo_id=None,
                        fecha_ini=None, fecha_fin=None):
    eventos = event_engine.consultar_eventos(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        tipo_evento=event_engine.TIPO_FINANCIERO,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)
    por_dia = defaultdict(float)
    for e in eventos:
        sub = (e["subtipo_evento"] or "").upper()
        if sub in ("GASTO", "AJUSTE"):
            por_dia[e["fecha"]] += e["valor"] or 0
    dias = sorted(por_dia)
    return dias, [por_dia[d] for d in dias]


def _serie_produccion_diaria(contrato_id=None, centro_costo_id=None,
                             fecha_ini=None, fecha_fin=None):
    eventos = event_engine.consultar_eventos(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        tipo_evento=event_engine.TIPO_TECNICO,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)
    por_dia = defaultdict(float)
    for e in eventos:
        por_dia[e["fecha"]] += e["cantidad"] or 0
    dias = sorted(por_dia)
    return dias, [por_dia[d] for d in dias]


# ----------------------------------------------------------------------
# PREDICCIONES
# ----------------------------------------------------------------------

def predecir_gasto(contrato_id=None, centro_costo_id=None,
                   fecha_ini=None, fecha_fin=None, horizonte=7):
    """Proyecta el gasto de los proximos `horizonte` dias."""
    dias, serie = _serie_gasto_diario(
        contrato_id, centro_costo_id, fecha_ini, fecha_fin)
    if len(serie) < 2:
        return {"horizonte": horizonte, "proyeccion": [],
                "nota": "Historico insuficiente para proyectar."}
    proyeccion = _proyectar(serie, horizonte)
    a, b = _regresion_lineal(serie)
    return {
        "dias_historicos": len(dias),
        "promedio_diario": sum(serie) / len(serie),
        "tendencia_diaria": b,
        "horizonte": horizonte,
        "proyeccion": [round(v, 0) for v in proyeccion],
        "gasto_proyectado_total": round(sum(proyeccion), 0),
    }


def predecir_produccion(contrato_id=None, centro_costo_id=None,
                        fecha_ini=None, fecha_fin=None, horizonte=7):
    """Proyecta produccion (unidades ejecutadas) de los proximos dias."""
    dias, serie = _serie_produccion_diaria(
        contrato_id, centro_costo_id, fecha_ini, fecha_fin)
    if len(serie) < 2:
        return {"horizonte": horizonte, "proyeccion": [],
                "nota": "Sin produccion historica suficiente para proyectar."}
    proyeccion = _proyectar(serie, horizonte)
    return {
        "dias_historicos": len(dias),
        "promedio_diario": sum(serie) / len(serie),
        "horizonte": horizonte,
        "proyeccion": [round(v, 2) for v in proyeccion],
        "produccion_proyectada_total": round(sum(proyeccion), 2),
    }


def predecir_facturacion(valor_contrato, duracion_dias,
                         contrato_id=None, centro_costo_id=None,
                         fecha_ini=None, fecha_fin=None,
                         porc_directos=None):
    """
    Estima la facturacion esperada segun el modelo economico del contrato
    y la compara con el gasto real proyectado.

        facturacion_dia = valor_contrato / duracion_dias
    """
    if porc_directos is None:
        porc_directos = config.PORC_DIRECTOS_DEFAULT
    if duracion_dias <= 0:
        return {"nota": "duracion_dias debe ser > 0."}

    facturacion_dia = valor_contrato / duracion_dias
    dias, serie = _serie_gasto_diario(
        contrato_id, centro_costo_id, fecha_ini, fecha_fin)
    dias_transcurridos = len(dias)

    facturacion_esperada = facturacion_dia * dias_transcurridos
    gasto_real = sum(serie)
    utilidad_estimada = facturacion_esperada - gasto_real
    margen = (utilidad_estimada / facturacion_esperada) if facturacion_esperada else 0

    return {
        "facturacion_dia": round(facturacion_dia, 0),
        "dias_transcurridos": dias_transcurridos,
        "facturacion_esperada": round(facturacion_esperada, 0),
        "gasto_real": round(gasto_real, 0),
        "utilidad_estimada": round(utilidad_estimada, 0),
        "margen_estimado": round(margen, 4),
        "facturacion_total_contrato": valor_contrato,
    }


# ----------------------------------------------------------------------
# DETECCION DE SOBRECONSUMO / ANOMALIAS
# ----------------------------------------------------------------------

def detectar_sobreconsumo(contrato_id=None, centro_costo_id=None,
                          fecha_ini=None, fecha_fin=None, k=2.0):
    """
    Marca dias cuyo gasto supera (media + k*desviacion_estandar) por item
    canonico. k=2 ~ por encima del 95% de lo normal.
    """
    eventos = event_engine.consultar_eventos(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        tipo_evento=event_engine.TIPO_FINANCIERO,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    # gasto por (item, dia)
    por_item_dia = defaultdict(lambda: defaultdict(float))
    for e in eventos:
        sub = (e["subtipo_evento"] or "").upper()
        if sub in ("GASTO", "AJUSTE"):
            item = e["descripcion_normalizada"] or "SIN_ITEM"
            por_item_dia[item][e["fecha"]] += e["valor"] or 0

    alertas = []
    for item, dias in por_item_dia.items():
        valores = list(dias.values())
        if len(valores) < 3:
            continue
        media = sum(valores) / len(valores)
        var = sum((v - media) ** 2 for v in valores) / len(valores)
        desv = sqrt(var)
        if desv == 0:
            continue
        umbral = media + k * desv
        for fecha, valor in dias.items():
            if valor > umbral:
                alertas.append({
                    "item": item,
                    "fecha": fecha,
                    "valor": round(valor, 0),
                    "promedio": round(media, 0),
                    "umbral": round(umbral, 0),
                    "exceso": round(valor - umbral, 0),
                    "clasificacion": config.clasificar_costo(item),
                })

    alertas.sort(key=lambda a: a["exceso"], reverse=True)
    return {"total_alertas": len(alertas), "alertas": alertas}
