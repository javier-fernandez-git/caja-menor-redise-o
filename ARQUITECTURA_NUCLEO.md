# Reconstrucción del núcleo — Etapa 1

Implementación de la **Etapa 1 (Construcción del núcleo)** del prompt maestro,
evolucionando la app Flask existente (no se reescribió desde cero).

## Reglas del prompt → dónde viven

| Regla | Implementación |
|-------|----------------|
| #1 — Todo es un evento (inmutable) | `src/event_engine.py` + tabla `eventos_corporativos`. No se sobrescribe; una corrección es un evento nuevo. |
| #2 — Homologación semántica | `src/normalizador.py` (`diccionario_equivalencias`, `motor_normalizacion()`, `normalizar_item/centro_costo/contrato/dependencia`) + tabla `diccionario_semantico`. |
| #3 — IDs corporativos universales | `contrato_id`/`centro_costo_id`/`responsable_id`/`item_id` en los eventos; los nombres se resuelven contra catálogos. |
| #4 — Temporalidad como eje | `src/timeline_engine.py` (`reconstruir_timeline`, `narrar_timeline`); todo se agrupa por fecha. |
| #5 — Dos contabilidades | `src/contabilidad.py` — `contabilidad_caja` (saldo de efectivo) vs `contabilidad_obra` (inversión; los reembolsos NO reducen costo). |
| Score de confiabilidad | Cada evento lleva `score_confiabilidad` (1.0 validado / 0.7 inferido / 0.4 sospechoso), calculado por el motor de homologación. |

## Capas / services (`src/services/`)

- `homologacion_service` — fachada del motor de homologación.
- `financiero_service` — registra movimiento → persiste en `movimientos` **y** emite evento homologado.
- `costeo_service` — costos unitarios + modelo económico del contrato (esperado vs real, desviación).
- `contabilidad_service` — caja vs obra.
- `analitica_service` — dashboard gerencial (top gastos, indicadores de confiabilidad) + timeline.

## Datos

`data/movimientos.csv` (136 registros históricos) ahora se importa una sola vez a
la tabla `movimientos` (`db.importar_movimientos_historicos`) y se proyecta a la
capa de eventos (`event_engine.backfill_desde_movimientos`, idempotente).

## Endpoints nuevos (Flask)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/homologar?texto=&dominio=` | Homologa un texto humano. |
| POST | `/api/movimientos` | Registra movimiento + evento (JSON). |
| GET | `/api/eventos` | Repositorio de eventos (filtros temporales). |
| GET | `/api/contabilidad` | Caja vs obra. |
| GET | `/api/timeline` | Cronología corporativa. |
| GET | `/api/dashboard` | Tablero gerencial. |
| GET | `/api/costos-unitarios` | Costo unitario real por producción. |

Filtros comunes: `contrato_id`/`obra_id`, `centro_costo_id`/`cc_id`,
`responsable_id`, `fecha_ini`, `fecha_fin`.

## Cómo correr

```bash
pip install -r requirements.txt
python src/webapp.py          # http://127.0.0.1:8000
```

## Pendiente — Etapa 2 (inteligencia operacional)

Motor causal (`¿por qué subió el costo?`), correlaciones multivariable,
predicción (`predecir_gasto/facturacion/produccion`, `detectar_sobreconsumo`),
MDM con permisos por área, y generación de PDF de liquidaciones.
