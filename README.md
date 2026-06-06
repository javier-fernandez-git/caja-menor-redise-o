# Sistema de Caja Menor

Sistema de consola en Python para registrar y liquidar movimientos de caja menor por obra, responsable y centro de costos. Usa SQLite como base de datos.

---

## ¿Qué hace la aplicación?

- **Registrar movimientos**: asignaciones, gastos, reembolsos y ajustes por responsable, obra, ítem y centro de costos.
- **Consultar movimientos**: ver el historial filtrando por responsable.
- **Resumen por ítem**: totales acumulados agrupados por categoría de gasto.
- **Liquidación**: genera un recibo de liquidación con el parcial de reembolsos del período, el acumulado de gastos y el neto final del trabajador.
- **Administrar catálogos**: agregar responsables, obras e ítems directamente desde el menú.

---

## Estructura del proyecto

```
.
├── data/
│   ├── caja_menor.db           ← Base de datos SQLite (generada por migrate.py)
│   ├── movimientos.csv         ← Datos históricos (fuente de migración)
│   ├── responsables.csv
│   ├── obras.csv
│   ├── descripciones.csv
│   ├── centro_de_costos.csv
│   ├── tipo_de_movimientos.csv
│   ├── unidades_constructivas.csv
│   └── consecutivo.txt
├── src/
│   ├── db.py                   ← Conexión, esquema y consultas SQLite
│   ├── migrate.py              ← Migración única CSV → SQLite
│   └── app.py                  ← Aplicación principal (menú de consola)
├── recibos_pdf/                ← PDFs generados (si aplica)
├── recibos_imprimibles/        ← Recibos en texto
└── README.md
```

---

## Esquema de la base de datos

| Tabla                    | Descripción                                      |
|--------------------------|--------------------------------------------------|
| `responsables`           | Trabajadores que manejan caja menor              |
| `obras`                  | Proyectos u obras de construcción                |
| `centro_de_costos`       | Clasificación del contrato (INTERNAS, OBRA CIVIL…) |
| `tipo_movimientos`       | ASIGNACION, GASTO, REEMBOLSO, AJUSTE             |
| `items`                  | Categorías de gasto (MATERIALES, ALIMENTACION…)  |
| `unidades_constructivas` | Unidades de medida para obras civiles            |
| `movimientos`            | Tabla principal con todos los registros          |
| `consecutivo`            | Número del último recibo emitido                 |

---

## Requisitos

- Python 3.10 o superior (incluido con la instalación estándar de Python)
- No requiere librerías externas — solo la librería estándar de Python (`sqlite3`, `csv`, `pathlib`, `datetime`)

---

## Instalación y primer uso

### 1. Clonar o descargar el proyecto

```bash
git clone <url-del-repositorio>
cd 2026.04.11-caja-menor-actualizada
```

### 2. Migrar los datos históricos (solo la primera vez)

Este comando lee los archivos CSV en `data/` y crea la base de datos SQLite:

```bash
python src/migrate.py
```

Verá una salida similar a:

```
==================================================
  MIGRACION CSV -> SQLite
==================================================
  OK  Responsables     : 9
  OK  Obras            : 15
  ...
  OK  Movimientos      : 136 migrados, 0 omitidos
  OK  Consecutivo      : 1212

  OK  Base de datos lista -> data/caja_menor.db
==================================================
```

> Si ejecuta `migrate.py` nuevamente, los registros duplicados se omiten de forma segura. No hay riesgo de duplicar datos.

### 3. Ejecutar la aplicación

```bash
python src/app.py
```

---

## Guía completa de uso

### Cómo iniciar la aplicación

Abra una terminal en la carpeta raíz del proyecto y ejecute:

```bash
python src/app.py
```

Verá el menú principal:

```
==========================================
       SISTEMA DE CAJA MENOR
       Consecutivo actual: #1212
==========================================
  1. Registrar movimiento
  2. Ver movimientos
  3. Ver resumen por item
  4. Generar liquidacion
  5. Administrar catalogos
  0. Salir
------------------------------------------
  Opcion:
```

> **Nota:** en cualquier paso puede escribir `X` y presionar Enter para cancelar y volver al menú principal.

---

### Opción 1 — Registrar movimiento

Registra un nuevo movimiento de caja: asignación de dinero, gasto, reembolso o ajuste.

**Pasos:**

**Paso 1 — Seleccione el responsable**

```
  -- RESPONSABLE --
     1. ALFREDO SAADE
     2. AMIN GAMARRA
     3. CIBETH PERTUZ
     4. EDER AVILA
     5. HECTOR TOVAR
     ...
     0. Cancelar
  Opcion (0-9): 2
```

