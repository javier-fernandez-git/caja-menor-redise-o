"""
CAJA MENOR — Sistema financiero, técnico y operativo.

ARQUITECTURA CORREGIDA:
✔ Recupera OBRAS en launcher
✔ Separa UNIDADES CONSTRUCTIVAS como módulo independiente
✔ Mantiene ITEMS financieros
✔ Mantiene CENTROS DE COSTOS
✔ Permite trazabilidad técnico-financiera
✔ Corrige menú desalineado
✔ Prepara integración PDF profesional

Ejecutar:
    python src/app.py
"""

import sys
from datetime import date, datetime
from pathlib import Path

# -------------------------------------------------------
# UTF-8 WINDOWS
# -------------------------------------------------------

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

import db


# -------------------------------------------------------
# UTILIDADES
# -------------------------------------------------------

def pesos(n):
    return f"$ {n:,.0f}"


def sep(car="-", ancho=70):
    print(car * ancho)


def encabezado(titulo):
    print()
    sep("=")
    print(f"  {titulo}")
    sep("=")


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------

def elegir_de_lista(lista, clave_texto, titulo):

    print(f"\n  ── {titulo} ──")

    for i, item in enumerate(lista, 1):
        print(f"    {i:2}. {item[clave_texto]}")

    print("     0. Cancelar")

    while True:

        op = input(f"  Opción (0-{len(lista)}): ").strip()

        if op == "0":
            return None

        if op.isdigit() and 1 <= int(op) <= len(lista):
            return lista[int(op) - 1]

        print("  ⚠ Opción inválida")


def pedir_fecha(mensaje, default=None):

    sufijo = f" [{default}]" if default else ""

    while True:

        f = input(f"  {mensaje}{sufijo}: ").strip()

        if f == "":
            return default

        if f.upper() == "X":
            return None

        try:
            datetime.strptime(f, "%Y-%m-%d")
            return f

        except ValueError:
            print("  ⚠ Use formato AAAA-MM-DD")


def pedir_monto(mensaje):

    while True:

        valor = input(f"  {mensaje}: ").strip().replace(",", "")

        if valor.upper() == "X":
            return None

        if valor.isdigit() and int(valor) > 0:
            return int(valor)

        print("  ⚠ Valor inválido")


def pedir_cantidad(mensaje):

    while True:

        valor = input(f"  {mensaje}: ").strip().replace(",", ".")

        if valor.upper() == "X":
            return None

        try:
            cantidad = float(valor)

            if cantidad > 0:
                return cantidad

        except:
            pass

        print("  ⚠ Cantidad inválida")


# -------------------------------------------------------
# ASOCIAR UNIDAD A MOVIMIENTO
# -------------------------------------------------------

def asociar_unidad_a_movimiento(movs):

    seleccion = input(
        f"\n  Movimiento a relacionar (1-{len(movs)}): "
    ).strip()

    if not seleccion.isdigit():
        print("  ⚠ Movimiento inválido")
        return

    indice = int(seleccion)

    if indice < 1 or indice > len(movs):
        print("  ⚠ Movimiento fuera de rango")
        return

    movimiento = movs[indice - 1]

    unidades = db.obtener_unidades_constructivas()

    unidad = elegir_de_lista(
        unidades,
        "nombre",
        "UNIDAD CONSTRUCTIVA"
    )

    if not unidad:
        return

    cantidad = pedir_cantidad(
        "Cantidad ejecutada"
    )

    if cantidad is None:
        return

    observacion = input(
        "  Observación técnica: "
    ).strip()

    fecha = pedir_fecha(
        "Fecha ejecución",
        default=date.today().isoformat()
    )

    usuario = input(
        "  Usuario responsable: "
    ).strip()

    if not usuario:
        usuario = movimiento["responsable"]

    db.registrar_unidad_ejecutada(
        movimiento_id=movimiento["id"],
        unidad_constructiva_id=unidad["id"],
        cantidad=cantidad,
        observacion=observacion,
        fecha=fecha,
        usuario=usuario,
    )

    print()
    sep()

    print("  ✔ Unidad constructiva registrada")
    print(f"     Unidad   : {unidad['nombre']}")
    print(f"     Cantidad : {cantidad}")

    sep()

# -------------------------------------------------------
# REGISTRAR MOVIMIENTO
# -------------------------------------------------------

