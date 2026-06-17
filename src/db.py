"""
Módulo de base de datos para Caja Menor.
Gestiona la conexión SQLite, esquema y operaciones CRUD.
"""
import sqlite3
import csv
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "caja_menor.db"
UNIDADES_CSV = DATA_DIR / "unidades_constructivas.csv"
OBRAS_CSV = DATA_DIR / "obras.csv"
ITEMS_CSV = DATA_DIR / "descripciones.csv"
RESPONSABLES_CSV = DATA_DIR / "responsables.csv"
TIPOS_CSV = DATA_DIR / "tipo_de_movimientos.csv"
CC_CSV = DATA_DIR / "centro_de_costos.csv"
MOVIMIENTOS_CSV = DATA_DIR / "movimientos.csv"


def conectar():
    """Retorna una conexión con row_factory y foreign keys activados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar():
    """Crea todas las tablas si no existen y siembra el consecutivo."""

    with conectar() as conn:

        conn.executescript("""
            CREATE TABLE IF NOT EXISTS responsables (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS obras (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS centro_de_costos (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                contrato TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS tipo_movimientos (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                texto TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS items (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS unidades_constructivas (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS movimientos (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                recibo         INTEGER NOT NULL,
                fecha_movimiento TEXT  NOT NULL,
                responsable_id INTEGER NOT NULL REFERENCES responsables(id),
                obra_id        INTEGER REFERENCES obras(id),
                tipo_id        INTEGER NOT NULL REFERENCES tipo_movimientos(id),
                item_id        INTEGER REFERENCES items(id),
                monto          INTEGER NOT NULL DEFAULT 0,
                cc_id          INTEGER REFERENCES centro_de_costos(id),
                observacion    TEXT,
                soporte        TEXT
            );

            CREATE TABLE IF NOT EXISTS unidades_ejecutadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movimiento_id INTEGER NOT NULL REFERENCES movimientos(id) ON DELETE CASCADE,
                unidad_constructiva_id INTEGER NOT NULL REFERENCES unidades_constructivas(id),
                cantidad REAL NOT NULL CHECK(cantidad >= 0),
                observacion TEXT,
                fecha TEXT NOT NULL,
                usuario TEXT
            );

            CREATE TABLE IF NOT EXISTS consecutivo (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                ultimo INTEGER NOT NULL DEFAULT 1000
            );

            INSERT OR IGNORE INTO consecutivo (id, ultimo)
            VALUES (1, 1000);

            -- ===================================================
            -- CAPA SEMANTICA (homologacion)
            -- Mapea lenguaje humano inconsistente -> canonico
            -- ===================================================
            CREATE TABLE IF NOT EXISTS diccionario_semantico (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                dominio   TEXT NOT NULL,   -- item | centro_costo | contrato | dependencia
                variante  TEXT NOT NULL,   -- forma normalizada de la entrada humana
                canonico  TEXT NOT NULL,   -- lenguaje corporativo universal
                canonico_id INTEGER,       -- id del catalogo maestro, si aplica
                origen    TEXT DEFAULT 'manual',  -- manual | inferido
                UNIQUE(dominio, variante)
            );

            -- ===================================================
            -- CAPA DE EVENTOS (event sourcing)
            -- Registros inmutables: NO se sobrescriben.
            -- ===================================================
            CREATE TABLE IF NOT EXISTS eventos_corporativos (
                evento_id            INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha                TEXT NOT NULL,
                tipo_evento          TEXT NOT NULL,   -- FINANCIERO | TECNICO | ...
                subtipo_evento       TEXT,            -- GASTO | ASIGNACION | PRODUCCION | ...
                contrato_id          INTEGER,         -- obra / proyecto / frente -> ID universal
                centro_costo_id      INTEGER,
                dependencia_id       INTEGER,
                responsable_id       INTEGER,
                item_id              INTEGER,
                valor                REAL DEFAULT 0,
                cantidad             REAL,
                descripcion_original   TEXT,
                descripcion_normalizada TEXT,
                fuente               TEXT,            -- modulo / tabla de origen
                usuario              TEXT,
                timestamp_creacion   TEXT NOT NULL,
                score_confiabilidad  REAL NOT NULL DEFAULT 1.0,
                origen_tabla         TEXT,            -- idempotencia del backfill
                origen_id            INTEGER,
                UNIQUE(origen_tabla, origen_id)
            );

            CREATE INDEX IF NOT EXISTS idx_eventos_fecha
                ON eventos_corporativos(fecha);
            CREATE INDEX IF NOT EXISTS idx_eventos_contrato
                ON eventos_corporativos(contrato_id, fecha);
            CREATE INDEX IF NOT EXISTS idx_eventos_cc
                ON eventos_corporativos(centro_costo_id, fecha);

            -- ===================================================
            -- GOBERNANZA DE DATOS (MDM basico)
            -- Una entidad maestra por dominio = ID corporativo universal.
            -- Subsume contratos_master / centros_costos_master / items_master
            -- / dependencias_master / sedes_master en una sola tabla por dominio.
            -- ===================================================
            CREATE TABLE IF NOT EXISTS mdm_maestros (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                dominio         TEXT NOT NULL,   -- contrato|centro_costo|item|dependencia|sede|empleado
                codigo          TEXT,            -- codigo corporativo (ej. OT 373460551)
                nombre_canonico TEXT NOT NULL,
                area_propietaria TEXT,           -- finanzas|rrhh|operaciones|compras|gerencia
                estado          TEXT NOT NULL DEFAULT 'ACTIVO',  -- ACTIVO|INACTIVO
                catalogo_id     INTEGER,         -- enlace al catalogo operativo (obras.id, etc.)
                creado_en       TEXT,
                UNIQUE(dominio, nombre_canonico)
            );

            -- Convergencia de IDs (Regla #3): nombres alternos -> mismo maestro.
            CREATE TABLE IF NOT EXISTS mdm_alias (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                dominio   TEXT NOT NULL,
                master_id INTEGER NOT NULL REFERENCES mdm_maestros(id) ON DELETE CASCADE,
                alias     TEXT NOT NULL,
                origen    TEXT DEFAULT 'manual',
                UNIQUE(dominio, alias)
            );

            -- Permisos por area: quien puede crear/editar cada dominio maestro.
            CREATE TABLE IF NOT EXISTS mdm_permisos (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                area         TEXT NOT NULL,
                dominio      TEXT NOT NULL,
                puede_crear  INTEGER NOT NULL DEFAULT 0,
                puede_editar INTEGER NOT NULL DEFAULT 0,
                UNIQUE(area, dominio)
            );

            CREATE INDEX IF NOT EXISTS idx_mdm_maestros_dom
                ON mdm_maestros(dominio, estado);
            CREATE INDEX IF NOT EXISTS idx_mdm_alias_dom
                ON mdm_alias(dominio, alias);

            -- Consecutivo propio de documentos PDF (distinto del recibo).
            CREATE TABLE IF NOT EXISTS consecutivo_pdf (
                id     INTEGER PRIMARY KEY CHECK(id = 1),
                ultimo INTEGER NOT NULL DEFAULT 0
            );
            INSERT OR IGNORE INTO consecutivo_pdf (id, ultimo) VALUES (1, 0);

            -- Usuarios y roles (separa registro operativo de analitica).
            CREATE TABLE IF NOT EXISTS usuarios (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario       TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                rol           TEXT NOT NULL,   -- admin | gerente | digitador
                nombre        TEXT,
                activo        INTEGER NOT NULL DEFAULT 1,
                creado_en     TEXT
            );
        """)

        _migrar_movimientos_financieros(conn)
        _crear_tabla_unidades_ejecutadas(conn)

    importar_responsables()
    importar_obras()
    importar_centros_de_costos()
    importar_tipos_movimiento()
    importar_items_gasto()
    importar_unidades_constructivas()
    separar_unidades_de_items()
    importar_movimientos_historicos()

    # --- Capas nuevas (Etapa 1: nucleo) ---
    # Import perezoso para evitar dependencias circulares (estos modulos usan db).
    import normalizador
    import event_engine
    import mdm
    import auth
    normalizador.sembrar_diccionario()
    event_engine.backfill_desde_movimientos()
    mdm.sembrar_permisos()
    mdm.sembrar_maestros_desde_catalogos()
    auth.sembrar_usuarios_default()


def _columnas_tabla(conn, tabla):
    return [row["name"] for row in conn.execute(f"PRAGMA table_info({tabla})")]


def _crear_tabla_unidades_ejecutadas(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS unidades_ejecutadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movimiento_id INTEGER NOT NULL REFERENCES movimientos(id) ON DELETE CASCADE,
            unidad_constructiva_id INTEGER NOT NULL REFERENCES unidades_constructivas(id),
            cantidad REAL NOT NULL CHECK(cantidad >= 0),
            observacion TEXT,
            fecha TEXT NOT NULL,
            usuario TEXT
        )
    """)


def _migrar_movimientos_financieros(conn):
    """Normaliza movimientos antiguos y elimina datos tecnicos del flujo financiero."""
    columnas = _columnas_tabla(conn, "movimientos")
    columnas_objetivo = {
        "id", "recibo", "fecha_movimiento", "responsable_id", "obra_id",
        "tipo_id", "item_id", "monto", "cc_id", "observacion", "soporte",
    }

    if set(columnas) == columnas_objetivo:
        return

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_nueva (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            recibo         INTEGER NOT NULL,
            fecha_movimiento TEXT  NOT NULL,
            responsable_id INTEGER NOT NULL REFERENCES responsables(id),
            obra_id        INTEGER REFERENCES obras(id),
            tipo_id        INTEGER NOT NULL REFERENCES tipo_movimientos(id),
            item_id        INTEGER REFERENCES items(id),
            monto          INTEGER NOT NULL DEFAULT 0,
            cc_id          INTEGER REFERENCES centro_de_costos(id),
            observacion    TEXT,
            soporte        TEXT
        )
    """)

    if columnas:
        def col(nombre, fallback):
            return nombre if nombre in columnas else fallback

        conn.execute(f"""
            INSERT INTO movimientos_nueva
                (id, recibo, fecha_movimiento, responsable_id, obra_id, tipo_id,
                 item_id, monto, cc_id, observacion, soporte)
            SELECT
                {col("id", "NULL")},
                {col("recibo", "0")},
                COALESCE({col("fecha_movimiento", "NULL")}, {col("fecha_ini", "NULL")}, date('now')),
                {col("responsable_id", "NULL")},
                {col("obra_id", "NULL")},
                {col("tipo_id", "NULL")},
                {col("item_id", "NULL")},
                {col("monto", "0")},
                {col("cc_id", "NULL")},
                {col("observacion", "NULL")},
                {col("soporte", "NULL")}
            FROM movimientos
            WHERE responsable_id IS NOT NULL
              AND tipo_id IS NOT NULL
        """)

    conn.execute("DROP TABLE IF EXISTS movimientos")
    conn.execute("ALTER TABLE movimientos_nueva RENAME TO movimientos")
    conn.execute("PRAGMA foreign_keys = ON")


def _valor_csv(row, campos):
    for campo in campos:
        valor = (row.get(campo) or "").strip()
        if valor:
            return valor.upper()
    return ""


def _id_csv(row):
    valor = (row.get("id") or "").strip()
    return int(valor) if valor.isdigit() else None


def _leer_catalogo_csv(ruta_csv, campos_nombre):
    if not ruta_csv.exists():
        return []

    registros = []
    with ruta_csv.open(newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)
        for row in lector:
            item_id = _id_csv(row)
            nombre = _valor_csv(row, campos_nombre)
            if item_id is None or not nombre:
                continue
            registros.append((item_id, nombre))

    return registros


def _sincronizar_catalogo_csv(ruta_csv, tabla, campos_nombre, columna_movimiento=None):
    """Sincroniza un catalogo CSV con IDs persistentes y conserva registros legacy."""
    registros_csv = _leer_catalogo_csv(ruta_csv, campos_nombre)
    if not registros_csv:
        return 0

    csv_por_id = dict(registros_csv)
    csv_por_nombre = {nombre: item_id for item_id, nombre in registros_csv}
    nuevas_filas = dict(csv_por_id)
    cambios_id = {}

    with conectar() as conn:
        existentes = [dict(r) for r in conn.execute(
            f"SELECT id, nombre FROM {tabla} ORDER BY id"
        )]

        siguiente_legacy = max(
            [10000, *csv_por_id.keys(), *[r["id"] for r in existentes]]
        ) + 1

        for row in existentes:
            actual_id = row["id"]
            nombre = row["nombre"]

            if nombre in csv_por_nombre:
                cambios_id[actual_id] = csv_por_nombre[nombre]
                continue

            nuevo_id = actual_id
            if nuevo_id in nuevas_filas:
                while siguiente_legacy in nuevas_filas:
                    siguiente_legacy += 1
                nuevo_id = siguiente_legacy
                siguiente_legacy += 1

            cambios_id[actual_id] = nuevo_id
            nuevas_filas[nuevo_id] = nombre

        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute(f"DELETE FROM {tabla}")

        for item_id, nombre in sorted(nuevas_filas.items()):
            conn.execute(
                f"INSERT INTO {tabla} (id, nombre) VALUES (?, ?)",
                (item_id, nombre),
            )

        if columna_movimiento:
            for anterior_id, nuevo_id in cambios_id.items():
                if anterior_id != nuevo_id:
                    conn.execute(
                        f"""
                        UPDATE movimientos
                        SET {columna_movimiento} = ?
                        WHERE {columna_movimiento} = ?
                        """,
                        (nuevo_id, anterior_id),
                    )

        conn.execute("PRAGMA foreign_keys = ON")

    return len(registros_csv)


def importar_obras():
    """Importa data/obras.csv a obras sin duplicar registros."""
    return _sincronizar_catalogo_csv(
        OBRAS_CSV, "obras", ("obra", "obra.", "nombre"), "obra_id"
    )


def importar_responsables():
    """Importa data/responsables.csv a responsables."""
    return _sincronizar_catalogo_csv(
        RESPONSABLES_CSV, "responsables", ("nombre", "nombre."), "responsable_id"
    )


def importar_centros_de_costos():
    if not CC_CSV.exists():
        return 0
    registros = _leer_catalogo_csv(CC_CSV, ("contrato", "contrato."))
    with conectar() as conn:
        for cc_id, contrato in registros:
            conn.execute(
                "INSERT OR IGNORE INTO centro_de_costos (id, contrato) VALUES (?, ?)",
                (cc_id, contrato),
            )
    return len(registros)


def importar_tipos_movimiento():
    if not TIPOS_CSV.exists():
        return 0
    registros = _leer_catalogo_csv(TIPOS_CSV, ("texto",))
    tipos_base = {"ASIGNACION", "GASTO", "AJUSTE", "REEMBOLSO"}
    with conectar() as conn:
        for tipo_id, texto in registros:
            conn.execute(
                "INSERT OR IGNORE INTO tipo_movimientos (id, texto) VALUES (?, ?)",
                (tipo_id, texto),
            )
        for texto in tipos_base:
            conn.execute(
                "INSERT OR IGNORE INTO tipo_movimientos (texto) VALUES (?)",
                (texto,),
            )
    return len(registros)


def importar_items_gasto():
    """Importa data/descripciones.csv a items sin mezclar unidades constructivas."""
    return _sincronizar_catalogo_csv(
        ITEMS_CSV, "items", ("item", "nombre"), "item_id"
    )


def importar_unidades_constructivas():
    """Importa data/unidades_constructivas.csv a su propio catálogo."""
    return _sincronizar_catalogo_csv(
        UNIDADES_CSV, "unidades_constructivas", ("unidad", "nombre")
    )


def separar_unidades_de_items():
    """Quita unidades constructivas del catálogo de gastos si una versión anterior las mezcló."""
    nombres_unidades = [nombre for _, nombre in _leer_catalogo_csv(
        UNIDADES_CSV, ("unidad", "nombre")
    )]
    if not nombres_unidades:
        return

    placeholders = ",".join("?" for _ in nombres_unidades)
    with conectar() as conn:
        conn.execute(f"""
            UPDATE movimientos
            SET item_id = NULL
            WHERE item_id IN (
                SELECT id FROM items WHERE upper(nombre) IN ({placeholders})
            )
        """, nombres_unidades)
        conn.execute(f"""
            DELETE FROM items
            WHERE upper(nombre) IN ({placeholders})
        """, nombres_unidades)


def importar_movimientos_historicos():
    """
    Siembra la tabla movimientos desde data/movimientos.csv (una sola vez).

    El CSV guarda nombres, no IDs: aqui se resuelven contra los catalogos.
    Es la actividad humana fragmentada que el sistema reconstruira como
    eventos homologados. Solo corre si la tabla esta vacia (idempotente).
    """
    if not MOVIMIENTOS_CSV.exists():
        return 0

    with conectar() as conn:
        ya_hay = conn.execute("SELECT COUNT(*) AS n FROM movimientos").fetchone()["n"]
        if ya_hay:
            return 0

        def _mapa(tabla, columna):
            return {
                (r[columna] or "").strip().upper(): r["id"]
                for r in conn.execute(f"SELECT id, {columna} AS {columna} FROM {tabla}")
            }

        resp_map = _mapa("responsables", "nombre")
        obra_map = _mapa("obras", "nombre")
        item_map = _mapa("items", "nombre")
        tipo_map = {
            (r["texto"] or "").strip().upper(): r["id"]
            for r in conn.execute("SELECT id, texto FROM tipo_movimientos")
        }

        importados = 0
        with MOVIMIENTOS_CSV.open(newline="", encoding="utf-8-sig") as archivo:
            for row in csv.DictReader(archivo):
                row = {(k or "").strip().lower(): (v or "").strip()
                       for k, v in row.items()}
                tipo_texto = row.get("tipo", "GASTO").upper() or "GASTO"

                # asegurar que el tipo existe (REEMBOLSO no venia en el CSV base)
                if tipo_texto not in tipo_map:
                    cur = conn.execute(
                        "INSERT OR IGNORE INTO tipo_movimientos (texto) VALUES (?)",
                        (tipo_texto,),
                    )
                    fila = conn.execute(
                        "SELECT id FROM tipo_movimientos WHERE texto = ?",
                        (tipo_texto,),
                    ).fetchone()
                    tipo_map[tipo_texto] = fila["id"]

                recibo = row.get("recibo", "0")
                recibo = int(recibo) if recibo.isdigit() else 0
                fecha = row.get("fecha_ini") or row.get("fecha") or ""
                monto = row.get("monto", "0").replace(",", "")
                monto = int(monto) if monto.lstrip("-").isdigit() else 0
                cc = row.get("cc", "")
                cc_id = int(cc) if cc.isdigit() else None

                responsable_id = resp_map.get(row.get("resp", "").upper())
                tipo_id = tipo_map.get(tipo_texto)
                # responsable_id y tipo_id son NOT NULL: omitir filas irresolubles
                if responsable_id is None or tipo_id is None:
                    continue

                conn.execute(
                    """
                    INSERT INTO movimientos
                        (recibo, fecha_movimiento, responsable_id, obra_id,
                         tipo_id, item_id, monto, cc_id, observacion, soporte)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        recibo, fecha,
                        responsable_id,
                        obra_map.get(row.get("obra", "").upper()),
                        tipo_id,
                        item_map.get(row.get("item", "").upper()),
                        monto, cc_id, None, None,
                    ),
                )
                importados += 1

    # mantener el consecutivo por encima del maximo recibo historico
    with conectar() as conn:
        maximo = conn.execute(
            "SELECT MAX(recibo) AS m FROM movimientos"
        ).fetchone()["m"] or 1000
        conn.execute(
            "UPDATE consecutivo SET ultimo = ? WHERE id = 1 AND ultimo < ?",
            (maximo, maximo),
        )

    return importados


# -------------------------------------------------------
# Consultas de catálogos
# -------------------------------------------------------

def obtener_responsables():
    with conectar() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, nombre FROM responsables ORDER BY nombre"
        )]


def obtener_obras():
    with conectar() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, nombre FROM obras ORDER BY id ASC"
        )]


