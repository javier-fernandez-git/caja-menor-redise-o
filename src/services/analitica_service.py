"""
analitica_service.py — CAPA ANALITICA (Etapa 1: tablero gerencial).

Combina contabilidad, costeo y timeline para producir un tablero gerencial.
Los motores causal/predictivo completos pertenecen a la Etapa 2; aqui se
entrega el tablero base + indicadores de confiabilidad.
"""

import contabilidad
import event_engine
import timeline_engine
import predictive_engine
import db


def dashboard(contrato_id=None, centro_costo_id=None, responsable_id=None,
              fecha_ini=None, fecha_fin=None, top=5):
    filtros = dict(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        responsable_id=responsable_id, fecha_ini=fecha_ini, fecha_fin=fecha_fin,
    )

    estado = contabilidad.estado_completo(**filtros)
    costo_por_item = estado["obra"]["costo_por_item"]
    top_gastos = sorted(
        costo_por_item.items(), key=lambda kv: kv[1], reverse=True
    )[:top]

    eventos = event_engine.consultar_eventos(**filtros)
    confiabilidad = _indicadores_confiabilidad(eventos)

    return {
        "caja": estado["caja"],
        "obra": estado["obra"],
        "top_gastos": [{"item": k, "valor": v} for k, v in top_gastos],
        "total_eventos": len(eventos),
        "confiabilidad": confiabilidad,
    }


def timeline(**filtros):
    return timeline_engine.reconstruir_timeline(**filtros)


def tablero_gerencial(contrato_id=None, centro_costo_id=None, responsable_id=None,
                      fecha_ini=None, fecha_fin=None,
                      valor_contrato=None, duracion_dias=None, top=5):
    """
    Tablero gerencial completo (Etapa 4):
    utilidad, desviaciones, sobrecostos, producción, facturación esperada,
    top gastos y alertas.
    """
    filtros = dict(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        responsable_id=responsable_id, fecha_ini=fecha_ini, fecha_fin=fecha_fin,
    )

    base = dashboard(top=top, **filtros)

    # Alertas de sobreconsumo (sin responsable: el motor filtra por contrato/cc)
    sobreconsumo = predictive_engine.detectar_sobreconsumo(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    # Producción y costos unitarios reales
    tecnico = db.generar_resumen_tecnico(
        responsable_id=responsable_id,
        obra_id=contrato_id,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    # Facturación esperada y utilidad (si se conoce el modelo económico)
    facturacion = None
    if valor_contrato and duracion_dias:
        facturacion = predictive_engine.predecir_facturacion(
            valor_contrato=valor_contrato, duracion_dias=duracion_dias,
            contrato_id=contrato_id, centro_costo_id=centro_costo_id,
            fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    # Indicadores predictivos integrados al tablero (Etapa 6)
    prediccion_gasto = predictive_engine.predecir_gasto(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    costo_obra = base["obra"]["costo_obra"]
    utilidad = facturacion["utilidad_estimada"] if facturacion else None

    return {
        "prediccion_gasto": prediccion_gasto,
        "caja": base["caja"],
        "obra": base["obra"],
        "utilidad_estimada": utilidad,
        "facturacion": facturacion,
        "produccion": {
            "total_unidades": tecnico["total_unidades"],
            "gasto_asociado": tecnico["gasto_asociado"],
            "unidades": tecnico["unidades"],
        },
        "top_gastos": base["top_gastos"],
        "costo_obra": costo_obra,
        "confiabilidad": base["confiabilidad"],
        "alertas": sobreconsumo["alertas"],
        "total_alertas": sobreconsumo["total_alertas"],
    }


def _indicadores_confiabilidad(eventos):
    """Reparte los eventos por nivel de confiabilidad (validado/inferido/sospechoso)."""
    total = len(eventos) or 1
    validados = sum(1 for e in eventos if (e["score_confiabilidad"] or 0) >= 1.0)
    inferidos = sum(1 for e in eventos
                    if 0.7 <= (e["score_confiabilidad"] or 0) < 1.0)
    sospechosos = sum(1 for e in eventos if (e["score_confiabilidad"] or 0) < 0.7)
    return {
        "validados": validados,
        "inferidos": inferidos,
        "sospechosos": sospechosos,
        "pct_validados": round(validados / total * 100, 1),
        "pct_sospechosos": round(sospechosos / total * 100, 1),
    }
