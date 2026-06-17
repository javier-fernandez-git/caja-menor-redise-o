"""
mdm_service.py — fachada de GOBERNANZA DE DATOS (Etapa 3).

Expone el MDM (maestros, convergencia de IDs, permisos por area) y el catalogo
de equivalencias administrable a la UI/API.
"""

import mdm
import normalizador


# --- Consultas ---
def maestros(dominio=None, estado=None):
    return mdm.listar_maestros(dominio=dominio, estado=estado)


def alias(dominio=None, master_id=None):
    return mdm.listar_alias(dominio=dominio, master_id=master_id)


def permisos(area=None):
    return mdm.listar_permisos(area=area)


def dominios():
    return list(mdm.DOMINIOS.keys())


# --- Convergencia de IDs (Regla #3) ---
def resolver(dominio, texto):
    return mdm.resolver_id_universal(dominio, texto)


# --- CRUD gobernado (con permisos por area) ---
def crear_maestro(dominio, nombre, area_actor, codigo=None):
    return mdm.crear_maestro(dominio, nombre, area_actor, codigo=codigo)


def registrar_alias(dominio, master_id, alias_texto, area_actor=None):
    return mdm.registrar_alias(dominio, master_id, alias_texto,
                               area_actor=area_actor)


def cambiar_estado(dominio, master_id, estado, area_actor):
    return mdm.cambiar_estado(dominio, master_id, estado, area_actor)


# --- Catalogo de equivalencias administrable desde UI ---
def registrar_equivalencia(dominio, variante, canonico, canonico_id=None):
    return normalizador.aprender_equivalencia(
        dominio, variante, canonico, canonico_id, origen="manual")