def obtener_centros_de_costos():
    with conectar() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, contrato FROM centro_de_costos ORDER BY id"
        )]


def obtener_tipos_movimiento():
    with conectar() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, texto FROM tipo_movimientos ORDER BY texto"
        )]


def obtener_items():
    with conectar() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, nombre FROM items ORDER BY id ASC"
        )]


def obtener_unidades_constructivas():
    with conectar() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, nombre FROM unidades_constructivas ORDER BY id ASC"
        )]


# -------------------------------------------------------
# Consecutivo
# -------------------------------------------------------

def siguiente_consecutivo():
    """Incrementa en 1 y retorna el próximo número de recibo."""
    with conectar() as conn:
        conn.execute("UPDATE consecutivo SET ultimo = ultimo + 1 WHERE id = 1")
        row = conn.execute(
            "SELECT ultimo FROM consecutivo WHERE id = 1"
        ).fetchone()
        return row["ultimo"]


def obtener_ultimo_consecutivo():
    with conectar() as conn:
        row = conn.execute(
            "SELECT ultimo FROM consecutivo WHERE id = 1"
        ).fetchone()
        return row["ultimo"] if row else 1000


def siguiente_consecutivo_pdf():
    """Consecutivo propio de los documentos PDF generados."""
    with conectar() as conn:
        conn.execute("UPDATE consecutivo_pdf SET ultimo = ultimo + 1 WHERE id = 1")
        row = conn.execute(
            "SELECT ultimo FROM consecutivo_pdf WHERE id = 1"
        ).fetchone()
        return row["ultimo"]


