"""
config.py — Configuracion central y VERSIONADO de la aplicacion.

Versionado: SemVer (MAJOR.MINOR.PATCH).
    MAJOR -> cambios incompatibles / hitos de arquitectura
    MINOR -> nueva etapa o capacidad retrocompatible
    PATCH -> correcciones

Mapa de versiones <-> etapas del ROADMAP:
    0.1.0  Etapa 1  Construccion del nucleo (event sourcing, homologacion,
                    dos contabilidades, services, timeline, score)
    0.2.0  Etapa 2  Inteligencia operacional (motor causal, correlaciones,
                    prediccion, deteccion de sobreconsumo)
    0.3.0  Etapa 3  Gobernanza de datos / MDM (maestros, convergencia de IDs,
                    permisos por area, equivalencias administrables)
    0.4.0  Etapa 4  Analitica avanzada + PDF (tablero gerencial, liquidaciones,
                    reportes financieros y trazabilidad con QR y consecutivo)
"""

APP_NAME = "Sistema de Reconstruccion Operacional-Financiera"
APP_VERSION = "0.5.1"
ETAPA_ACTUAL = "Etapa 5 - UI para usuarios inconsistentes (cierre)"

# Clave de sesion Flask. En produccion definir SECRET_KEY por variable de entorno.
import os
SECRET_KEY = os.environ.get("SECRET_KEY", "caja-menor-dev-secret-cambiar")

# ----------------------------------------------------------------------
# ROLES Y PERMISOS DE PANTALLA
# Separa el registro operativo de la analitica gerencial:
# los digitadores NO acceden al analisis.
# ----------------------------------------------------------------------
ROLES = ("admin", "gerente", "digitador")

# Que pantallas puede ver cada rol.
ACCESO_PANTALLAS = {
    "digitador": {"operativo"},
    "gerente":   {"gerencial"},
    "admin":     {"operativo", "gerencial", "configuracion"},
}

# Pantalla de inicio por rol.
INICIO_POR_ROL = {
    "digitador": "operativo",
    "gerente":   "gerencial",
    "admin":     "gerencial",
}


def puede_ver(rol, pantalla):
    return pantalla in ACCESO_PANTALLAS.get(rol, set())


# ----------------------------------------------------------------------
# CLASIFICACION DE COSTOS (modelo economico del contrato)
# Items canonicos -> directos | indirectos.
# Configurable: el motor causal usa esto para explicar variaciones.
# ----------------------------------------------------------------------

COSTOS_DIRECTOS = {
    "MATERIALES",
    "MANO_DE_OBRA",
    "AGUA",            # agua para perfilacion / produccion
}

COSTOS_INDIRECTOS = {
    "COMBUSTIBLE",
    "ARRIENDO",
    "ARRIENDO_VEHICULOS",
    "ALIMENTACION",
    "MANTENIMIENTO_VEHICULAR",
    "BODEGAJE",
    "GASTOS_MENORES",
    "PEAJES",
}

# Porcentaje por defecto del modelo economico (75% directos / 25% indirectos)
PORC_DIRECTOS_DEFAULT = 0.75


def clasificar_costo(item_canonico):
    """Devuelve 'DIRECTO', 'INDIRECTO' o 'NO_CLASIFICADO'."""
    if item_canonico in COSTOS_DIRECTOS:
        return "DIRECTO"
    if item_canonico in COSTOS_INDIRECTOS:
        return "INDIRECTO"
    return "NO_CLASIFICADO"


def version_info():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "etapa": ETAPA_ACTUAL,
    }