Escriba el número del responsable y presione Enter. En este ejemplo se elige `2` para AMIN GAMARRA.

**Paso 2 — Seleccione la obra**

```
  -- OBRA --
     1. ALEJANDRIA OT 388884384
     2. ALTOS DE 20 DE OCTUBRE OT 386194281
     3. CORALINA CARIBE OT 375505681
     4. CORALINA DEL SOL OT 373454376
     5. FUNDACION OT 2388968797
     6. GRAN VIA OT 388175823
     7. GUAMAL OT 385865401
     8. LABERINTO MACONDO OT 390545173
     9. LAS ACACIAS OT 385868802
    10. LIBANO 2000 OT 373460551
     ...
     0. Cancelar
  Opcion (0-15): 10
```

**Paso 3 — Seleccione el tipo de movimiento**

```
  -- TIPO DE MOVIMIENTO --
     1. AJUSTE
     2. ASIGNACION
     3. GASTO
     4. REEMBOLSO
     0. Cancelar
  Opcion (0-4): 4
```

| Tipo        | Cuándo usarlo                                              |
|-------------|-------------------------------------------------------------|
| ASIGNACION  | Se le entrega dinero al trabajador para la obra             |
| GASTO       | El trabajador registra un gasto realizado                   |
| REEMBOLSO   | Se le devuelve dinero al trabajador por gastos comprobados  |
| AJUSTE      | Corrección de un monto ya registrado                        |

**Paso 4 — Seleccione el ítem**

```
  -- ITEM --
     1. AGUA PARA PERFILACION
     2. AGUA Y HIELO
     3. ALIMENTACION
     4. CAJA MENOR
     5. GASTOS MENORES
     6. MATERIALES
     7. PAGO DE ARRIENDO
     8. PAGO DE BODEGAJE
     9. PAGO DE MANO DE OBRA
    10. PEAJES ARACATACA
    11. PEAJES COPEY
    12. PEAJES DIFICIL
    13. PEAJES TUCURINCA
    14. PEAJES ZONA TURISTICA
     0. Cancelar
  Opcion (0-14): 6
```

**Paso 5 — Seleccione el centro de costos**

```
  -- CENTRO DE COSTOS --
     1. INTERNAS
     2. MANTENIMIENTO
     3. OBRA CIVIL
     0. Cancelar
  Opcion (0-3): 3
```

**Paso 6 — Ingrese las fechas del período**

```
  Fecha inicio (AAAA-MM-DD) [2026-04-11]: 2026-04-10
  Fecha fin    (AAAA-MM-DD) [2026-04-11]: 2026-04-11
```

Presione Enter sin escribir nada para usar la fecha de hoy como valor predeterminado.

**Paso 7 — Ingrese el monto**

```
  Monto ($) (X=cancelar): 350000
```

**Resultado:**

```
--------------------------------------------------------------
  >> Recibo #1213 registrado exitosamente
     Responsable : AMIN GAMARRA
     Obra        : LIBANO 2000 OT 373460551
     Tipo        : REEMBOLSO
     Item        : MATERIALES
     Monto       : $ 350,000
     Periodo     : 2026-04-10 -> 2026-04-11
--------------------------------------------------------------
```

El número de recibo se asigna automáticamente y aumenta de forma consecutiva con cada registro.

---

### Opción 2 — Ver movimientos

Muestra el historial de todos los movimientos registrados en la base de datos.

**Pasos:**

1. Al seleccionar la opción `2`, el sistema pregunta por un filtro de responsable:

```
  Filtrar por responsable (Enter = todos):
     1. ALFREDO SAADE
     2. AMIN GAMARRA
     3. CIBETH PERTUZ
     ...
  Opcion:
```

2. Escriba el número del responsable para filtrar, o presione **Enter** para ver todos.

**Ejemplo de salida (filtrado por AMIN GAMARRA):**

```
--------------------------------------------------------------
RECIBO F.INI       F.FIN       RESPONSABLE        TIPO        ITEM                  MONTO
--------------------------------------------------------------
1121   2026-02-25  2026-02-26  AMIN GAMARRA       REEMBOLSO   MATERIALES         $ 50,000
1123   2026-02-26  2026-02-27  AMIN GAMARRA       REEMBOLSO   GASTOS MENORES    $ 500,000
1123   2026-02-26  2026-02-27  AMIN GAMARRA       REEMBOLSO   AGUA Y HIELO       $ 67,000
1126   2026-03-10  2026-03-15  AMIN GAMARRA       ASIGNACION  ALIMENTACION       $ 50,000
...
--------------------------------------------------------------
                                                    TOTAL    $ 58,603,043
```

