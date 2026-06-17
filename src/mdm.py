"""
mdm.py — GOBERNANZA DE DATOS / MASTER DATA MANAGEMENT (Etapa 3)

Implementa el MDM basico exigido por el prompt:

  * Entidades maestras por dominio (contrato, centro_costo, item, dependencia,
    sede, empleado) = el ID corporativo universal (Regla #3).
  * Convergencia de IDs: aunque cada area diga "proyecto", "frente" o
    "contrato", todos los nombres/alias apuntan al mismo maestro.
  * Permisos por area: solo finanzas crea centros de costo, solo RRHH crea
    empleados, etc.

No reemplaza los catalogos operativos (obras, items, ...); los gobierna por
encima, conservando el enlace `catalogo_id`.
"""

import re
from datetime import datetime
from difflib import SequenceMatcher

import db
import normalizador


# ----------------------------------------------------------------------
# Dominios maestros y su origen / propietario
#   dominio -> (tabla_catalogo, columna_nombre, area_propietaria, dominio_homologacion)
# ----------------------------------------------------------------------

DOMINIOS = {
    "contrato":     ("obras",            "nombre",   "gerencia",     "contrato"),
    "centro_costo": ("centro_de_costos", "contrato", "finanzas",     "centro_costo"),
    "item":         ("items",            "nombre",   "operaciones",  "item"),
    "empleado":     ("responsables",     "nombre",   "rrhh",         None),
    "dependencia":  (None,               None,       "rrhh",         "dependencia"),
    "sede":         (None,               None,       "administracion", None),
}

# Permisos por defecto: (area, dominio, puede_crear, puede_editar)
PERMISOS_DEFAULT = [
    ("finanzas",       "centro_costo", 1, 1),
    ("finanzas",       "contrato",     0, 1),
    ("gerencia",       "contrato",     1, 1),
    ("rrhh",           "empleado",     1, 1),
    ("rrhh",           "dependencia",  1, 1),
    ("operaciones",    "item",         1, 1),
    ("compras",        "item",         0, 1),
    ("administracion", "sede",         1, 1),
]


class PermisoDenegado(Exception):
    """Se lanza cuando un area intenta una accion no autorizada sobre un dominio."""


# ----------------------------------------------------------------------
# SIEMBRA
# ----------------------------------------------------------------------

def sembrar_permisos():
    with db.conectar() as conn:
        for area, dominio, crear, editar in PERMISOS_DEFAULT:
            conn.execute(
                """
                INSERT OR IGNORE INTO mdm_permisos
                    (area, dominio, puede_crear, puede_editar)
                VALUES (?, ?, ?, ?)
                """,
                (area, dominio, crear, editar),
            )


def _codigo_desde_nombre(nombre):
    """Extrae el codigo corporativo (ej. 'OT 373460551') si esta en el nombre."""
    m = re.search(r"\bOT\s*\d+", nombre or "", flags=re.IGNORECASE)
    if m:
        return re.sub(r"\s+", " ", m.group(0).upper())
    return None