def registrar_movimiento():

    encabezado("REGISTRAR MOVIMIENTO")

    responsables = db.obtener_responsables()

    responsable = elegir_de_lista(
        responsables,
        "nombre",
        "RESPONSABLE"
    )

    if not responsable:
        return

    tipos = db.obtener_tipos_movimiento()

    tipo = elegir_de_lista(
        tipos,
        "texto",
        "TIPO DE MOVIMIENTO"
    )

    if not tipo:
        return

    centros = db.obtener_centros_de_costos()

    cc = elegir_de_lista(
        centros,
        "contrato",
        "CENTRO DE COSTOS"
    )

    if not cc:
        return

    items = db.obtener_items()

    item = elegir_de_lista(
        items,
        "nombre",
        "ITEM / CONCEPTO"
    )

    if not item:
        return

    monto = pedir_monto(
        "Monto ($)"
    )

    if monto is None:
        return

    observacion = input(
        "  Observación: "
    ).strip()

    soporte = input(
        "  Soporte: "
    ).strip()

    fecha = pedir_fecha(
        "Fecha movimiento",
        default=date.today().isoformat()
    )

    db.registrar_movimiento(
        responsable_id=responsable["id"],
        obra_id=obra["id"],
        tipo_id=tipo["id"],
        item_id=item["id"],
        monto=monto,
        cc_id=cc["id"],
        observacion=observacion,
        soporte=soporte,
        fecha=fecha,
    )

    print()

    sep("=")

    print("  ✔ Movimiento registrado exitosamente")

    print(f"     Recibo : {recibo}")
    print(f"     Monto  : {pesos(monto)}")

    sep("=")

# -------------------------------------------------------
# VER MOVIMIENTOS
# -------------------------------------------------------

def ver_movimientos():

    encabezado("MOVIMIENTOS")

    movs = db.listar_movimientos()

    if not movs:
        print("\n  (sin movimientos)")
        return

    fmt = "{:<4} {:<7} {:<10} {:<16} {:<18} {:>12}"

    print()

    print(fmt.format(
        "#",
        "RECIBO",
        "FECHA",
        "RESPONSABLE",
        "ITEM",
        "MONTO"
    ))

    sep()

    for idx, m in enumerate(movs, 1):

        print(fmt.format(
            idx,
            m["recibo"],
            m["fecha_movimiento"],
            (m["responsable"] or "")[:16],
            (m["item"] or "")[:18],
            pesos(m["monto"])
        ))

        # -----------------------------------------
        # PRODUCCION ASOCIADA
        # -----------------------------------------

        unidades = db.consultar_unidades_ejecutadas(
            movimiento_id=m["id"]
        )

        print()
        print("     PRODUCCION ASOCIADA")

        if not unidades:

            print("        (sin unidades ejecutadas)")

        else:

            for u in unidades:

                print(
                    f"        - {u['unidad_constructiva']} "
                    f"→ {u['cantidad']:,.2f}"
                )

                if u["observacion"]:

                    print(
                        f"          Obs: "
                        f"{u['observacion']}"
                    )

        print()

    sep()

    print("\n  A. Asociar unidad ejecutada")
    print("  ENTER. Volver")

    accion = input(
        "\n  Opción: "
    ).strip().upper()

    if accion == "A":

        asociar_unidad_a_movimiento(movs)


# -------------------------------------------------------
# OPCION 4
# VER RESUMEN
# -------------------------------------------------------

def ver_resumen():

    encabezado("RESUMEN FINANCIERO Y TECNICO")

    resumen = db.resumen_por_item()

    total = 0

    for r in resumen:

        print(
            f"  {r['item']:<30} "
            f"{pesos(r['total'])}"
        )

        total += r["total"]

    sep()

    print(f"  TOTAL: {pesos(total)}")

    tecnico = db.generar_resumen_tecnico()

    print()
    sep()

    print("  UNIDADES CONSTRUCTIVAS")

    sep()

    print()
    print("=" * 70)
    print("UNIDAD CONSTRUCTIVA")
    print("=" * 70)

    print(
        f"{'UNIDAD':<30}"
        f"{'CANTIDAD':>12}"
        f"{'GASTO':>15}"
        f"{'COSTO/U':>12}"
    )

    print("-" * 70)

    for fila in tecnico["unidades"]:

        print(
            f"{fila['unidad_constructiva']:<30}"
            f"{fila['cantidad']:>12.2f}"
            f"{fila['gasto_asociado']:>15,.0f}"
            f"{fila['costo_unitario']:>12,.0f}"
        )

    print("-" * 70)