---

### Opción 3 — Ver resumen por ítem

Muestra los totales acumulados agrupados por categoría de gasto.

**Pasos:**

1. El sistema pregunta por un filtro de responsable (igual que en la opción 2). Presione **Enter** para ver el resumen global.

2. Luego pregunta por el tipo de movimiento:

```
  Filtrar por tipo (Enter = todos):
     1. AJUSTE
     2. ASIGNACION
     3. GASTO
     4. REEMBOLSO
  Opcion:
```

Presione **Enter** para incluir todos los tipos.

**Ejemplo de salida:**

```
--------------------------------------------------------------
  ITEM                           TOTAL
--------------------------------------------------------------
  AGUA Y HIELO                $ 212,700
  ALIMENTACION             $ 17,847,010
  ASIGNACION                  $ 740,000
  CAJA MENOR               $ 45,914,000
  GASTOS MENORES            $ 7,612,000
  MATERIALES               $ 28,427,000
  PAGO DE ARRIENDO             $ 56,777
  PEAJES ARACATACA             $ 74,700
  PEAJES COPEY                 $ 93,066
  PEAJES DIFICIL                $ 5,600
  PEAJES TUCURINCA             $ 15,500
  PEAJES ZONA TURISTICA        $ 34,761
--------------------------------------------------------------
  TOTAL GENERAL           $ 101,033,114
```

---

### Opción 4 — Generar liquidación

Genera el recibo de liquidación de caja menor para un responsable, una obra y un período de fechas.

**Pasos:**

1. **Seleccione el responsable** (mismo menú de lista numerada).
2. **Seleccione la obra**.
3. **Seleccione el centro de costos**.
4. **Ingrese la fecha de inicio del período:**

```
  Fecha inicio del periodo (X=cancelar): 2026-03-01
```

5. **Ingrese la fecha de fin del período:**

```
  Fecha fin del periodo (X=cancelar): 2026-03-31
```

**Ejemplo de recibo generado:**

```
==============================================================
           RECIBO DE LIQUIDACION -- CAJA MENOR
==============================================================
  RESPONSABLE   : AMIN GAMARRA
  OBRA          : LIBANO 2000 OT 373460551
  CENTRO COSTOS : OBRA CIVIL
  PERIODO       : 2026-03-01  a  2026-03-31
--------------------------------------------------------------
  GASTOS PARA REEMBOLSO (periodo):
--------------------------------------------------------------
  AGUA Y HIELO                        $      28,000
  ALIMENTACION                        $     766,000
  GASTOS MENORES                      $   5,280,000
  MATERIALES                          $  13,827,000
  PEAJES ARACATACA                    $      54,100
  PEAJES COPEY                        $      76,566
  PEAJES DIFICIL                      $       5,600
  PEAJES TUCURINCA                    $      15,500
  PEAJES ZONA TURISTICA               $      14,300
--------------------------------------------------------------
  (=) TOTAL REEMBOLSO                 $  20,066,066

--------------------------------------------------------------
  RESUMEN GENERAL:
--------------------------------------------------------------
  (+) ASIGNACIONES                    $  36,919,500
  (+) REEMBOLSOS RECIBIDOS            $  21,641,166
  (=) TOTAL RECIBIDO                  $  58,560,666
  (-) EJECUTADO                       $     856,700
--------------------------------------------------------------
  (=) NETO                            $  57,703,966
==============================================================
```

**Cómo leer el recibo:**

| Línea                   | Significado                                                       |
|-------------------------|-------------------------------------------------------------------|
| GASTOS PARA REEMBOLSO   | Movimientos tipo REEMBOLSO registrados en el período seleccionado |
| (+) ASIGNACIONES        | Total de dinero entregado al trabajador                           |
| (+) REEMBOLSOS RECIBIDOS| Total de reembolsos ya recibidos por el trabajador                |
| (=) TOTAL RECIBIDO      | Suma de asignaciones + reembolsos                                 |
| (-) EJECUTADO           | Total de gastos y ajustes registrados por el trabajador           |
| (=) NETO                | Diferencia: lo que el trabajador tiene disponible o debe          |

---

### Opción 5 — Administrar catálogos

Permite agregar nuevos registros a los catálogos sin editar archivos ni la base de datos directamente.

```
==========================================
       ADMINISTRAR CATALOGOS
==========================================
  1. Agregar responsable
  2. Agregar obra
  3. Agregar item
  0. Volver
  Opcion:
```

