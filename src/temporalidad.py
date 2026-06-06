import csv
from collections import defaultdict
from pathlib import Path

# ======================================================
# UTILIDADES
# ======================================================

def pesos(n):
    return f"$ {n:,.0f}"

def numero_a_letras(n):
    if n == 40000:
        return "CUARENTA MIL PESOS COP"
    return ""


# ======================================================
# LECTURA DE MOVIMIENTOS
# ======================================================

def leer_movimientos():
    ruta = Path("data/movimientos.csv")
    movimientos = []

    if not ruta.exists():
        print("❌ No existe data/movimientos.csv")
        return movimientos

    with open(ruta, newline="", encoding="utf-8-sig") as f:
        # Usamos un delimitador (,) pero si tu Excel usa (;) cámbialo aquí
        reader = csv.DictReader(f)
        
        # Limpiar espacios en los nombres de las columnas
        reader.fieldnames = [field.strip().lower() for field in reader.fieldnames]
        
        for row in reader:
            try:
                # MAPEAMOS LOS NOMBRES REALES DEL CSV A TU LÓGICA
                movimientos.append({
                    "fecha": row.get("fecha", "").strip(),
                    "responsable": row.get("responsable_nombre", "").strip().upper(),
                    # Si 'obra', 'tipo', etc. NO están en el CSV, darán error o quedarán vacíos:
                    "obra": row.get("obra", "SIN OBRA").strip(), 
                    "tipo": row.get("tipo", "GASTO").strip().upper(),
                    "item": row.get("item", "VARIOS").strip().upper(),
                    "monto": int(row.get("monto", 0)),
                    "cc": row.get("cc", "0").strip()
                })
            except Exception as e:
                print(f"⚠️ Error procesando fila: {e}")
                continue

    return movimientos


# ======================================================
# CÁLCULO DE LIQUIDACIÓN
# ======================================================

def calcular_liquidacion(movs, responsables, obra, cc, f_ini, f_fin):
    parcial = defaultdict(int)
    acumulado = defaultdict(int)

    total_asignaciones = 0
    total_reembolsos = 0
    total_ejecutado = 0

    for m in movs:
        if m["responsables"] != responsable:
            continue

        monto = m["monto"]
        fecha = m["fecha"]

        # Asignaciones
        if m["tipo"] == "ASIGNACION":
            total_asignaciones += monto

        # Reembolsos recibidos
        if m["tipo"] == "REEMBOLSO":
            total_reembolsos += monto

        # Gastos ejecutados (acumulado)
        if m["tipo"] in ("GASTO", "CRUCE"):
            total_ejecutado += monto
            acumulado[m["item"]] += monto

        # Parcial del periodo (para reembolso)
        if (
            m["tipo"] == "GASTO"
            and m["obra"] == obra
            and m["cc"] == cc
            and f_ini <= fecha <= f_fin
            and m["item"] != "CAJA MENOR"
        ):
            parcial[m["item"]] += monto

    return {
        "parcial": parcial,
        "acumulado": acumulado,
        "asignaciones": total_asignaciones,
        "reembolsos": total_reembolsos,
        "ejecutado": total_ejecutado
    }


# ======================================================
# IMPRESIÓN DEL RECIBO
# ======================================================

def imprimir_recibo(responsable, obra, cc, f_ini, f_fin, datos):
    print("\n--- RECIBO DE LIQUIDACION ---")
    print(f"RESPONSABLE: {responsable}")
    print(f"PERIODO: {f_ini} a {f_fin}")
    print("MOVIMIENTO: REEMBOLSO")
    print(f"OBRA: {obra}")
    print(f"CENTRO DE COSTOS: {cc}")
    print("--------------------------------------")

    print("RESUMEN PARCIAL DE GASTOS POR ITEMS:")
    print("--------------------------------------")
    for item, monto in datos["parcial"].items():
        print(f"{item:<15} :..........................  {pesos(monto):>12}")

    total_reembolso = sum(datos["parcial"].values())

    print()
    print(f"(=) GASTOS PARA REEMBOLSO:............  {pesos(total_reembolso):>12}")
    print(numero_a_letras(total_reembolso))
    print()
    print("--------------------------------------")
    print("ACUMULADO TOTAL DE GASTOS POR ITEMS:")
    print("--------------------------------------")
    print("PERIODO: 2026-02-01 a 2026-02-10")
    for item, monto in datos["acumulado"].items():
        print(f"{item:<15} :  	{pesos(monto):>12}")

    print("--------------------------------------")
    print("RESUMEN GENERAL  DE GASTOS POR ITEMS:")
    print("PERIODO: 2026-02-01 a 2026-02-10")
    print("-------------------------------------")
    print(f"(+) RECIBIDO EN ASIGNACIONES :.......  	{pesos(datos['asignaciones']):>12}")
    print(f"(+) RECIBIDO EN REEMBOLSO :..........  	{pesos(datos['reembolsos']):>12}")

    total_trabajador = datos["asignaciones"] + datos["reembolsos"]
    print(f"(=) ACUMULADO TOTAL TRABAJADOR:......   {pesos(total_trabajador):>12}")
    print(f"(-) EJECUTADO POR EL TRABAJADOR:.....   {pesos(datos['ejecutado']):>12}")
    print(f"(=) NETO:............................  	{pesos(total_trabajador - datos['ejecutado']):>12}")


# ======================================================
# EJECUCIÓN
# ======================================================

if __name__ == "__main__":
    movimientos = leer_movimientos()

    responsable = "HECTOR TOVAR"
    obra = "VEREDA GUADALUPANA 310345902"
    cc = "2"
    f_ini = "2026-02-05"
    f_fin = "2026-02-10"

    datos = calcular_liquidacion(
        movimientos,
        responsable,
        obra,
        cc,
        f_ini,
        f_fin
    )

    imprimir_recibo(
        responsable,
        obra,
        cc,
        f_ini,
        f_fin,
        datos
    )
