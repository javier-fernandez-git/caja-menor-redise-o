"""
normalizador.py — MOTOR DE HOMOLOGACION SEMANTICA (Regla #2)

Esta capa es el nucleo del sistema. Transforma lenguaje humano inconsistente
en lenguaje corporativo universal.

    "Mantto Veh" / "Mantenimiento" / "Mantenimiento Veh."  ->  MANTENIMIENTO_VEHICULAR

Componentes:
    - diccionario_equivalencias : variantes humanas -> termino canonico
    - motor_normalizacion()     : resuelve cualquier texto a su canonico + score
    - normalizar_item()
    - normalizar_centro_costo()
    - normalizar_contrato()
    - normalizar_dependencia()

El score_confiabilidad refleja COMO se resolvio el termino:
    1.0  -> coincidencia exacta con catalogo maestro o diccionario (validado)
    0.7  -> coincidencia aproximada (inferido por similitud)
    0.4  -> sin coincidencia, se conserva el texto crudo (sospechoso)
"""

import re
import unicodedata
from difflib import SequenceMatcher

import db

# Umbral minimo de similitud para aceptar una coincidencia aproximada (inferida).
UMBRAL_INFERENCIA = 0.78

SCORE_EXACTO = 1.0
SCORE_INFERIDO = 0.7
SCORE_SOSPECHOSO = 0.4


# ----------------------------------------------------------------------
# DICCIONARIO DE EQUIVALENCIAS BASE
# Sembrado inicial. El sistema aprende y agrega mas con el tiempo.
# clave: dominio -> { variante_normalizada : CANONICO }
# ----------------------------------------------------------------------

diccionario_equivalencias = {
    "item": {
        "MANTTO VEH": "MANTENIMIENTO_VEHICULAR",
        "MANTENIMIENTO": "MANTENIMIENTO_VEHICULAR",
        "MANTENIMIENTO VEH": "MANTENIMIENTO_VEHICULAR",
        "MANTENIMIENTO VEHICULAR": "MANTENIMIENTO_VEHICULAR",
        "MTto": "MANTENIMIENTO_VEHICULAR",
        "GASOLINA": "COMBUSTIBLE",
        "ACPM": "COMBUSTIBLE",
        "DIESEL": "COMBUSTIBLE",
        "GAS": "COMBUSTIBLE",
        "COMBUSTIBLE": "COMBUSTIBLE",
        "AGUA Y HIELO": "AGUA",
        "AGUA PARA PERFILACION": "AGUA",
        "AGUA": "AGUA",
        "PAGO DE ARRIENDO": "ARRIENDO",
        "ARRIENDO": "ARRIENDO",
        "ARRIENDO VEHICULOS": "ARRIENDO_VEHICULOS",
        "PAGO DE MANO DE OBRA": "MANO_DE_OBRA",
        "MANO DE OBRA": "MANO_DE_OBRA",
        "ALIMENTACION": "ALIMENTACION",
        "MATERIALES": "MATERIALES",
        "PAGO DE BODEGAJE": "BODEGAJE",
        "GASTOS MENORES": "GASTOS_MENORES",
    },
    "centro_costo": {
        "INTERNAS": "INTERNAS",
        "OBRA CIVIL": "OBRA_CIVIL",
        "CIVIL": "OBRA_CIVIL",
        "MANTENIMIENTO": "MANTENIMIENTO",
    },
    "contrato": {},
    "dependencia": {
        "RRHH": "RECURSOS_HUMANOS",
        "RECURSOS HUMANOS": "RECURSOS_HUMANOS",
        "TALENTO HUMANO": "RECURSOS_HUMANOS",
        "VEHICULOS": "VEHICULOS",
        "FLOTA": "VEHICULOS",
        "COMPRAS": "COMPRAS",
        "ABASTECIMIENTO": "COMPRAS",
        "SEGURIDAD": "SST",
        "SST": "SST",
        "SEGURIDAD INDUSTRIAL": "SST",
        "CAJA MENOR": "CAJA_MENOR",
        "MANTENIMIENTO": "MANTENIMIENTO",
    },
}


# ----------------------------------------------------------------------
# NORMALIZACION DE TEXTO (limpieza ortografica previa)
# ----------------------------------------------------------------------

