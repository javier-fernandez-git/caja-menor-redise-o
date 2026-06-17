# Sistema de Reconstrucción Operacional-Financiera

> Antes "Caja Menor". Aplicación **web** (Python + Flask + SQLite) que convierte
> la actividad financiera y técnica fragmentada en **inteligencia organizacional
> consultable**, basada en **eventos homologados temporalmente**.

**Versión actual:** 0.6.0 — Etapas 1 a 6 completadas. (Ver `CHANGELOG.md`.)

No es una simple caja menor CRUD: combina event sourcing, homologación
semántica, doble contabilidad, gobernanza de datos (MDM), analítica causal,
predicción, generación de PDF y una memoria organizacional consultable en
lenguaje natural.

> 📘 Para la **guía paso a paso de puesta en marcha** (incluida una versión
> sencilla para usuarios de negocio) y el **detalle técnico completo**, ver
> **`ROADMAP.md`**. El historial de cambios está en **`CHANGELOG.md`**.

---

## ¿Qué hace?

- **Registro operativo:** captura rápida de movimientos (asignación, gasto,
  reembolso, ajuste) con autocompletar, **homologación en vivo** y validación.
- **Producción técnica:** registro de unidades constructivas ejecutadas.
- **Eventos inmutables:** cada hecho queda como un evento que no se sobrescribe,
  con **score de confiabilidad**.
- **Dos contabilidades:** caja (efectivo disponible) vs obra (inversión real).
- **Analítica gerencial:** tablero con utilidad, alertas, top gastos; **motor
  causal** ("¿por qué subió el costo?"), correlaciones y **predicción**.
- **Gobernanza de datos (MDM):** maestros únicos, convergencia de IDs y
  **permisos por área**.
- **Documentos PDF:** liquidación (logo, firmas, QR, consecutivo), reporte
  financiero y trazabilidad temporal.
- **Memoria consultable:** preguntar en lenguaje natural qué ocurrió en un
  contrato y exportar la cronología (Markdown / JSON).
- **Usuarios y roles:** el digitador solo registra; la gerencia solo analiza.

---

## Requisitos

- **Python 3.10+** (probado en 3.13).
- Dependencias en `requirements.txt`: **Flask, Werkzeug, fpdf2, segno**.

---

## Instalación y ejecución

```bash
# 1. Instalar dependencias (solo la primera vez o cuando cambien)
pip install -r requirements.txt

# 2. Ejecutar la aplicación
python src/webapp.py
#   (en Windows también puedes hacer doble clic en launcher.bat)

# 3. Abrir en el navegador
#    http://127.0.0.1:8000
```

> La base de datos `data/caja_menor.db` se crea y siembra sola en el primer
> arranque (catálogos desde CSV, eventos históricos, maestros MDM, permisos y
> usuarios por defecto). No requiere migración manual.

### Usuarios de prueba

| Usuario | Contraseña | Acceso |
|---|---|---|
| `admin` | `admin123` | Todo (operativo, gerencial, configuración) |
| `gerente` | `ger123` | Analítica gerencial y memoria |
| `digitador` | `dig123` | Solo registro operativo |

> Son credenciales **de prueba**. Cambiarlas antes de cualquier uso real
> (ver "Pendiente hacia 1.0.0").

---

## Estructura del proyecto

```
.
├── data/                       ← CSV semilla + caja_menor.db (se genera sola)
├── src/
│   ├── webapp.py               ← App web Flask (rutas, API, control de acceso)
│   ├── config.py               ← Versión, roles, configuración
│   ├── db.py                   ← Esquema SQLite, catálogos y consultas
│   ├── auth.py                 ← Login, roles y sesiones
│   ├── event_engine.py         ← Eventos inmutables (event sourcing)
│   ├── normalizador.py         ← Homologación semántica
│   ├── contabilidad.py         ← Dos contabilidades (caja vs obra)
│   ├── timeline_engine.py      ← Temporalidad / cronología
│   ├── analytics_engine.py     ← Motor causal + correlaciones
│   ├── predictive_engine.py    ← Predicción y detección de sobreconsumo
│   ├── mdm.py                  ← Gobernanza de datos (maestros, permisos)
│   ├── memoria_engine.py       ← Memoria consultable (lenguaje natural)
│   ├── pdf_engine.py           ← Documentos PDF (fpdf2 + segno)
│   ├── services/               ← Capa de servicios (orquestación por capas)
│   └── app.py / migrate.py     ← Consola legacy (ver nota abajo)
├── templates/                  ← Pantallas (login, operativo, gerencial, …)
├── static/                     ← CSS y JS por pantalla
├── reports/                    ← PDFs generados (ignorado por git)
├── requirements.txt
├── ROADMAP.md                  ← Guía de puesta en marcha + detalle técnico
└── CHANGELOG.md                ← Historial de versiones
```

---

## Esquema de la base de datos (principales tablas)

| Tabla | Descripción |
|---|---|
| `responsables`, `obras`, `centro_de_costos`, `items`, `tipo_movimientos`, `unidades_constructivas` | Catálogos operativos |
| `movimientos` | Movimientos financieros |
| `unidades_ejecutadas` | Producción técnica |
| `eventos_corporativos` | **Repositorio central de eventos inmutables** |
| `diccionario_semantico` | Equivalencias de homologación |
| `mdm_maestros`, `mdm_alias`, `mdm_permisos` | Gobernanza de datos (MDM) |
| `usuarios` | Usuarios y roles |
| `consecutivo`, `consecutivo_pdf` | Consecutivos de recibo y de documentos |

---

## Nota: sistema de consola legacy

`src/app.py` (menú de consola) y `src/migrate.py` son la **versión anterior**.
Quedan en el repositorio como referencia histórica, pero están **superados por
la aplicación web** (`src/webapp.py`), que cubre y amplía todo lo que hacían.

---

## Pendiente hacia 1.0.0 (estabilización)

La funcionalidad del prompt está completa. Antes de un uso productivo falta:

- `SECRET_KEY` y usuario admin por **variables de entorno**; cambiar contraseñas
  demo.
- `debug=False` + servidor **WSGI** real (`waitress`/`gunicorn`).
- Protección **CSRF**, cookies seguras y rate-limit en login.
- **Backup** de la base de datos y migraciones de esquema.
- Pruebas automatizadas.

Despliegue recomendado: **Railway o Render** con disco persistente (no
Vercel/Netlify por el filesystem efímero). Detalles en `ROADMAP.md` (Parte 2).
