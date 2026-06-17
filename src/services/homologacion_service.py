"""
homologacion_service.py — fachada de la CAPA DE HOMOLOGACION.

Expone el motor de normalizacion a la UI y a los demas services sin que
estos dependan de los detalles internos del normalizador.
"""

import normalizador


def homologar(texto, dominio="item"):
    """Resuelve un texto humano a su forma corporativa universal + score."""
    return normalizador.motor_normalizacion(texto, dominio)


def homologar_item(texto):
    return normalizador.normalizar_item(texto)


def homologar_centro_costo(texto):
    return normalizador.normalizar_centro_costo(texto)


def homologar_contrato(texto):
    return normalizador.normalizar_contrato(texto)


def homologar_dependencia(texto):
    return normalizador.normalizar_dependencia(texto)


def registrar_equivalencia(dominio, variante, canonico, canonico_id=None):
    """Permite a la UI de configuracion ensenar nuevas equivalencias."""
    return normalizador.aprender_equivalencia(
        dominio, variante, canonico, canonico_id, origen="manual"
    )
