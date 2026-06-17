# ROADMAP — Sistema de Reconstrucción Operacional-Financiera

Este documento tiene **dos partes**:

- **Parte 1 — Guía de revisión:** instrucciones sencillas, sin tecnicismos, para
  descargar la última versión, ejecutar la aplicación y entender qué hace.
  *(Pensada para quien conoce el negocio pero no programa.)*
- **Parte 2 — Detalle técnico:** arquitectura, módulos, endpoints, decisiones y
  lo que falta hacia la versión 1.0.0. *(Pensada para un desarrollador o una IA.)*

Estado general: **Etapas 1 a 6 del prompt COMPLETADAS** (versión 0.6.0).
Falta solo la fase de **estabilización y despliegue** hacia 1.0.0.

---
---

# PARTE 1 — GUÍA DE REVISIÓN (sencilla)

> Objetivo: que puedas abrir la aplicación en tu computador, navegarla y entender
> qué se construyó. No necesitas saber programar. Sigue los pasos en orden.

## Qué vas a ver
Una aplicación web (se abre en el navegador, como una página) que reemplaza el
viejo sistema de consola. Permite **registrar gastos**, ver **análisis e
indicadores**, generar **PDFs**, y **preguntar en lenguaje normal** qué pasó en
cada contrato.

## Paso 1 — Abrir el proyecto en VS Code
1. Abre **Visual Studio Code**.
2. Menú **File → Open Folder…** y elige la carpeta del proyecto
   (`caja-menor-redise-o`).

## Paso 2 — Traer la última versión (git pull)
La versión nueva ya está en la rama **main**. Tienes dos formas; usa la que te
resulte cómoda.

**Forma A — visual (recomendada para ti):**
1. Abajo a la izquierda de VS Code verás el **nombre de la rama** (un icono de
   ramita). Haz clic y selecciona **`main`**.
2. Al lado del nombre de la rama hay un icono de **flechas en círculo (🔄
   sincronizar)**. Haz clic ahí: eso descarga la última versión.

**Forma B — terminal:**
1. Menú **Terminal → New Terminal**.
2. Escribe estos dos comandos (Enter después de cada uno):
   ```
   git checkout main
   git pull
   ```

## Paso 3 — Instalar lo necesario (solo la primera vez)
La app usa unos componentes. En la terminal de VS Code escribe:
```
pip install -r requirements.txt
```
Espera a que termine. Esto solo se repite si en el futuro se agregan componentes
nuevos.

## Paso 4 — Ejecutar la aplicación
Tienes dos opciones:

- **Opción fácil:** en el explorador de archivos de Windows, haz doble clic en
  **`launcher.bat`**. Abre la app y el navegador solo.
- **Opción terminal:** en la terminal de VS Code escribe:
  ```
  python src/webapp.py
  ```
  Luego abre el navegador en: **http://127.0.0.1:8000**

> La base de datos se prepara sola en el primer arranque y ya carga los
> movimientos históricos. No tienes que configurar nada.

## Paso 5 — Ingresar y revisar
Verás una pantalla de **ingreso**. Hay tres usuarios de prueba (cada uno ve
cosas distintas a propósito):

| Usuario | Contraseña | Qué ve |
|---|---|---|
| `admin` | `admin123` | Todo (registro, análisis y configuración) |
| `gerente` | `ger123` | Solo análisis gerencial y memoria |
| `digitador` | `dig123` | Solo registro de gastos (no ve los análisis) |

Sugerencia de recorrido (entra como **admin** para verlo todo):
1. **Registro operativo:** registra un gasto. Al escribir el concepto, fíjate
   cómo el sistema lo **traduce y valida solo** (chip de color).
2. **Analítica gerencial:** mira los indicadores, "por qué cambió el costo",
   alertas y los botones de **PDF**.
3. **Memoria:** escribe una pregunta como *"¿qué ocurrió en libano 2000?"* y
   observa la respuesta en lenguaje natural.
4. **Configuración:** catálogos, usuarios y gobernanza de datos.

## Paso 6 — Cerrar la aplicación
En la terminal donde está corriendo, presiona **Ctrl + C**. (Si usaste
`launcher.bat`, cierra la ventana negra que se abrió.)

