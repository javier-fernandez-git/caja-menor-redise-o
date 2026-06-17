"""
timeline_engine.py — TEMPORALIDAD COMO EJE CENTRAL (Regla #4)

Reconstruye cronologias corporativas. La fecha es el eje universal de
correlacion. Permite responder:

    "Que ocurrio en el contrato X entre el dia A y B?"

agrupando todos los eventos homologados por fecha / contrato / centro_costo.
"""

from collections import defaultdict

import event_engine


def reconstruir_timeline(contrato_id=None, centro_costo_id=None,
                         responsable_id=None, fecha_ini=None, fecha_fin=None):
    """
    Devuelve una lista de dias; cada dia agrupa sus eventos ordenados.

    [
      {
        "fecha": "2026-02-05",
        "eventos": [ {...}, {...} ],
        "gasto_dia": 120000,
        "produccion_dia": 8.0
      },
      ...
    ]
    """
    eventos = event_engine.consultar_eventos(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        responsable_id=responsable_id, fecha_ini=fecha_ini, fecha_fin=fecha_fin,
    )

    por_dia = defaultdict(list)
    for e in eventos:
        por_dia[e["fecha"]].append(e)

    timeline = []
    for fecha in sorted(por_dia.keys()):
        dia_eventos = por_dia[fecha]
        gasto = sum(
            (e["valor"] or 0) for e in dia_eventos
            if e["tipo_evento"] == event_engine.TIPO_FINANCIERO
            and (e["subtipo_evento"] or "").upper() in ("GASTO", "AJUSTE")
        )
        produccion = sum(
            (e["cantidad"] or 0) for e in dia_eventos
            if e["tipo_evento"] == event_engine.TIPO_TECNICO
        )
        timeline.append({
            "fecha": fecha,
            "eventos": [_resumir_evento(e) for e in dia_eventos],
            "gasto_dia": gasto,
            "produccion_dia": produccion,
        })

    return timeline


def _resumir_evento(e):
    """Proyeccion ligera de un evento para la vista cronologica."""
    return {
        "evento_id": e["evento_id"],
        "tipo_evento": e["tipo_evento"],
        "subtipo_evento": e["subtipo_evento"],
        "contrato": e.get("contrato"),
        "centro_costo": e.get("centro_costo"),
        "responsable": e.get("responsable"),
        "descripcion": e["descripcion_normalizada"],
        "valor": e["valor"],
        "cantidad": e["cantidad"],
        "fuente": e["fuente"],
        "score_confiabilidad": e["score_confiabilidad"],
    }


def narrar_timeline(contrato_id=None, centro_costo_id=None,
                    fecha_ini=None, fecha_fin=None):
    """Version texto del timeline (memoria organizacional consultable)."""
    timeline = reconstruir_timeline(
        contrato_id=contrato_id, centro_costo_id=centro_costo_id,
        fecha_ini=fecha_ini, fecha_fin=fecha_fin,
    )
    lineas = []
    for dia in timeline:
        lineas.append(f"\n[{dia['fecha']}]  "
                      f"gasto=${dia['gasto_dia']:,.0f}  "
                      f"produccion={dia['produccion_dia']:g}")
        for ev in dia["eventos"]:
            quien = ev["responsable"] or ev["fuente"]
            if ev["tipo_evento"] == event_engine.TIPO_TECNICO:
                lineas.append(f"   - {quien} ejecuto {ev['descripcion']} "
                              f"x{ev['cantidad']:g}")
            else:
                lineas.append(f"   - {quien} registro {ev['subtipo_evento']} "
                              f"{ev['descripcion']} por ${ev['valor']:,.0f}")
    return "\n".join(lineas)