# -------------------------------------------------------
# CRUD de movimientos
# -------------------------------------------------------

def insertar_movimiento(recibo, fecha_movimiento, responsable_id, tipo_id,
                         item_id, monto, cc_id, obra_id=None,
                         observacion=None, soporte=None):
    with conectar() as conn:
        conn.execute("""
            INSERT INTO movimientos
                (recibo, fecha_movimiento, responsable_id, obra_id, tipo_id,
                 item_id, monto, cc_id, observacion, soporte)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (recibo, fecha_movimiento, responsable_id, obra_id, tipo_id,
              item_id, monto, cc_id, observacion, soporte))


def listar_movimientos(responsable_id=None, obra_id=None,
                        fecha_ini=None, fecha_fin=None, tipo=None, cc_id=None):
    """Retorna movimientos con nombres resueltos via JOINs."""
    sql = """
        SELECT
            m.id,
            m.recibo,
            m.fecha_movimiento,
            r.nombre   AS responsable,
            o.nombre   AS obra,
            t.texto    AS tipo,
            i.nombre   AS item,
            c.contrato AS cc,
            m.monto,
            m.observacion,
            m.soporte
        FROM movimientos m
        JOIN responsables     r ON r.id = m.responsable_id
        LEFT JOIN obras       o ON o.id = m.obra_id
        JOIN tipo_movimientos t ON t.id = m.tipo_id
        LEFT JOIN items       i ON i.id = m.item_id
        LEFT JOIN centro_de_costos c ON c.id = m.cc_id
        WHERE 1=1
    """
    params = []
    if responsable_id:
        sql += " AND m.responsable_id = ?"
        params.append(responsable_id)
    if obra_id:
        sql += " AND m.obra_id = ?"
        params.append(obra_id)
    if fecha_ini:
        sql += " AND m.fecha_movimiento >= ?"
        params.append(fecha_ini)
    if fecha_fin:
        sql += " AND m.fecha_movimiento <= ?"
        params.append(fecha_fin)
    if tipo:
        sql += " AND upper(t.texto) = ?"
        params.append(tipo.upper())
    if cc_id:
        sql += " AND m.cc_id = ?"
        params.append(cc_id)
    sql += " ORDER BY m.recibo, m.id"

    with conectar() as conn:
        return [dict(r) for r in conn.execute(sql, params)]

def consultar_movimientos_financieros(
        responsable_id=None,
        obra_id=None,
        fecha_ini=None,
        fecha_fin=None):

    sql = """
        SELECT
            m.id,
            m.recibo,
            m.fecha_movimiento,
            m.monto,
            m.observacion,
            m.soporte,

            r.nombre AS responsable,
            o.nombre AS obra,
            c.contrato AS cc,
            t.texto AS tipo,
            i.nombre AS item

        FROM movimientos m

        JOIN responsables r
            ON r.id = m.responsable_id

        LEFT JOIN obras o
            ON o.id = m.obra_id

        LEFT JOIN centro_de_costos c
            ON c.id = m.cc_id

        LEFT JOIN tipo_movimientos t
            ON t.id = m.tipo_id

        LEFT JOIN items i
            ON i.id = m.item_id

        WHERE 1=1
    """

    params = []

    if responsable_id:
        sql += " AND m.responsable_id = ?"
        params.append(responsable_id)

    if obra_id:
        sql += " AND m.obra_id = ?"
        params.append(obra_id)

    if fecha_ini:
        sql += " AND m.fecha_movimiento >= ?"
        params.append(fecha_ini)

    if fecha_fin:
        sql += " AND m.fecha_movimiento <= ?"
        params.append(fecha_fin)

    sql += """
        ORDER BY
            m.fecha_movimiento,
            m.id
    """

    with conectar() as conn:
        return [
            dict(r)
            for r in conn.execute(sql, params)
        ]

def resumen_por_item(responsable_id=None, obra_id=None, tipo=None,
                     fecha_ini=None, fecha_fin=None):
    """Suma de montos agrupada por ítem."""
    sql = """
        SELECT
            COALESCE(i.nombre, 'SIN ÍTEM') AS item,
            SUM(m.monto) AS total
        FROM movimientos m
        LEFT JOIN items            i ON i.id = m.item_id
        JOIN tipo_movimientos t ON t.id = m.tipo_id
        WHERE 1=1
    """
    params = []
    if responsable_id:
        sql += " AND m.responsable_id = ?"
        params.append(responsable_id)
    if obra_id:
        sql += " AND m.obra_id = ?"
        params.append(obra_id)
    if tipo:
        sql += " AND upper(t.texto) = ?"
        params.append(tipo.upper())
    if fecha_ini:
        sql += " AND m.fecha_movimiento >= ?"
        params.append(fecha_ini)
    if fecha_fin:
        sql += " AND m.fecha_movimiento <= ?"
        params.append(fecha_fin)
    sql += " GROUP BY item ORDER BY item"

    with conectar() as conn:
        return [dict(r) for r in conn.execute(sql, params)]


def resumen_por_centro_costos(responsable_id=None, obra_id=None,
                              fecha_ini=None, fecha_fin=None):
    sql = """
        SELECT
            COALESCE(c.contrato, 'SIN CENTRO') AS centro_costos,
            SUM(m.monto) AS total
        FROM movimientos m
        LEFT JOIN centro_de_costos c ON c.id = m.cc_id
        WHERE 1=1
    """
    params = []
    if responsable_id:
        sql += " AND m.responsable_id = ?"
        params.append(responsable_id)
    if obra_id:
        sql += " AND m.obra_id = ?"
        params.append(obra_id)
    if fecha_ini:
        sql += " AND m.fecha_movimiento >= ?"
        params.append(fecha_ini)
    if fecha_fin:
        sql += " AND m.fecha_movimiento <= ?"
        params.append(fecha_fin)
    sql += " GROUP BY centro_costos ORDER BY centro_costos"

    with conectar() as conn:
        return [dict(r) for r in conn.execute(sql, params)]


def registrar_unidad_ejecutada(movimiento_id, unidad_constructiva_id, cantidad,
                               observacion=None, fecha=None, usuario=None):
    fecha = fecha or ""
    with conectar() as conn:
        cur = conn.execute("""
            INSERT INTO unidades_ejecutadas
                (movimiento_id, unidad_constructiva_id, cantidad, observacion,
                 fecha, usuario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            movimiento_id, unidad_constructiva_id, cantidad, observacion,
            fecha, usuario,
        ))
        return cur.lastrowid


