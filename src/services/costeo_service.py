"""
costeo_service.py — CAPA DE COSTEO (cruza GASTOS vs PRODUCCION).

Distribuye costos proporcionalmente por dia y produccion para obtener costos
unitarios reales por unidad constructiva, y compara contra el modelo economico
del contrato (esperado vs real).
"""

import db


def calcular_costos_unitarios(**filtros):
    return db.calcular_costos_unitarios(**filtros)


def resumen_tecnico(**filtros):
    return db.generar_resumen_tecnico(**filtros)


def modelo_economico_contrato(valor_contrato, duracion_dias,
                              costos_directos_porcentaje=0.75):
    """
    Calcula lo ESPERADO por dia segun el modelo economico del contrato.

        valor/dia = valor_contrato / duracion_dias
        directo/dia = valor/dia * costos_directos_porcentaje
    """
    if duracion_dias <= 0:
        return {"valor_dia": 0, "directo_dia": 0, "indirecto_dia": 0}

    valor_dia = valor_contrato / duracion_dias
    directo_dia = valor_dia * costos_directos_porcentaje
    indirecto_dia = valor_dia * (1 - costos_directos_porcentaje)
    return {
        "valor_dia": valor_dia,
        "directo_dia": directo_dia,
        "indirecto_dia": indirecto_dia,
        "costos_directos_porcentaje": costos_directos_porcentaje,
        "costos_indirectos_porcentaje": 1 - costos_directos_porcentaje,
    }


def calcular_desviacion(valor_contrato, duracion_dias, gasto_real,
                        dias_transcurridos, costos_directos_porcentaje=0.75):
    """Compara esperado vs real y entrega la desviacion (sobrecosto/ahorro)."""
    modelo = modelo_economico_contrato(
        valor_contrato, duracion_dias, costos_directos_porcentaje
    )
    esperado = modelo["valor_dia"] * max(dias_transcurridos, 0)
    desviacion = gasto_real - esperado
    porcentaje = (desviacion / esperado) if esperado else 0
    return {
        "esperado": esperado,
        "real": gasto_real,
        "desviacion": desviacion,
        "desviacion_porcentaje": porcentaje,
        "estado": "SOBRECOSTO" if desviacion > 0 else "DENTRO_DE_PRESUPUESTO",
    }