## Si algo no funciona
- *"python no se reconoce"* → falta instalar Python (python.org) y marcar
  "Add to PATH" al instalar.
- *La página no abre* → revisa que la terminal diga "SERVIDOR WEB CAJA MENOR" y
  vuelve a entrar a http://127.0.0.1:8000.

## Resumen macro: qué se construyó (en lenguaje de negocio)
La aplicación dejó de ser "una caja menor" y se convirtió en un **sistema de
reconstrucción histórica operacional-financiera**. Se hizo por etapas:

- **Etapa 1 — Base inteligente.** Cada hecho se guarda como un **evento que no se
  borra** (historial confiable). Un **traductor** unifica los nombres que cada
  persona escribe distinto ("mantto veh", "mantenimiento" → un solo término). Y
  se separan dos cuentas: **cuánto efectivo queda** vs. **cuánto se invirtió en
  la obra**.
- **Etapa 2 — Inteligencia.** El sistema **explica por qué subió el costo**,
  **detecta gastos anormales** y **proyecta** el gasto futuro.
- **Etapa 3 — Orden de datos.** Una **lista maestra única** de contratos,
  centros de costo e ítems para que todas las áreas hablen de lo mismo, con
  **permisos** (quién puede crear qué).
- **Etapa 4 — Tablero y documentos.** Un **tablero gerencial** con utilidad,
  alertas y top de gastos; y **PDFs** profesionales (liquidación con firma y
  código QR, reporte financiero, trazabilidad).
- **Etapa 5 — Aplicación fácil de usar.** Interfaz web con **usuarios y roles**:
  el digitador solo registra, la gerencia solo analiza. Captura **rápida** que
  corrige y sugiere sola.
- **Etapa 6 — Memoria consultable.** Preguntar en **lenguaje normal** qué pasó
  en un contrato y recibir un **relato**, además de **exportar** la historia.

## Nota importante
Las contraseñas de arriba son **solo para revisar**. Cuando la app se use de
verdad, hay que cambiarlas. Eso es parte de la fase de estabilización (Parte 2).

---
---

# PARTE 2 — DETALLE TÉCNICO (para desarrollador / IA)

## Resumen de estado
- **Versión actual:** 0.6.0 (`src/config.py` → `APP_VERSION`).
- **Etapas 1–6 del prompt:** completadas.
- **Pendiente:** estabilización y despliegue → 1.0.0.
- La versión vive en `src/config.py`; el historial detallado en `CHANGELOG.md`.

## Stack y arranque
- **Backend:** Python 3.13 + Flask 3.1 (servidor de desarrollo).
- **Base de datos:** SQLite (`data/caja_menor.db`), archivo único.
- **PDF/QR:** `fpdf2` + `segno` (puro Python, sin dependencias nativas).
- **Auth:** `werkzeug.security` (hash de contraseñas) + sesiones Flask.
- **Frontend:** plantillas Jinja + JS vanilla + `static/app.css` (sin framework).
- **Arranque:** `python src/webapp.py` (o `launcher.bat`) → `127.0.0.1:8000`.
- **Dependencias:** `requirements.txt` (Flask, Werkzeug, fpdf2, segno).
- La BD se inicializa y siembra sola en `db.inicializar()` (idempotente):
  catálogos desde CSV, diccionario semántico, backfill de eventos, maestros MDM,
  permisos y usuarios por defecto.

## Arquitectura por capas (reglas del prompt)
| Regla | Implementación |
|---|---|
| #1 — Todo es un evento (inmutable) | `event_engine.py` + tabla `eventos_corporativos` |
| #2 — Homologación semántica | `normalizador.py` + tabla `diccionario_semantico` |
| #3 — IDs corporativos universales | `mdm.py` (`resolver_id_universal`) + `mdm_maestros` |
| #4 — Temporalidad como eje | `timeline_engine.py` |
| #5 — Dos contabilidades (caja vs obra) | `contabilidad.py` |
| Score de confiabilidad | Campo en cada evento (1.0 / 0.7 / 0.4) |

## Mapa de módulos (`src/`)
- **Núcleo / motores:** `db.py`, `config.py`, `event_engine.py`,
  `normalizador.py`, `contabilidad.py`, `timeline_engine.py`,
  `analytics_engine.py` (causal + correlaciones), `predictive_engine.py`,
  `mdm.py`, `memoria_engine.py`, `pdf_engine.py`, `auth.py`.