def sembrar_maestros_desde_catalogos():
    """
    Crea un maestro por cada entrada de los catalogos operativos y de las
    dependencias canonicas del normalizador. Idempotente.
    """
    creados = 0
    ahora = datetime.now().isoformat(timespec="seconds")

    with db.conectar() as conn:
        for dominio, (tabla, columna, area, _dom_h) in DOMINIOS.items():
            if tabla:
                filas = conn.execute(
                    f"SELECT id, {columna} AS nombre FROM {tabla}"
                ).fetchall()
                for f in filas:
                    nombre = (f["nombre"] or "").strip().upper()
                    if not nombre:
                        continue
                    cur = conn.execute(
                        """
                        INSERT OR IGNORE INTO mdm_maestros
                            (dominio, codigo, nombre_canonico, area_propietaria,
                             estado, catalogo_id, creado_en)
                        VALUES (?, ?, ?, ?, 'ACTIVO', ?, ?)
                        """,
                        (dominio, _codigo_desde_nombre(nombre), nombre, area,
                         f["id"], ahora),
                    )
                    creados += cur.rowcount

        # dependencias: desde los canonicos del normalizador
        dep_canonicos = sorted(set(
            normalizador.diccionario_equivalencias.get("dependencia", {}).values()
        ))
        for nombre in dep_canonicos:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO mdm_maestros
                    (dominio, codigo, nombre_canonico, area_propietaria,
                     estado, creado_en)
                VALUES ('dependencia', NULL, ?, 'rrhh', 'ACTIVO', ?)
                """,
                (nombre, ahora),
            )
            creados += cur.rowcount

    return creados


# ----------------------------------------------------------------------
# PERMISOS
# ----------------------------------------------------------------------

def puede(area, dominio, accion="crear"):
    """accion: 'crear' | 'editar'. Devuelve bool."""
    columna = "puede_crear" if accion == "crear" else "puede_editar"
    with db.conectar() as conn:
        fila = conn.execute(
            f"SELECT {columna} AS permitido FROM mdm_permisos "
            "WHERE area = ? AND dominio = ?",
            (area, dominio),
        ).fetchone()
    return bool(fila and fila["permitido"])


def listar_permisos(area=None):
    sql = "SELECT area, dominio, puede_crear, puede_editar FROM mdm_permisos"
    params = []
    if area:
        sql += " WHERE area = ?"
        params.append(area)
    sql += " ORDER BY area, dominio"
    with db.conectar() as conn:
        return [dict(r) for r in conn.execute(sql, params)]


# ----------------------------------------------------------------------
# CRUD GOBERNADO
# ----------------------------------------------------------------------

def crear_maestro(dominio, nombre, area_actor, codigo=None, area_propietaria=None):
    """
    Crea una entidad maestra, validando que `area_actor` tenga permiso de
    creacion sobre el dominio. Lanza PermisoDenegado / ValueError.
    """
    if dominio not in DOMINIOS:
        raise ValueError(f"Dominio desconocido: {dominio}")
    if not puede(area_actor, dominio, "crear"):
        raise PermisoDenegado(
            f"El area '{area_actor}' no puede crear maestros de '{dominio}'."
        )

    nombre = (nombre or "").strip().upper()
    if not nombre:
        raise ValueError("El nombre del maestro es obligatorio.")

    area_propietaria = area_propietaria or DOMINIOS[dominio][2]
    ahora = datetime.now().isoformat(timespec="seconds")
    with db.conectar() as conn:
        cur = conn.execute(
            """
            INSERT INTO mdm_maestros
                (dominio, codigo, nombre_canonico, area_propietaria,
                 estado, creado_en)
            VALUES (?, ?, ?, ?, 'ACTIVO', ?)
            ON CONFLICT(dominio, nombre_canonico) DO NOTHING
            """,
            (dominio, codigo or _codigo_desde_nombre(nombre), nombre,
             area_propietaria, ahora),
        )
        if cur.rowcount == 0:
            fila = conn.execute(
                "SELECT id FROM mdm_maestros WHERE dominio = ? AND nombre_canonico = ?",
                (dominio, nombre),
            ).fetchone()
            return fila["id"]
        return cur.lastrowid


def registrar_alias(dominio, master_id, alias, area_actor=None, origen="manual"):
    """Asocia un nombre alterno a un maestro (convergencia de IDs)."""
    if area_actor is not None and not puede(area_actor, dominio, "editar"):
        raise PermisoDenegado(
            f"El area '{area_actor}' no puede editar maestros de '{dominio}'."
        )
    alias_limpio = normalizador.limpiar_texto(alias)
    if not alias_limpio:
        raise ValueError("Alias vacio.")
    with db.conectar() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO mdm_alias (dominio, master_id, alias, origen)
            VALUES (?, ?, ?, ?)
            """,
            (dominio, master_id, alias_limpio, origen),
        )
    return True


def cambiar_estado(dominio, master_id, estado, area_actor):
    if estado not in ("ACTIVO", "INACTIVO"):
        raise ValueError("Estado invalido.")
    if not puede(area_actor, dominio, "editar"):
        raise PermisoDenegado(
            f"El area '{area_actor}' no puede editar maestros de '{dominio}'."
        )
    with db.conectar() as conn:
        conn.execute(
            "UPDATE mdm_maestros SET estado = ? WHERE id = ? AND dominio = ?",
            (estado, master_id, dominio),
        )
    return True


# ----------------------------------------------------------------------
# CONVERGENCIA DE IDs (Regla #3)
# ----------------------------------------------------------------------

