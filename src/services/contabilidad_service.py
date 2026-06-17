"""
contabilidad_service.py — fachada de las DOS CONTABILIDADES (Regla #5).
"""

import contabilidad


def saldo_caja(**filtros):
    return contabilidad.contabilidad_caja(**filtros)


def costo_obra(**filtros):
    return contabilidad.contabilidad_obra(**filtros)


def estado(**filtros):
    return contabilidad.estado_completo(**filtros)