- **Capa de servicios (`src/services/`):** `financiero_service`,
  `tecnico_service`, `costeo_service`, `contabilidad_service`,
  `homologacion_service`, `analitica_service`, `prediccion_service`,
  `mdm_service`, `memoria_service`.
- **Web:** `webapp.py` (rutas, API y control de acceso),
  `templates/` (login, base, operativo, gerencial, configuracion, memoria,
  index=guía), `static/` (CSS + JS por pantalla).

## Catálogo de endpoints (principales)
- **Auth/páginas:** `/login`, `/logout`, `/`, `/operativo`, `/gerencial`,
  `/configuracion`, `/memoria`, `/guia`, `/api/me`, `/api/version`.
- **Operativo:** `GET/POST /api/movimientos`, `POST /api/unidades-ejecutadas`,
  catálogos `GET /api/{responsables,obras,cc,tipos,items,unidades-constructivas}`,
  `GET /api/homologar`.
- **Analítica (rol gerencial):** `/api/tablero`, `/api/dashboard`,
  `/api/contabilidad`, `/api/timeline`, `/api/eventos`, `/api/causal`,
  `/api/correlaciones`, `/api/prediccion/{gasto,produccion,facturacion}`,
  `/api/sobreconsumo`, `/api/costos-unitarios`, `/api/resumen-tecnico`,
  `/api/reportes/{liquidacion,financiero,trazabilidad}.pdf`,
  `/api/memoria/{consultar,narrativa,exportar}`.
- **Configuración (admin):** `POST /api/catalogo/<tipo>` (+ editar/eliminar
  `/<id>`), `GET/POST /api/usuarios` (+ `/<id>/estado`),
  `/api/mdm/{maestros,alias,permisos,resolver,...}`,
  `POST /api/homologar/equivalencia`.

## Control de acceso (separación operativo / gerencial)
- Guardia central `before_request` + decorador `rol_required` en `webapp.py`.
- Roles: `digitador` (operativo), `gerente` (gerencial), `admin` (todo).
- Los digitadores reciben **403** en cualquier endpoint de analítica.

## Versionado y etapas (todas ✅)
| Etapa | Versión | Entregable |
|---|---|---|
| 1. Núcleo | 0.1.0 | Event sourcing, homologación, dos contabilidades, timeline, services, score |
| 2. Inteligencia operacional | 0.2.0 | Motor causal, correlaciones, predicción, sobreconsumo, modelo económico |
| 3. Gobernanza (MDM) | 0.3.0 | Maestros, convergencia de IDs, permisos por área, equivalencias |
| 4. Analítica + PDF | 0.4.0 | Tablero gerencial, liquidación/financiero/trazabilidad PDF con QR y consecutivo |
| 5. UI con roles | 0.5.0–0.5.1 | Login/roles, operativo, gerencial, configuración; cierre (producción, usuarios, MDM-UI, catálogos editables) |
| 6. Memoria consultable | 0.6.0 | Consulta en lenguaje natural, narrativa, exportación MD/JSON, predictivo en tablero |

### Etapa 1 — Núcleo (v0.1.0)
- [x] Esquema SQLite + modelos
- [x] Eventos inmutables (`event_engine`, `eventos_corporativos`)
- [x] Homologación semántica (`normalizador`, `diccionario_semantico`)
- [x] IDs universales en eventos
- [x] Timeline (`timeline_engine`)
- [x] Dos contabilidades (`contabilidad`)
- [x] Score de confiabilidad
- [x] Capa de services + importador histórico + endpoints del núcleo

### Etapa 2 — Inteligencia operacional (v0.2.0)
- [x] Modelo económico del contrato (esperado vs real)
- [x] Motor causal (¿por qué subió el costo?)
- [x] Correlaciones multivariable
- [x] Predicción de gasto / facturación / producción
- [x] Detección de sobreconsumo
- [x] Endpoints + versionado + `/api/version`

### Etapa 3 — Gobernanza de datos / MDM (v0.3.0)
- [x] Tablas maestras por dominio (`mdm_maestros`)
- [x] Convergencia de IDs (`resolver_id_universal`)
- [x] Permisos por área (`mdm_permisos`)
- [x] Equivalencias administrables

