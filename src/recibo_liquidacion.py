# ======================================================
# RECIBO DE LIQUIDACION - VERSION SEGURA
# ======================================================

def imprimir_recibo():
    print("\n--- RECIBO DE LIQUIDACION ---")
    print("RESPONSABLE: HECTOR TOVAR")
    print("PERIODO: 2026-02-05 a 2026-02-10")
    print("MOVIMIENTO: REEMBOLSO")
    print("OBRA: VEREDA GUADALUPANA 310345902")
    print("CENTRO DE COSTOS: 2")
    print("--------------------------------------")

    print("RESUMEN PARCIAL DE GASTOS POR ITEMS:")
    print("--------------------------------------")
    print("MATERIALES :..........................  $     100,000")
    print("ALIMENTACION :........................  $      30,000")
    print()
    print("(=) GASTOS PARA REEMBOLSO:............  $      40,000")
    print("CUARENTA MIL PESOS COP")
    print()
    print("--------------------------------------")
    print("ACUMULADO TOTAL DE GASTOS POR ITEMS:")
    print("--------------------------------------")
    print("PERIODO: 2026-02-01 a 2026-02-10")
    print("MATERIALES :  	$     150,000")
    print("ALIMENTACION :  $      80,000")
    print("--------------------------------------")
    print("RESUMEN GENERAL  DE GASTOS POR ITEMS:")
    print("PERIODO: 2026-02-01 a 2026-02-10")
    print("-------------------------------------")
    print("(+) RECIBIDO EN ASIGNACIONES :.......  	$     500,000")
    print("(+) RECIBIDO EN REEMBOLSO :..........  	$      40,000")
    print("(=) ACUMULADO TOTAL TRABAJADOR:......   $     540,000")
    print("(-) EJECUTADO POR EL TRABAJADOR:.....   $     230,000")
    print("(=) NETO:............................  	$     210,000")


if __name__ == "__main__":
    imprimir_recibo()
