import csv
from collections import defaultdict

# ----------------------------
# 1. Leer movimientos
# ----------------------------
resumen = defaultdict(int)

with open('data/movimientos.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        item = row['item']
        total = int(row['total'])
        resumen[item] += total

# ----------------------------
# 2. Mostrar resumen
# ----------------------------
print("\n=== RESUMEN POR ÍTEM ===\n")

gran_total = 0

for item, total in resumen.items():
    print(f"{item:20} $ {total:,.0f}")
    gran_total += total

print("\n----------------------------")
print(f"{'TOTAL GENERAL':20} $ {gran_total:,.0f}")
