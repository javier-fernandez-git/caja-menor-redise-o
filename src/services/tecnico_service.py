"""
tecnico_service.py — CAPA TECNICA (produccion / ejecucion fisica).

Registra unidades constructivas ejecutadas y emite el evento TECNICO
correspondiente, para que timeline, costeo y analitica las vean en vivo
(sin esperar al backfill del proximo arranque).
"""

from datetime import date

import db
import event_engine
import normalizador


def registrar_unidad_ejecutada(movimiento_id, unidad_constructiva_id, cantidad,
                               observacion=None, fecha=None, usuario=None):
    """Inserta la produccion y emite su evento inmutable. Retorna ids."""
    fecha = fecha or date.today().isoformat()

    ue_id = db.registrar_unidad_ejecutada(
        movimiento_id=movimiento_id,
        unidad_constructiva_id=unidad_constructiva_id,
        cantidad=cantidad,
        observacion=observacion,
        fecha=fecha,
        usuario=usuario,
    )

    # Datos de contexto del movimiento asociado + nombre de la unidad.
    with db.conectar() as conn:
        mov = conn.execute(
            "SELECT responsable_id, obra_id, cc_id FROM movimientos WHERE id = ?",
            (movimiento_id,),
        ).fetchone()
        unidad = conn.execute(
            "SELECT nombre FROM unidades_constructivas WHERE id = ?",
            (unidad_constructiva_id,),
        ).fetchone()

    unidad_nombre = unidad["nombre"] if unidad else ""

    evento_id = event_engine.registrar_evento(
        fecha=fecha,
        tipo_evento=event_engine.TIPO_TECNICO,
        subtipo_evento="PRODUCCION",
        contrato_id=mov["obra_id"] if mov else None,
        centro_costo_id=mov["cc_id"] if mov else None,
        responsable_id=mov["responsable_id"] if mov else None,
        valor=0,
        cantidad=cantidad,
        descripcion_original=unidad_nombre,
        descripcion_normalizada=normalizador._canonizar(unidad_nombre),
        score_confiabilidad=1.0,
        fuente="unidades_ejecutadas",
        usuario=usuario,
        origen_tabla="unidades_ejecutadas",
        origen_id=ue_id,
    )

    return {"unidad_ejecutada_id": ue_id, "evento_id": evento_id}


def consultar(**filtros):
    return db.consultar_unidades_ejecutadas(**filtros)
