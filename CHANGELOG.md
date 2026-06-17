# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [SemVer](https://semver.org/lang/es/).
La versión vive en `src/config.py` (`APP_VERSION`).

## [No publicado]

### Por hacer
- Etapa 6 (memoria organizacional consultable). Ver `ROADMAP.md`.

## [0.5.1] — 2026-06-17 — Cierre de Etapa 5

### Añadido
- **Captura de producción técnica** desde la UI (`/operativo`): formulario de
  unidades ejecutadas + `POST /api/unidades-ejecutadas`. `tecnico_service`
  inserta y emite el evento TECNICO en vivo (lo ven timeline, costeo y analítica).
- **PDF de liquidación por responsable** correctamente cableado en `/gerencial`
  (selector de responsable que habilita el botón).
- **Gestión de usuarios** en `/configuracion` (admin): crear, activar/desactivar.
  Endpoints `/api/usuarios` (GET/POST) y `/api/usuarios/<id>/estado`.
- **MDM desde la UI**: alta de maestros y alias, y **editor de permisos por área**
  (`POST /api/mdm/permisos`, `mdm.actualizar_permiso`).
- **Editar / eliminar catálogos**: `POST`/`DELETE /api/catalogo/<tipo>/<id>`
  (la eliminación se bloquea con 409 si el registro está en uso).
- Versión → **0.5.1**.

## [0.5.0] — 2026-06-17 — Etapa 5: UI para usuarios inconsistentes

### Añadido
- **Autenticación y roles** (`auth.py`, tabla `usuarios`, sesiones Flask,
  hash werkzeug). Roles: `digitador`, `gerente`, `admin`. Usuarios demo
  sembrados (cambiar en producción).
- **Separación operativo / gerencial**: guardia central (`before_request`) +
  `rol_required`. Los digitadores NO acceden a la analítica (403 / redirect).
- **UI operativa** (`/operativo`): captura rápida de movimientos con
  autocompletar (datalist), **homologación en vivo** (chip de score
  validado/inferido/sospechoso) y validación inline.
- **UI gerencial** (`/gerencial`): tablero (saldo caja, costo obra, utilidad,
  alertas), motor causal, top gastos, confiabilidad y enlaces a PDF.
- **UI de configuración** (`/configuracion`, admin): alta de catálogos,
  convergencia MDM (resolver), equivalencias y listado de maestros.
- Pantalla de login, layout base con navegación según rol, tema industrial
  (`static/app.css`).
- Endpoints: `/login`, `/logout`, `/api/me`, `/api/catalogo/<tipo>` (POST).
  La guía de uso original queda en `/guia`.
- Versión → **0.5.0**.

## [0.4.0] — 2026-06-16 — Etapa 4: Analítica avanzada + PDF

### Añadido
- **Tablero gerencial** (`analitica_service.tablero_gerencial`): caja, costo de
  obra, utilidad y facturación esperada (modelo económico), producción, top
  gastos, indicadores de confiabilidad y alertas de sobreconsumo.
- **Motor de PDF** (`pdf_engine`, fpdf2 + segno, sin dependencias nativas):
  - `generar_liquidacion_pdf`: recibo con logo opcional, firmas (responsable y
    supervisor), **código QR** de verificación y **consecutivo PDF propio**.
  - `generar_reporte_financiero_pdf`: caja vs obra.
  - `generar_trazabilidad_pdf`: timeline corporativo por contrato.
- Consecutivo de documentos (`consecutivo_pdf`) independiente del recibo.
- Endpoints: `/api/tablero`, `/api/reportes/liquidacion.pdf`,
  `/api/reportes/financiero.pdf`, `/api/reportes/trazabilidad.pdf`.
- Dependencias: `fpdf2`, `segno`.
- Versión → **0.4.0**.

### Corregido
- `db.listar_movimientos` no incluía la columna `monto`, lo que rompía
  `db.liquidacion` (bug latente). Ahora la selecciona.