def limpiar_texto(texto):
    """Mayusculas, sin acentos, sin puntuacion sobrante, espacios colapsados."""
    if texto is None:
        return ""
    texto = str(texto).strip().upper()
    # quitar acentos
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    # quitar puntuacion final tipica ("VEH." -> "VEH")
    texto = re.sub(r"[.;,_]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _canonizar(texto):
    """Convierte un nombre canonico legible a formato CORPORATIVO_UNIVERSAL."""
    base = limpiar_texto(texto)
    return re.sub(r"\s+", "_", base) if base else ""


# ----------------------------------------------------------------------
# CARGA DEL DICCIONARIO PERSISTIDO + CATALOGOS MAESTROS
# ----------------------------------------------------------------------

def _equivalencias_persistidas(dominio):
    """Lee del diccionario_semantico las equivalencias guardadas en BD."""
    try:
        with db.conectar() as conn:
            filas = conn.execute(
                "SELECT variante, canonico, canonico_id "
                "FROM diccionario_semantico WHERE dominio = ?",
                (dominio,),
            ).fetchall()
        return {f["variante"]: (f["canonico"], f["canonico_id"]) for f in filas}
    except Exception:
        return {}


def _catalogo_maestro(dominio):
    """Devuelve [(id, nombre_canonico)] del catalogo maestro del dominio."""
    mapa = {
        "item": ("items", "nombre"),
        "centro_costo": ("centro_de_costos", "contrato"),
        "contrato": ("obras", "nombre"),
        "dependencia": (None, None),
    }
    tabla, columna = mapa.get(dominio, (None, None))
    if not tabla:
        return []
    with db.conectar() as conn:
        filas = conn.execute(
            f"SELECT id, {columna} AS nombre FROM {tabla}"
        ).fetchall()
    return [(f["id"], f["nombre"]) for f in filas]


# ----------------------------------------------------------------------
# MOTOR DE NORMALIZACION
# ----------------------------------------------------------------------

def motor_normalizacion(texto, dominio):
    """
    Resuelve `texto` al lenguaje corporativo universal del `dominio`.

    Retorna dict:
        {
          "original": str,
          "canonico": str,
          "canonico_id": int | None,
          "score": float,
          "metodo": "exacto" | "inferido" | "sospechoso"
        }
    """
    original = "" if texto is None else str(texto)
    limpio = limpiar_texto(original)

    if not limpio:
        return {
            "original": original, "canonico": "", "canonico_id": None,
            "score": SCORE_SOSPECHOSO, "metodo": "sospechoso",
        }

    # 1) Diccionario en memoria (sembrado) -> exacto
    base = diccionario_equivalencias.get(dominio, {})
    if limpio in base:
        return {
            "original": original, "canonico": base[limpio], "canonico_id": None,
            "score": SCORE_EXACTO, "metodo": "exacto",
        }

    # 2) Diccionario persistido en BD -> exacto
    persistidas = _equivalencias_persistidas(dominio)
    if limpio in persistidas:
        canonico, canonico_id = persistidas[limpio]
        return {
            "original": original, "canonico": canonico, "canonico_id": canonico_id,
            "score": SCORE_EXACTO, "metodo": "exacto",
        }

    # 3) Catalogo maestro: exacto por nombre limpio
    catalogo = _catalogo_maestro(dominio)
    for cid, nombre in catalogo:
        if limpiar_texto(nombre) == limpio:
            return {
                "original": original, "canonico": _canonizar(nombre),
                "canonico_id": cid, "score": SCORE_EXACTO, "metodo": "exacto",
            }

    # 4) Coincidencia aproximada (inferida) contra diccionario + catalogo
    candidatos = []
    for variante, canonico in base.items():
        candidatos.append((variante, canonico, None))
    for variante, (canonico, cid) in persistidas.items():
        candidatos.append((variante, canonico, cid))
    for cid, nombre in catalogo:
        candidatos.append((limpiar_texto(nombre), _canonizar(nombre), cid))

    mejor = None
    mejor_score = 0.0
    for variante, canonico, cid in candidatos:
        ratio = SequenceMatcher(None, limpio, variante).ratio()
        if ratio > mejor_score:
            mejor_score = ratio
            mejor = (canonico, cid)

    if mejor and mejor_score >= UMBRAL_INFERENCIA:
        canonico, cid = mejor
        return {
            "original": original, "canonico": canonico, "canonico_id": cid,
            "score": SCORE_INFERIDO, "metodo": "inferido",
        }

    # 5) Sin coincidencia: se conserva el texto crudo canonizado, marcado sospechoso
    return {
        "original": original, "canonico": _canonizar(limpio), "canonico_id": None,
        "score": SCORE_SOSPECHOSO, "metodo": "sospechoso",
    }


# ----------------------------------------------------------------------
# FUNCIONES OBLIGATORIAS (API publica de la capa)
# ----------------------------------------------------------------------

def normalizar_item(texto):
    return motor_normalizacion(texto, "item")


def normalizar_centro_costo(texto):
    return motor_normalizacion(texto, "centro_costo")


def normalizar_contrato(texto):
    return motor_normalizacion(texto, "contrato")


def normalizar_dependencia(texto):
    return motor_normalizacion(texto, "dependencia")


# ----------------------------------------------------------------------
# APRENDIZAJE: persistir nuevas equivalencias
# ----------------------------------------------------------------------

def aprender_equivalencia(dominio, variante, canonico, canonico_id=None,
                          origen="manual"):
    """Guarda una equivalencia para que futuras entradas se resuelvan exactas."""
    variante_limpia = limpiar_texto(variante)
    if not variante_limpia or not canonico:
        return False
    with db.conectar() as conn:
        conn.execute(
            """
            INSERT INTO diccionario_semantico
                (dominio, variante, canonico, canonico_id, origen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(dominio, variante) DO UPDATE SET
                canonico = excluded.canonico,
                canonico_id = excluded.canonico_id,
                origen = excluded.origen
            """,
            (dominio, variante_limpia, canonico, canonico_id, origen),
        )
    return True


def sembrar_diccionario():
    """Vuelca el diccionario_equivalencias base a la BD (idempotente)."""
    with db.conectar() as conn:
        for dominio, mapa in diccionario_equivalencias.items():
            for variante, canonico in mapa.items():
                conn.execute(
                    """
                    INSERT OR IGNORE INTO diccionario_semantico
                        (dominio, variante, canonico, origen)
                    VALUES (?, ?, ?, 'semilla')
                    """,
                    (dominio, limpiar_texto(variante), canonico),
                )


if __name__ == "__main__":
    db.inicializar()
    pruebas = [
        ("item", "Mantto Veh"),
        ("item", "Mantenimiento Veh."),
        ("item", "gasolina"),
        ("item", "agua para perfilacion"),
        ("item", "xyz raro"),
        ("dependencia", "talento humano"),
    ]
    for dominio, texto in pruebas:
        r = motor_normalizacion(texto, dominio)
        print(f"[{dominio:13}] {texto!r:28} -> {r['canonico']:24} "
              f"score={r['score']} ({r['metodo']})")