def consultar_unidades_ejecutadas(movimiento_id=None, responsable_id=None,
                                  obra_id=None, fecha_ini=None, fecha_fin=None):
    sql = """
        SELECT
            ue.id,
            ue.movimiento_id,
            m.recibo,
            m.fecha_movimiento,
            ue.fecha,
            r.nombre AS responsable,
            o.nombre AS obra,
            c.contrato AS cc,
            uc.nombre AS unidad_constructiva,
            ue.cantidad,
            ue.observacion,
            ue.usuario
        FROM unidades_ejecutadas ue
        JOIN movimientos m ON m.id = ue.movimiento_id
        JOIN responsables r ON r.id = m.responsable_id
        LEFT JOIN obras o ON o.id = m.obra_id
        LEFT JOIN centro_de_costos c ON c.id = m.cc_id
        JOIN unidades_constructivas uc ON uc.id = ue.unidad_constructiva_id
        WHERE 1=1
    """
    params = []
    if movimiento_id:
        sql += " AND ue.movimiento_id = ?"
        params.append(movimiento_id)
    if responsable_id:
        sql += " AND m.responsable_id = ?"
        params.append(responsable_id)
    if obra_id:
        sql += " AND m.obra_id = ?"
        params.append(obra_id)
    if fecha_ini:
        sql += " AND ue.fecha >= ?"
        params.append(fecha_ini)
    if fecha_fin:
        sql += " AND ue.fecha <= ?"
        params.append(fecha_fin)
    sql += " ORDER BY ue.fecha, ue.id"

    with conectar() as conn:
        return [dict(r) for r in conn.execute(sql, params)]