def resolver_id_universal(dominio, texto):
    """
    Resuelve cualquier nombre/alias al maestro universal del dominio.

    Estrategia: alias exacto -> nombre canonico exacto -> homologacion ->
    similitud aproximada. Devuelve dict con metodo y score, o master_id None.
    """
    if dominio not in DOMINIOS:
        raise ValueError(f"Dominio desconocido: {dominio}")

    limpio = normalizador.limpiar_texto(texto)
    if not limpio:
        return {"master_id": None, "metodo": "vacio", "score": 0.0}

    with db.conectar() as conn:
        # 1) alias exacto
        fila = conn.execute(
            """
            SELECT m.* FROM mdm_alias a
            JOIN mdm_maestros m ON m.id = a.master_id
            WHERE a.dominio = ? AND a.alias = ?
            """,
            (dominio, limpio),
        ).fetchone()
        if fila:
            return _resultado(fila, "alias", 1.0)

        # 2) nombre canonico exacto
        fila = conn.execute(
            "SELECT * FROM mdm_maestros WHERE dominio = ? AND nombre_canonico = ?",
            (dominio, limpio),
        ).fetchone()
        if fila:
            return _resultado(fila, "exacto", 1.0)

        maestros = conn.execute(
            "SELECT * FROM mdm_maestros WHERE dominio = ?", (dominio,)
        ).fetchall()

    # 3) homologacion semantica -> reintenta match exacto sobre canonico
    dom_h = DOMINIOS[dominio][3]
    if dom_h:
        norm = normalizador.motor_normalizacion(texto, dom_h)
        objetivo = normalizador.limpiar_texto(
            norm["canonico"].replace("_", " ")
        )
        for m in maestros:
            if normalizador.limpiar_texto(m["nombre_canonico"]) == objetivo:
                return _resultado(m, "homologado", norm["score"])

    # 4) contencion por tokens: el texto del usuario es un subconjunto del
    #    nombre maestro (ej. "libano 2000" dentro de "LIBANO 2000 OT 3734...").
    tokens_in = set(limpio.split())
    if tokens_in:
        contenidos = []
        for m in maestros:
            tokens_m = set(normalizador.limpiar_texto(m["nombre_canonico"]).split())
            if tokens_in.issubset(tokens_m):
                contenidos.append((m, len(tokens_in) / len(tokens_m)))
        if contenidos:
            mejor_m, ratio = max(contenidos, key=lambda c: c[1])
            return _resultado(mejor_m, "contenido", round(ratio, 3))

    # 5) similitud aproximada
    mejor, mejor_score = None, 0.0
    for m in maestros:
        ratio = SequenceMatcher(
            None, limpio, normalizador.limpiar_texto(m["nombre_canonico"])
        ).ratio()
        if ratio > mejor_score:
            mejor, mejor_score = m, ratio
    if mejor and mejor_score >= normalizador.UMBRAL_INFERENCIA:
        return _resultado(mejor, "inferido", round(mejor_score, 3))

    return {"master_id": None, "metodo": "no_encontrado", "score": 0.0,
            "sugerencia": dict(mejor) if mejor else None,
            "similitud_sugerencia": round(mejor_score, 3) if mejor else 0.0}


def _resultado(fila, metodo, score):
    return {
        "master_id": fila["id"],
        "dominio": fila["dominio"],
        "codigo": fila["codigo"],
        "nombre_canonico": fila["nombre_canonico"],
        "area_propietaria": fila["area_propietaria"],
        "estado": fila["estado"],
        "metodo": metodo,
        "score": score,
    }


# ----------------------------------------------------------------------
# CONSULTAS
# ----------------------------------------------------------------------

def listar_maestros(dominio=None, estado=None):
    sql = "SELECT * FROM mdm_maestros WHERE 1=1"
    params = []
    if dominio:
        sql += " AND dominio = ?"
        params.append(dominio)
    if estado:
        sql += " AND estado = ?"
        params.append(estado)
    sql += " ORDER BY dominio, nombre_canonico"
    with db.conectar() as conn:
        return [dict(r) for r in conn.execute(sql, params)]


def listar_alias(dominio=None, master_id=None):
    sql = "SELECT * FROM mdm_alias WHERE 1=1"
    params = []
    if dominio:
        sql += " AND dominio = ?"
        params.append(dominio)
    if master_id:
        sql += " AND master_id = ?"
        params.append(master_id)
    with db.conectar() as conn:
        return [dict(r) for r in conn.execute(sql, params)]


if __name__ == "__main__":
    db.inicializar()
    print("Maestros por dominio:")
    for dom in DOMINIOS:
        n = len(listar_maestros(dominio=dom))
        print(f"  {dom:13} {n}")
    print("\nConvergencia de IDs (ejemplos):")
    for dom, texto in [("contrato", "libano 2000"),
                       ("centro_costo", "civil"),
                       ("item", "mantto veh"),
                       ("dependencia", "talento humano")]:
        r = resolver_id_universal(dom, texto)
        print(f"  [{dom:12}] {texto!r:18} -> master_id={r['master_id']} "
              f"{r.get('nombre_canonico','')} ({r['metodo']}, score={r['score']})")