# -------------------------------------------------------
# OPCION 5
# LIQUIDACION
# -------------------------------------------------------

def generar_liquidacion():

    encabezado("LIQUIDACION")

    responsables = db.obtener_responsables()

    resp = elegir_de_lista(
        responsables,
        "nombre",
        "RESPONSABLE"
    )

    if not resp:
        return

    obras = db.obtener_obras()

    obra = elegir_de_lista(
        obras,
        "nombre",
        "OBRA"
    )

    if not obra:
        return

    centros = db.obtener_centros_de_costos()

    cc = elegir_de_lista(
        centros,
        "contrato",
        "CENTRO COSTOS"
    )

    if not cc:
        return

    fecha_ini = pedir_fecha("Fecha inicio")
    fecha_fin = pedir_fecha("Fecha fin")

    datos = db.liquidacion(
        responsable_id=resp["id"],
        obra_id=obra["id"],
        cc_id=cc["id"],
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
    )

    print()
    sep("=")

    print("   RECIBO DE LIQUIDACION")

    sep("=")

    print(f"  RESPONSABLE : {resp['nombre']}")
    print(f"  OBRA        : {obra['nombre']}")
    print(f"  CENTRO      : {cc['contrato']}")

    sep()

    total = 0

    for item, monto in datos["parcial"].items():

        print(f"  {item:<28} {pesos(monto):>14}")

        total += monto

    sep()

    print(f"  TOTAL REEMBOLSO : {pesos(total)}")

    sep()

    print("\n  ✔ Próxima fase:")
    print("     PDF corporativo")
    print("     Logo empresarial")
    print("     Firma responsable")
    print("     Firma supervisor")
    print("     Código QR")
    print("     Consecutivo PDF")

    sep()


# -------------------------------------------------------
# OPCION 6
# CATALOGOS
# -------------------------------------------------------

def administrar_catalogos():

    encabezado("CATALOGOS")

    print("  1. Responsable")
    print("  2. Obras")
    print("  3. Items")
    print("  4. Unidades constructivas")
    print("  0. Volver")

    op = input("  Opción: ").strip()

    with db.conectar() as conn:

        if op == "1":

            nombre = input(
                "  Responsable: "
            ).strip().upper()

            conn.execute(
                "INSERT OR IGNORE INTO responsables(nombre) VALUES (?)",
                (nombre,)
            )

        elif op == "2":

            nombre = input(
                "  Obra: "
            ).strip().upper()

            conn.execute(
                "INSERT OR IGNORE INTO obras(nombre) VALUES (?)",
                (nombre,)
            )

        elif op == "3":

            nombre = input(
                "  Item: "
            ).strip().upper()

            conn.execute(
                "INSERT OR IGNORE INTO items(nombre) VALUES (?)",
                (nombre,)
            )

        elif op == "4":

            nombre = input(
                "  Unidad constructiva: "
            ).strip().upper()

            conn.execute(
                """
                INSERT OR IGNORE INTO
                unidades_constructivas(nombre)
                VALUES (?)
                """,
                (nombre,)
            )

    print("\n  ✔ Catálogo actualizado")


# -------------------------------------------------------
# MENU
# -------------------------------------------------------

def menu():

    db.inicializar()

    while True:

        ultimo = db.obtener_ultimo_consecutivo()

        print("\n" + "=" * 50)

        print("      SISTEMA DE CAJA MENOR")

        print(f"      Consecutivo actual: #{ultimo}")

        print("=" * 50)

        print("  1. Registrar movimiento")
        print("  2. Ver movimientos")
        print("  3. Ver resumen")
        print("  4. Generar liquidación")
        print("  5. Catálogos")
        print("  0. Salir")

        sep("-", 50)

        op = input("  Opción: ").strip()

        if op == "1":

            registrar_movimiento()

        elif op == "2":

            ver_movimientos()

        elif op == "3":

            ver_resumen()

        elif op == "4":

            generar_liquidacion()

        elif op == "5":

            administrar_catalogos()

        elif op == "0":

            print("\n  Hasta luego.\n")

            break

        else:

            print("  ⚠ Opción inválida")


# -------------------------------------------------------

if __name__ == "__main__":
    menu()