### Etapa 4 — Analítica avanzada + PDF (v0.4.0)
- [x] Tablero gerencial (utilidad, costo obra, producción, top gastos, alertas)
- [x] `pdf_engine`: liquidación (logo/firmas/QR/consecutivo), financiero, trazabilidad
- [x] Endpoints `/api/tablero` y `/api/reportes/*.pdf`

### Etapa 5 — UI para usuarios inconsistentes (v0.5.0) + cierre (v0.5.1)
- [x] Separación operativo vs gerencial (roles, 403 a digitadores en analítica)
- [x] Autocompletar + homologación en vivo + validación inline
- [x] Login y roles (`auth.py`)
- [x] Pantallas operativo / gerencial / configuración
- [x] Cierre: captura de producción, gestión de usuarios, MDM en UI
      (crear maestros/alias/permisos), catálogos editables/eliminables,
      liquidación PDF por responsable

### Etapa 6 — Memoria organizacional consultable (v0.6.0)
- [x] Consulta en lenguaje natural (`memoria_engine.consultar`)
- [x] Reconstrucción narrativa de cronologías
- [x] Indicadores predictivos integrados al tablero (`prediccion_gasto`)
- [x] Exportación de memoria (Markdown / JSON)
- [x] Pantalla `/memoria` (rol gerencial)

## Decisiones de diseño clave
- **Eventos inmutables:** no se editan ni borran; una corrección debe ser un
  evento nuevo (la UI de corrección aún no existe — ver pendientes).
- **Dos contabilidades:** los reembolsos NO reducen el costo de obra (la
  inversión sí ocurrió).
- **MDM en una sola tabla por dominio** (`mdm_maestros`), en vez de cinco tablas
  `*_master`; subsume contrato/centro_costo/item/dependencia/sede/empleado.
- **La base `data/caja_menor.db` está des-trackeada de git** mediante
  `git update-index --skip-worktree` (se regenera en local desde los CSV). Por
  eso NO aparece como modificada aunque la app la actualice. Implicación: los
  datos reales capturados por la app **no están respaldados por git** → se
  necesita una estrategia de backup propia.

## Pendiente — Estabilización hacia 1.0.0
Bloqueantes para producción:
- [ ] `SECRET_KEY` y usuario admin por **variables de entorno**; cambiar
      contraseñas demo.
- [ ] `debug=False` + servidor WSGI real (`waitress` en Windows / `gunicorn` en
      Linux) en lugar del servidor de desarrollo.
- [ ] Protección **CSRF** en formularios/endpoints POST; cookies
      `Secure`/`HttpOnly`/`SameSite`; rate-limit en login.
- [ ] Estrategia de **backup** de la base de datos.
- [ ] Validación server-side reforzada (montos, fechas).

Importante (no bloqueante):
- [ ] Pruebas automatizadas (pytest) de las capas.
- [ ] Paginación en listados grandes (`/api/movimientos`, `/api/eventos`).
- [ ] Migraciones de esquema (hoy todo es `CREATE IF NOT EXISTS`).
- [ ] Edición de usuarios y reseteo de contraseña; auditoría de cambios de config.
- [ ] UI de "evento de corrección" para enmendar movimientos sin romper la
      inmutabilidad.
- [ ] Gráficas en el tablero (hoy son tablas).

## Despliegue (recomendación)
La app es un **servidor Flask con estado y SQLite en archivo**:
- **No usar Vercel/Netlify** tal cual: su filesystem es efímero y SQLite no
  persiste (requeriría migrar a Postgres).
- **Recomendado: Railway o Render** con **disco persistente** montado en `data/`
  para conservar la BD. (Railway ya es conocido en el entorno del equipo.)
- Mínimos: `SECRET_KEY`/usuarios por entorno, `debug=False`, WSGI (`waitress`/
  `gunicorn`), disco persistente, sembrar admin real al primer arranque.
- **Decisión previa:** si será **multiusuario con escritura concurrente**,
  migrar SQLite → **PostgreSQL** (SQLite bloquea en escrituras concurrentes).
  Para uso interno de baja concurrencia, SQLite en disco persistente es válido.
