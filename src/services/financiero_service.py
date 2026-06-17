"""
financiero_service.py — CAPA FINANCIERA (dinero, movimientos, trazabilidad).

Orquesta el registro de un movimiento: homologa, persiste en la tabla
operativa (movimientos) y emite el evento inmutable correspondiente en el
repositorio central de eventos. Asi conviven el CRUD legible y el event log.
"""

from datetime import date

import db
import event_engine
import normalizador


def registrar_movimiento(responsable_id, tipo_id, monto, cc_id=None,
                         item_id=None, obra_id=None, fecha=None,
                         observacion=None, soporte=None, usuario=None):
    """
    Registra un movimiento financiero y su evento homologado.

    Retorna dict con recibo, evento_id y la homologacion aplicada.
    """
    fecha = fecha or date.today().isoformat()
    recibo = db.siguiente_consecutivo()

    db.insertar_movimiento(
        recibo=recibo,
        fecha_movimiento=fecha,
        responsable_id=responsable_id,
        tipo_id=tipo_id,
        item_id=item_id,
        monto=monto,
        cc_id=cc_id,
        obra_id=obra_id,
        observacion=observacion,
        soporte=soporte,
    )

    # recuperar el id real del movimiento recien insertado
    with db.conectar() as conn:
        fila = conn.execute(
            "SELECT id FROM movimientos WHERE recibo = ? ORDER BY id DESC LIMIT 1",
            (recibo,),
        ).fetchone()
        movimiento_id = fila["id"] if fila else None

        tipo_row = conn.execute(
            "SELECT texto FROM tipo_movimientos WHERE id = ?", (tipo_id,)
        ).fetchone()
        subtipo = (tipo_row["texto"] if tipo_row else "GASTO").upper()

        item_row = None
        if item_id:
            item_row = conn.execute(
                "SELECT nombre FROM items WHERE id = ?", (item_id,)
            ).fetchone()

    descripcion = (item_row["nombre"] if item_row else None) or observacion or ""
    norm = normalizador.normalizar_item(descripcion)

    evento_id = event_engine.registrar_evento(
        fecha=fecha,
        tipo_evento=event_engine.TIPO_FINANCIERO,
        subtipo_evento=subtipo,
        contrato_id=obra_id,
        centro_costo_id=cc_id,
        responsable_id=responsable_id,
        item_id=item_id,
        valor=monto,
        descripcion_original=descripcion,
        descripcion_normalizada=norm["canonico"],
        score_confiabilidad=norm["score"],
        fuente="movimientos",
        usuario=usuario,
        origen_tabla="movimientos",
        origen_id=movimiento_id,
    )

    return {
        "recibo": recibo,
        "movimiento_id": movimiento_id,
        "evento_id": evento_id,
        "homologacion": norm,
    }


def consultar_movimientos(**filtros):
    return db.listar_movimientos(**filtros)


def resumen_financiero(**filtros):
    return {
        "por_item": db.resumen_por_item(**filtros),
        "por_centro_costo": db.resumen_por_centro_costos(**{
            k: v for k, v in filtros.items() if k != "tipo"
        }),
    }
