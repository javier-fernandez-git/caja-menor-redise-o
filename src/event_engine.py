"""
event_engine.py — CAPA DE EVENTOS INMUTABLES (Regla #1: TODO ES UN EVENTO)

Cada evento responde: que ocurrio, cuando, quien, donde, cuanto costo,
a que contrato pertenece y con que confiabilidad se registro.

Los eventos NO se sobrescriben. Una correccion es un evento nuevo
(subtipo CORRECCION) que referencia al anterior; el historico se conserva.

Repositorio central: tabla eventos_corporativos.
Todos los modulos deben enviar aqui eventos ya homologados.
"""

from datetime import datetime

import db
import normalizador


TIPO_FINANCIERO = "FINANCIERO"
TIPO_TECNICO = "TECNICO"


# ----------------------------------------------------------------------
# REGISTRO DE EVENTOS (inmutable)
# ----------------------------------------------------------------------

def registrar_evento(
    fecha,
    tipo_evento,
    subtipo_evento=None,
    contrato_id=None,
    centro_costo_id=None,
    dependencia_id=None,
    responsable_id=None,
    item_id=None,
    valor=0,
    cantidad=None,
    descripcion_original=None,
    descripcion_normalizada=None,
    fuente="caja_menor",
    usuario=None,
    score_confiabilidad=None,
    origen_tabla=None,
    origen_id=None,
    dominio_normalizacion="item",
    conn=None,
):
    """
    Inserta un evento inmutable y retorna su evento_id.

    Si descripcion_normalizada / score no se entregan, se calculan con el
    motor de homologacion a partir de descripcion_original.
    """
    if descripcion_normalizada is None and descripcion_original is not None:
        norm = normalizador.motor_normalizacion(
            descripcion_original, dominio_normalizacion
        )
        descripcion_normalizada = norm["canonico"]
        if score_confiabilidad is None:
            score_confiabilidad = norm["score"]

    if score_confiabilidad is None:
        score_confiabilidad = 1.0

    timestamp = datetime.now().isoformat(timespec="seconds")

    sql = """
        INSERT OR IGNORE INTO eventos_corporativos
            (fecha, tipo_evento, subtipo_evento, contrato_id, centro_costo_id,
             dependencia_id, responsable_id, item_id, valor, cantidad,
             descripcion_original, descripcion_normalizada, fuente, usuario,
             timestamp_creacion, score_confiabilidad, origen_tabla, origen_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        fecha, tipo_evento, subtipo_evento, contrato_id, centro_costo_id,
        dependencia_id, responsable_id, item_id, valor, cantidad,
        descripcion_original, descripcion_normalizada, fuente, usuario,
        timestamp, score_confiabilidad, origen_tabla, origen_id,
    )

    if conn is not None:
        cur = conn.execute(sql, params)
        return cur.lastrowid

    with db.conectar() as own:
        cur = own.execute(sql, params)
        return cur.lastrowid


# ----------------------------------------------------------------------
# CONSULTAS TEMPORALES (Regla #4: la fecha es el eje de correlacion)
# ----------------------------------------------------------------------

def consultar_eventos(
    contrato_id=None,
    centro_costo_id=None,
    responsable_id=None,
    tipo_evento=None,
    fecha_ini=None,
    fecha_fin=None,
    score_minimo=None,
):
    sql = """
        SELECT
            e.*,
            o.nombre   AS contrato,
            c.contrato AS centro_costo,
            r.nombre   AS responsable,
            i.nombre   AS item
        FROM eventos_corporativos e
        LEFT JOIN obras            o ON o.id = e.contrato_id
        LEFT JOIN centro_de_costos c ON c.id = e.centro_costo_id
        LEFT JOIN responsables     r ON r.id = e.responsable_id
        LEFT JOIN items            i ON i.id = e.item_id
        WHERE 1=1
    """
    params = []
    if contrato_id:
        sql += " AND e.contrato_id = ?"
        params.append(contrato_id)
    if centro_costo_id:
        sql += " AND e.centro_costo_id = ?"
        params.append(centro_costo_id)
    if responsable_id:
        sql += " AND e.responsable_id = ?"
        params.append(responsable_id)
    if tipo_evento:
        sql += " AND e.tipo_evento = ?"
        params.append(tipo_evento)
    if fecha_ini:
        sql += " AND e.fecha >= ?"
        params.append(fecha_ini)
    if fecha_fin:
        sql += " AND e.fecha <= ?"
        params.append(fecha_fin)
    if score_minimo is not None:
        sql += " AND e.score_confiabilidad >= ?"
        params.append(score_minimo)
    sql += " ORDER BY e.fecha, e.evento_id"

    with db.conectar() as conn:
        return [dict(r) for r in conn.execute(sql, params)]


# ----------------------------------------------------------------------
# BACKFILL: proyectar movimientos existentes como eventos
# Idempotente gracias a UNIQUE(origen_tabla, origen_id).
# ----------------------------------------------------------------------

def backfill_desde_movimientos():
    """
    Convierte cada movimiento financiero y cada unidad ejecutada existente
    en un evento corporativo homologado. Se puede llamar muchas veces.
    """
    insertados = 0
    with db.conectar() as conn:
        # --- Movimientos financieros ---
        movimientos = conn.execute("""
            SELECT
                m.id, m.fecha_movimiento, m.responsable_id, m.obra_id,
                m.item_id, m.cc_id, m.monto, m.observacion, m.soporte,
                t.texto AS tipo, i.nombre AS item
            FROM movimientos m
            LEFT JOIN tipo_movimientos t ON t.id = m.tipo_id
            LEFT JOIN items i ON i.id = m.item_id
        """).fetchall()

        for m in movimientos:
            descripcion = m["item"] or m["observacion"] or ""
            norm = normalizador.motor_normalizacion(descripcion, "item")
            cur = registrar_evento(
                fecha=m["fecha_movimiento"],
                tipo_evento=TIPO_FINANCIERO,
                subtipo_evento=(m["tipo"] or "GASTO").upper(),
                contrato_id=m["obra_id"],
                centro_costo_id=m["cc_id"],
                responsable_id=m["responsable_id"],
                item_id=m["item_id"],
                valor=m["monto"] or 0,
                descripcion_original=descripcion,
                descripcion_normalizada=norm["canonico"],
                score_confiabilidad=norm["score"],
                fuente="movimientos",
                origen_tabla="movimientos",
                origen_id=m["id"],
                conn=conn,
            )
            if cur:
                insertados += 1

        # --- Unidades ejecutadas (produccion tecnica) ---
        unidades = conn.execute("""
            SELECT
                ue.id, ue.fecha, ue.cantidad, ue.observacion, ue.usuario,
                m.responsable_id, m.obra_id, m.cc_id,
                uc.nombre AS unidad
            FROM unidades_ejecutadas ue
            JOIN movimientos m ON m.id = ue.movimiento_id
            JOIN unidades_constructivas uc ON uc.id = ue.unidad_constructiva_id
        """).fetchall()

        for u in unidades:
            cur = registrar_evento(
                fecha=u["fecha"],
                tipo_evento=TIPO_TECNICO,
                subtipo_evento="PRODUCCION",
                contrato_id=u["obra_id"],
                centro_costo_id=u["cc_id"],
                responsable_id=u["responsable_id"],
                valor=0,
                cantidad=u["cantidad"],
                descripcion_original=u["unidad"],
                descripcion_normalizada=normalizador._canonizar(u["unidad"]),
                score_confiabilidad=1.0,
                fuente="unidades_ejecutadas",
                usuario=u["usuario"],
                origen_tabla="unidades_ejecutadas",
                origen_id=u["id"],
                conn=conn,
            )
            if cur:
                insertados += 1

    return insertados


if __name__ == "__main__":
    db.inicializar()
    eventos = consultar_eventos()
    print(f"Eventos en el repositorio: {len(eventos)}")
    for e in eventos[:10]:
        print(f"  {e['fecha']} | {e['tipo_evento']:10} | {e['subtipo_evento']:11} "
              f"| {e['descripcion_normalizada']:22} | ${e['valor']:>12,.0f} "
              f"| score={e['score_confiabilidad']}")
