"""
Migración única de datos CSV → SQLite.

Ejecutar desde la raíz del proyecto:
    python src/migrate.py

Si la base de datos ya tiene datos, los registros duplicados se omiten
de forma segura (INSERT OR IGNORE).
"""
import csv
import sys
from pathlib import Path

# Forzar UTF-8 en la terminal de Windows (cmd/PowerShell)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Permitir importar db.py desde src/
sys.path.insert(0, str(Path(__file__).parent))
import db

DATA_DIR = Path(__file__).parent.parent / "data"


def cargar_csv(nombre, encoding="utf-8-sig"):
    ruta = DATA_DIR / nombre
    if not ruta.exists():
        print(f"  [!] No encontrado: {ruta}")
        return []
    with open(ruta, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f)
        # Limpiar nombres de columna (quitar puntos y espacios finales)
        reader.fieldnames = [
            c.strip().rstrip(".").strip() for c in (reader.fieldnames or [])
        ]
        return list(reader)


def limpiar(valor):
    return (valor or "").strip()


def migrar():
    print("=" * 50)
    print("  MIGRACION CSV -> SQLite")
    print("=" * 50)

    db.inicializar()

    with db.conectar() as conn:

        # ── responsables ──────────────────────────────────
        filas = cargar_csv("responsables.csv")
        for r in filas:
            nombre = limpiar(r.get("nombre", "")).upper()
            if nombre:
                conn.execute(
                    "INSERT OR IGNORE INTO responsables (nombre) VALUES (?)",
                    (nombre,)
                )
        print(f"  OK  Responsables     : {len(filas)}")

        # ── obras ─────────────────────────────────────────
        filas = cargar_csv("obras.csv")
        for r in filas:
            nombre = limpiar(r.get("obra", "")).upper()
            if nombre:
                conn.execute(
                    "INSERT OR IGNORE INTO obras (nombre) VALUES (?)",
                    (nombre,)
                )
        print(f"  OK  Obras            : {len(filas)}")

        # ── centro_de_costos ──────────────────────────────
        filas = cargar_csv("centro_de_costos.csv")
        for r in filas:
            contrato = limpiar(r.get("contrato", "")).upper()
            if contrato:
                conn.execute(
                    "INSERT OR IGNORE INTO centro_de_costos (contrato) VALUES (?)",
                    (contrato,)
                )
        print(f"  OK  Centros de costo : {len(filas)}")

        # ── tipo_movimientos ──────────────────────────────
        # Combina lo que está en el CSV con los tipos que aparecen en los datos
        filas = cargar_csv("tipo_de_movimientos.csv")
        tipos = {limpiar(r.get("texto", "")).upper() for r in filas if r.get("texto")}
        tipos.update({"ASIGNACION", "GASTO", "AJUSTE", "REEMBOLSO"})
        for texto in sorted(tipos):
            if texto:
                conn.execute(
                    "INSERT OR IGNORE INTO tipo_movimientos (texto) VALUES (?)",
                    (texto,)
                )
        print(f"  OK  Tipos movimiento : {len(tipos)}")

        # ── items (descripciones) ─────────────────────────
        filas = cargar_csv("descripciones.csv")
        for r in filas:
            nombre = limpiar(r.get("item", "")).upper()
            if nombre:
                conn.execute(
                    "INSERT OR IGNORE INTO items (nombre) VALUES (?)",
                    (nombre,)
                )
        print(f"  OK  Items            : {len(filas)}")

        # ── unidades_constructivas ────────────────────────
        filas = cargar_csv("unidades_constructivas.csv")
        for r in filas:
            unidad = limpiar(r.get("unidad", ""))
            if unidad:
                conn.execute(
                    "INSERT OR IGNORE INTO unidades_constructivas (nombre) VALUES (?)",
                    (unidad.upper(),)
                )
        print(f"  OK  Unidades const.  : {len(filas)}")

        # ── helpers de lookup con auto-insert ────────────
        def get_or_create(tabla, campo, valor):
            """Busca por valor (case-insensitive) o inserta si no existe."""
            v = limpiar(valor).upper()
            if not v:
                return None
            row = conn.execute(
                f"SELECT id FROM {tabla} WHERE upper({campo}) = ?", (v,)
            ).fetchone()
            if row:
                return row[0]
            conn.execute(
                f"INSERT OR IGNORE INTO {tabla} ({campo}) VALUES (?)", (v,)
            )
            row = conn.execute(
                f"SELECT id FROM {tabla} WHERE upper({campo}) = ?", (v,)
            ).fetchone()
            return row[0] if row else None

        def resolver_cc(valor):
            """
            El campo cc en el CSV puede ser un id numérico ("2") o texto
            ("OBRA CIVIL"). Ambos se normalizan al id correcto.
            """
            v = limpiar(valor)
            if not v:
                return None
            if v.isdigit():
                row = conn.execute(
                    "SELECT id FROM centro_de_costos WHERE id = ?", (int(v),)
                ).fetchone()
                return row[0] if row else None
            return get_or_create("centro_de_costos", "contrato", v)

        # ── movimientos ───────────────────────────────────
        filas = cargar_csv("movimientos.csv")
        ok = 0
        errores = 0

        for r in filas:
            try:
                recibo_str = limpiar(r.get("recibo", "0"))
                recibo     = int(recibo_str) if recibo_str.isdigit() else 0
                fecha_movimiento = limpiar(r.get("fecha_movimiento", "")) or limpiar(r.get("fecha_ini", ""))
                resp_nom   = limpiar(r.get("resp", "")).upper()
                obra_nom   = limpiar(r.get("obra", "")).upper()
                tipo_txt   = limpiar(r.get("tipo", "")).upper()
                item_nom   = limpiar(r.get("item", "")).upper()
                monto_str  = limpiar(r.get("monto", "0")).replace(",", "")
                cc_raw     = limpiar(r.get("cc", ""))

                monto = int(monto_str) if monto_str.isdigit() else 0

                if not (recibo and fecha_movimiento and obra_nom and resp_nom and tipo_txt):
                    errores += 1
                    continue

                responsable_id = get_or_create("responsables", "nombre", resp_nom)
                obra_id        = get_or_create("obras", "nombre", obra_nom)
                tipo_id        = get_or_create("tipo_movimientos", "texto", tipo_txt)
                item_id        = get_or_create("items", "nombre", item_nom) if item_nom else None
                cc_id          = resolver_cc(cc_raw)

                conn.execute("""
                    INSERT INTO movimientos
                        (recibo, fecha_movimiento, responsable_id, obra_id,
                         tipo_id, item_id, monto, cc_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (recibo, fecha_movimiento, responsable_id, obra_id,
                      tipo_id, item_id, monto, cc_id))
                ok += 1

            except Exception as e:
                print(f"  [!] Error en fila {r}: {e}")
                errores += 1

        print(f"  OK  Movimientos      : {ok} migrados, {errores} omitidos")

        # ── consecutivo ───────────────────────────────────
        try:
            txt = (DATA_DIR / "consecutivo.txt").read_text(encoding="utf-8").strip()
            ultimo = int(txt) if txt.isdigit() else 1000
        except Exception:
            ultimo = 1000
        conn.execute(
            "INSERT OR REPLACE INTO consecutivo (id, ultimo) VALUES (1, ?)",
            (ultimo,)
        )
        print(f"  OK  Consecutivo      : {ultimo}")

    print()
    print(f"  OK  Base de datos lista -> {db.DB_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    migrar()
