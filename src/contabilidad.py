"""
contabilidad.py — DOS CONTABILIDADES SIMULTANEAS (Regla #5)

CONTABILIDAD DE CAJA
    Objetivo: saber cuanto efectivo queda.
        saldo = asignaciones + reembolsos + ajustes_positivos
                - gastos - ajustes_negativos

CONTABILIDAD DE OBRA
    Objetivo: saber cuanto dinero se INVIRTIO.
        costo_obra += gastos
    IMPORTANTE: los reembolsos NO disminuyen el costo de obra,
    porque la inversion si ocurrio.

Ambas se calculan sobre la capa de eventos (event sourcing), nunca sobre
saldos mutables.
"""

import event_engine


# Subtipos que suman/restan en CAJA
_CAJA_ENTRADAS = {"ASIGNACION", "REEMBOLSO"}
_CAJA_SALIDAS = {"GASTO"}
# AJUSTE: el signo lo da el valor (positivo suma, negativo resta).


def _eventos_financieros(**filtros):
    filtros["tipo_evento"] = event_engine.TIPO_FINANCIERO
    return event_engine.consultar_eventos(**filtros)


def contabilidad_caja(contrato_id=None, centro_costo_id=None,
                      responsable_id=None, fecha_ini=None, fecha_fin=None):
    """Flujo de efectivo: cuanto dinero queda disponible."""
    eventos = _eventos_financieros(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        responsable_id=responsable_id, fecha_ini=fecha_ini, fecha_fin=fecha_fin,
    )

    asignaciones = reembolsos = gastos = 0.0
    ajustes_positivos = ajustes_negativos = 0.0

    for e in eventos:
        sub = (e["subtipo_evento"] or "").upper()
        valor = e["valor"] or 0
        if sub == "ASIGNACION":
            asignaciones += valor
        elif sub == "REEMBOLSO":
            reembolsos += valor
        elif sub == "GASTO":
            gastos += valor
        elif sub == "AJUSTE":
            if valor >= 0:
                ajustes_positivos += valor
            else:
                ajustes_negativos += abs(valor)

    saldo = (asignaciones + reembolsos + ajustes_positivos
             - gastos - ajustes_negativos)

    return {
        "asignaciones": asignaciones,
        "reembolsos": reembolsos,
        "ajustes_positivos": ajustes_positivos,
        "gastos": gastos,
        "ajustes_negativos": ajustes_negativos,
        "saldo": saldo,
    }


def contabilidad_obra(contrato_id=None, centro_costo_id=None,
                      responsable_id=None, fecha_ini=None, fecha_fin=None):
    """Inversion real en la obra: solo acumula gastos (y ajustes a costo)."""
    eventos = _eventos_financieros(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        responsable_id=responsable_id, fecha_ini=fecha_ini, fecha_fin=fecha_fin,
    )

    costo_obra = 0.0
    costo_por_item = {}

    for e in eventos:
        sub = (e["subtipo_evento"] or "").upper()
        valor = e["valor"] or 0
        if sub in ("GASTO", "AJUSTE"):
            costo_obra += valor
            clave = e["descripcion_normalizada"] or "SIN_ITEM"
            costo_por_item[clave] = costo_por_item.get(clave, 0) + valor

    return {
        "costo_obra": costo_obra,
        "costo_por_item": costo_por_item,
    }


def estado_completo(contrato_id=None, centro_costo_id=None,
                    responsable_id=None, fecha_ini=None, fecha_fin=None):
    """Ambas contabilidades juntas, para tablero gerencial."""
    return {
        "caja": contabilidad_caja(contrato_id, centro_costo_id,
                                  responsable_id, fecha_ini, fecha_fin),
        "obra": contabilidad_obra(contrato_id, centro_costo_id,
                                  responsable_id, fecha_ini, fecha_fin),
    }