def calcular_costos_unitarios(
        responsable_id=None,
        obra_id=None,
        fecha_ini=None,
        fecha_fin=None):

    registros = consultar_unidades_ejecutadas(
        responsable_id=responsable_id,
        obra_id=obra_id,
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
    )

    # -----------------------------------------
    # AGRUPAR PRODUCCION POR FECHA
    # -----------------------------------------

    produccion_por_fecha = {}

    for r in registros:

        fecha = r["fecha"]

        if fecha not in produccion_por_fecha:

            produccion_por_fecha[fecha] = {
                "cantidad_total": 0,
                "registros": []
            }

        produccion_por_fecha[fecha]["cantidad_total"] += (
            r["cantidad"] or 0
        )

        produccion_por_fecha[fecha]["registros"].append(r)

    # -----------------------------------------
    # CONSULTAR MOVIMIENTOS FINANCIEROS
    # -----------------------------------------

    movimientos = consultar_movimientos_financieros(
        responsable_id=responsable_id,
        obra_id=obra_id,
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
    )

    # -----------------------------------------
    # AGRUPAR GASTOS POR FECHA
    # -----------------------------------------

    gastos_por_fecha = {}

    for m in movimientos:

        fecha = m["fecha_movimiento"]

        if not fecha:
            continue

        if fecha not in gastos_por_fecha:

            gastos_por_fecha[fecha] = {
                "gasto_total_dia": 0,
                "movimientos": []
            }

        monto = m["monto"] or 0

        gastos_por_fecha[fecha]["gasto_total_dia"] += monto

        gastos_por_fecha[fecha]["movimientos"].append(m)

    # -----------------------------------------
    # DISTRIBUCION PROPORCIONAL
    # -----------------------------------------

    resultado = {}

    for fecha, data in produccion_por_fecha.items():

        cantidad_total = data["cantidad_total"]

        if cantidad_total <= 0:
            continue

        gasto_total_dia = 0

        if fecha in gastos_por_fecha:

            gasto_total_dia = (
                gastos_por_fecha[fecha]["gasto_total_dia"]
            )

        for r in data["registros"]:

            unidad = r["unidad_constructiva"]

            cantidad = r["cantidad"] or 0

            porcentaje = cantidad / cantidad_total

            costo_distribuido = (
                gasto_total_dia * porcentaje
            )

            if unidad not in resultado:

                resultado[unidad] = {
                    "unidad_constructiva": unidad,
                    "cantidad": 0,
                    "gasto_asociado": 0,
                    "costo_unitario": 0,
                }

            resultado[unidad]["cantidad"] += cantidad

            resultado[unidad]["gasto_asociado"] += (
                costo_distribuido
            )

    # -----------------------------------------
    # COSTO UNITARIO FINAL
    # -----------------------------------------

    for unidad, data in resultado.items():

        cantidad = data["cantidad"]

        gasto = data["gasto_asociado"]

        if cantidad > 0:

            data["costo_unitario"] = (
                gasto / cantidad
            )

    return list(resultado.values())


