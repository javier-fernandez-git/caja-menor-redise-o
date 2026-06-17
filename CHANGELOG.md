# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [SemVer](https://semver.org/lang/es/).
La versión vive en `src/config.py` (`APP_VERSION`).

## [No publicado]

### Por hacer
- Etapa 4 (PDF), Etapa 5 (UI), Etapa 6 (memoria consultable). Ver `ROADMAP.md`.

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
[0.3.0]: ./CHANGELOG.md
[0.2.0]: ./CHANGELOG.md
[0.1.0]: ./CHANGELOG.md
