"""
memoria_service.py — fachada de la MEMORIA ORGANIZACIONAL CONSULTABLE (Etapa 6).
"""

import memoria_engine


def consultar(texto):
    return memoria_engine.consultar(texto)


def narrar(**filtros):
    return memoria_engine.narrar(**filtros)


def exportar(formato="md", **filtros):
    return memoria_engine.exportar(formato=formato, **filtros)