def generar_resumen_tecnico(responsable_id=None, obra_id=None,
                            fecha_ini=None, fecha_fin=None):
    unidades = calcular_costos_unitarios(
        responsable_id=responsable_id,
        obra_id=obra_id,
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
    )
    return {
        "unidades": unidades,
        "total_unidades": sum((u["cantidad"] or 0) for u in unidades),
        "gasto_asociado": sum((u["gasto_asociado"] or 0) for u in unidades),
    }


def generar_liquidacion_tecnica(responsable_id, obra_id, cc_id,
                                fecha_ini, fecha_fin):
    return {
        "financiero": liquidacion(responsable_id, obra_id, cc_id, fecha_ini, fecha_fin),
        "tecnico": generar_resumen_tecnico(
            responsable_id=responsable_id,
            obra_id=obra_id,
            fecha_ini=fecha_ini,
            fecha_fin=fecha_fin,
        ),
        "costos_unitarios": calcular_costos_unitarios(
            responsable_id=responsable_id,
            obra_id=obra_id,
            fecha_ini=fecha_ini,
            fecha_fin=fecha_fin,
        ),
    }


def liquidacion(responsable_id, obra_id, cc_id, fecha_ini, fecha_fin):
    """
    Calcula los datos de liquidación para un responsable/obra/período.
    Retorna un dict con parcial (reembolsos del período), acumulado (gastos),
    total_asignaciones, total_reembolsos y total_ejecutado.
    """
    movs = listar_movimientos(
        responsable_id=responsable_id,
        obra_id=obra_id,
        cc_id=cc_id,
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
    )

    parcial = {}
    acumulado = {}
    total_asignaciones = 0
    total_reembolsos = 0
    total_ejecutado = 0

    for m in movs:
        tipo  = (m["tipo"] or "").upper()
        item  = (m["item"] or "VARIOS").upper()
        monto = m["monto"]

        if tipo == "ASIGNACION":
            total_asignaciones += monto
        if tipo == "REEMBOLSO":
            total_reembolsos += monto
            parcial[item] = parcial.get(item, 0) + monto
        if tipo in ("GASTO", "AJUSTE"):
            total_ejecutado += monto
            acumulado[item] = acumulado.get(item, 0) + monto

    return {
        "parcial":            parcial,
        "acumulado":          acumulado,
        "total_asignaciones": total_asignaciones,
        "total_reembolsos":   total_reembolsos,
        "total_ejecutado":    total_ejecutado,
    }