## [0.3.0] — 2026-06-16 — Etapa 3: Gobernanza de datos (MDM)

### Añadido
- **MDM básico**: tablas `mdm_maestros`, `mdm_alias`, `mdm_permisos`.
  Una entidad maestra por dominio (contrato, centro_costo, item, dependencia,
  sede, empleado) = el ID corporativo universal.
- **Convergencia de IDs** (`mdm.resolver_id_universal`, Regla #3): resuelve
  nombres/alias/parciales al mismo maestro (alias → exacto → homologación →
  contención por tokens → similitud).
- **Permisos por área** (`mdm_permisos`): finanzas crea centros de costo,
  RRHH crea empleados, etc. `crear_maestro` lanza `PermisoDenegado`.
- Siembra de maestros desde los catálogos operativos y de permisos por defecto.
- `services/mdm_service.py` como fachada.
- Catálogo de equivalencias administrable desde API.
- Endpoints: `/api/mdm/dominios`, `/api/mdm/maestros` (GET/POST),
  `/api/mdm/resolver`, `/api/mdm/alias` (GET/POST), `/api/mdm/estado`,
  `/api/mdm/permisos`, `/api/homologar/equivalencia`.
- Versión → **0.3.0**.

## [0.2.0] — 2026-06-16 — Etapa 2: Inteligencia operacional

### Añadido
- **Motor causal** (`analytics_engine.motor_causal`): explica por qué cambió el
  costo de un contrato comparando dos períodos y detectando los ítems que más
  variaron (directos vs indirectos).
- **Motor de correlaciones** (`analytics_engine.motor_correlaciones`): correlación
  de Pearson entre series diarias (gasto, producción, combustible, etc.).
- **Motor predictivo** (`predictive_engine`): `predecir_gasto`,
  `predecir_facturacion`, `predecir_produccion` (regresión lineal) y
  `detectar_sobreconsumo` (anomalías por desviación estándar).
- `services/prediccion_service.py` como fachada de predicción.
- Versionado de la app: `src/config.py` (`APP_VERSION`) y endpoint `/api/version`.
- Clasificación de costos directos/indirectos configurable en `config.py`.
- Endpoints: `/api/causal`, `/api/correlaciones`, `/api/prediccion/gasto`,
  `/api/prediccion/produccion`, `/api/sobreconsumo`, `/api/version`.
- `ROADMAP.md` con todas las etapas y checklist; este `CHANGELOG.md`.

## [0.1.0] — 2026-06-16 — Etapa 1: Construcción del núcleo

### Añadido
- Capa de eventos inmutables (`event_engine`) y tabla `eventos_corporativos`
  (event sourcing, Regla #1).
- Motor de homologación semántica (`normalizador`) y tabla
  `diccionario_semantico` (Regla #2).
- IDs corporativos universales en los eventos (Regla #3).
- Timeline corporativo por fecha/contrato/centro de costo
  (`timeline_engine`, Regla #4).
- Dos contabilidades simultáneas: caja vs obra (`contabilidad`, Regla #5).
- Score de confiabilidad por evento.
- Capa de services: financiero, costeo, contabilidad, homologación, analítica.
- Importador histórico de `data/movimientos.csv`.
- Endpoints API del núcleo (`/api/eventos`, `/api/contabilidad`, `/api/timeline`,
  `/api/dashboard`, `/api/homologar`, `/api/costos-unitarios`, POST `/api/movimientos`).
- `requirements.txt` (Flask) y `ARQUITECTURA_NUCLEO.md`.

### Cambiado
- `db.inicializar()` ahora siembra el diccionario semántico y proyecta los
  movimientos existentes a la capa de eventos (backfill idempotente).

[No publicado]: ./ROADMAP.md
[0.5.1]: ./CHANGELOG.md
[0.5.0]: ./CHANGELOG.md
[0.4.0]: ./CHANGELOG.md
[0.3.0]: ./CHANGELOG.md
[0.2.0]: ./CHANGELOG.md
[0.1.0]: ./CHANGELOG.md