**Sub-opción 1 — Agregar responsable:**

```
  Nombre del responsable: CARLOS PEREZ
  >> Responsable 'CARLOS PEREZ' agregado
```

**Sub-opción 2 — Agregar obra:**

```
  Nombre de la obra: VILLA NUEVA OT 391234567
  >> Obra 'VILLA NUEVA OT 391234567' agregada
```

**Sub-opción 3 — Agregar ítem:**

```
  Nombre del item: COMBUSTIBLE
  >> Item 'COMBUSTIBLE' agregado
```

Los nuevos registros quedan disponibles de inmediato en el menú de registro de movimientos.

> Si intenta agregar un nombre que ya existe, el sistema lo omite sin generar error (no hay duplicados).

---

### Opción 0 — Salir

Cierra la aplicación de forma segura. Todos los datos quedan guardados en `data/caja_menor.db`.

---

## Archivos que ya no se usan (reemplazados por SQLite)

Los siguientes archivos CSV y TXT eran la fuente de datos original. Ahora son solo el origen de la migración y pueden mantenerse como respaldo histórico:

- `data/movimientos.csv`
- `data/consecutivo.txt`
- `data/responsables.csv`, `obras.csv`, `descripciones.csv`, etc.

La **única fuente de verdad** de ahora en adelante es `data/caja_menor.db`.

---

## Ideas para el siguiente paso: interfaz de usuario (UI)

A continuación, cuatro opciones ordenadas de menor a mayor complejidad, con sus ventajas para este caso de uso:

---

### Opción A — Streamlit (recomendada para un prototipo rápido)

**Tiempo estimado de implementación**: 1–2 días

Streamlit permite construir una app web interactiva escribiendo solo Python. Ideal para dashboards internos.

**Lo que se ganaría:**
- Tablas filtradas y ordenables con `st.dataframe`
- Formularios de registro con menús desplegables
- Gráficas de gastos por ítem, por responsable o por período con Plotly o Altair
- Resumen y liquidación exportable a PDF o Excel

**Instalación:**
```bash
pip install streamlit
streamlit run src/ui_streamlit.py
```

**Estructura mínima:**
```python
import streamlit as st
import sys; sys.path.insert(0, 'src')
import db

st.title("Caja Menor")
movs = db.listar_movimientos()
st.dataframe(movs)
```

---

### Opción B — FastAPI + HTMX (app web liviana y durable)

**Tiempo estimado de implementación**: 3–5 días

FastAPI expone endpoints REST y HTMX actualiza partes de la página sin recargarla. Sin frameworks JavaScript.

**Lo que se ganaría:**
- Formularios HTML clásicos que actualizan la página parcialmente
- Rutas como `GET /movimientos`, `POST /movimientos/nuevo`
- Fácil de desplegar en un servidor interno con `uvicorn`
- Puede crecer a una API completa

**Instalación:**
```bash
pip install fastapi uvicorn jinja2
```

---

### Opción C — Django (panel de administración automático)

**Tiempo estimado de implementación**: 4–6 días (solo el admin)

Django incluye un panel de administración que genera CRUD automático a partir de los modelos. Con los modelos definidos, el admin ya permite crear, editar y eliminar registros.

**Lo que se ganaría:**
- Admin panel listo para usar (`/admin`)
- Autenticación de usuarios incluida
- ORM robusto compatible con SQLite (y migración a PostgreSQL si escala)
- Ideal si el sistema va a crecer con más módulos

**Instalación:**
```bash
pip install django
```

---

### Opción D — Tkinter (escritorio, sin dependencias)

**Tiempo estimado de implementación**: 3–4 días

Tkinter viene incluido con Python. Genera una ventana nativa de Windows sin necesidad de instalar nada más.

**Lo que se ganaría:**
- App de escritorio sin necesidad de navegador
- Funciona offline completamente
- Formularios y tablas nativas de Windows
- No requiere conexión a internet ni servidor

**Cuándo elegirla**: si el equipo que usará la app no tiene acceso a un navegador o si se prefiere una app instalable.

---

### Recomendación

| Caso                                      | Opción sugerida |
|-------------------------------------------|-----------------|
| Prototipo rápido para mostrar al cliente  | Streamlit       |
| App interna con varios usuarios           | FastAPI + HTMX  |
| Sistema que crecerá con más módulos       | Django          |
| App de escritorio sin instalar extras     | Tkinter         |

La base de datos SQLite y el módulo `src/db.py` ya están listos para conectarse a cualquiera de estas interfaces sin cambios.
