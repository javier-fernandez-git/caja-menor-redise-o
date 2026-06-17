# ROADMAP — Reconstrucción operacional-financiera

Plan por etapas para implementar el prompt maestro completo
(*"Sistema de reconstrucción histórica operacional-financiera basado en
eventos homologados temporalmente"*).

Marcar cada ítem al completarlo: `[ ]` → `[x]`.
La versión de la app sube con cada etapa (ver `CHANGELOG.md` y `src/config.py`).

| Etapa | Versión | Estado |
|-------|---------|--------|
| 1. Núcleo | 0.1.0 | ✅ Completada |
| 2. Inteligencia operacional | 0.2.0 | ✅ Completada |
| 3. Gobernanza de datos (MDM) | 0.3.0 | ✅ Completada |
| 4. Capa analítica + PDF | 0.4.0 | ✅ Completada |
| 5. UI para usuarios inconsistentes | 0.5.0 | ⏳ Pendiente |
| 6. Memoria organizacional consultable | 0.6.0 | ⏳ Pendiente |
| Estabilización y release | 1.0.0 | ⏳ Pendiente |

---

## Etapa 1 — Construcción del núcleo  ✅  (v0.1.0)

> Infraestructura estable. Separar registro operativo de analítica gerencial.

- [x] Esquema SQLite + modelos base
- [x] **Regla #1** Eventos inmutables (`event_engine`, tabla `eventos_corporativos`)
- [x] **Regla #2** Homologación semántica (`normalizador`, `diccionario_semantico`)
- [x] **Regla #3** IDs corporativos universales en los eventos
- [x] **Regla #4** Temporalidad / timeline (`timeline_engine`)
- [x] **Regla #5** Dos contabilidades: caja vs obra (`contabilidad`)
- [x] Score de confiabilidad por evento
- [x] Capa de services (financiero, costeo, contabilidad, homologación, analítica)
- [x] Importador histórico de `movimientos.csv`
- [x] Endpoints API del núcleo
- [x] Validaciones básicas

---

## Etapa 2 — Inteligencia operacional  ✅  (v0.2.0)

> Motor analítico y predictivo.

- [x] Modelo económico del contrato (esperado vs real, desviación) — `costeo_service`
- [x] **Motor causal** — *¿por qué subió el costo del contrato?* (`analytics_engine`)
- [x] **Motor de correlaciones** multivariable (`motor_correlaciones`)
- [x] **Predicción de gasto** (`predecir_gasto`)
- [x] **Predicción de facturación** (`predecir_facturacion`)
- [x] **Predicción de producción** (`predecir_produccion`)
- [x] **Detección de sobreconsumo / anomalías** (`detectar_sobreconsumo`)
- [x] Endpoints API de analítica y predicción
- [x] Versionado de la app + `/api/version`

---

## Etapa 3 — Gobernanza de datos (MDM)  ✅  (v0.3.0)

> Master Data Management básico + permisos por área.

- [x] Tablas maestras por dominio (`mdm_maestros` subsume `contratos_master`,
      `centros_costos_master`, `items_master`, `dependencias_master`,
      `sedes_master` y `empleados`)
- [x] Repositorio central `eventos_corporativos` recibiendo de todos los módulos *(Etapa 1)*
- [x] Permisos por área (`mdm_permisos`: finanzas crea centros de costo; RRHH crea empleados)
- [x] Reglas de convergencia de IDs (`resolver_id_universal`: proyecto/frente/contrato → ID universal)
- [x] Catálogo de equivalencias administrable (`/api/homologar/equivalencia`)

---

## Etapa 4 — Capa analítica avanzada + PDF  ✅  (v0.4.0)

> Dashboards gerenciales y documentos.

- [x] Tablero gerencial: utilidad, costo de obra, producción,
      facturación esperada, top gastos, alertas (`analitica_service.tablero_gerencial`)
- [x] `pdf_engine`: liquidaciones, reportes financieros, trazabilidad
- [x] Liquidación con logo (opcional), firmas, QR y consecutivo PDF propio
- [x] Reporte de trazabilidad temporal por contrato
- [x] Endpoints `/api/tablero` y `/api/reportes/*.pdf`

---

## Etapa 5 — UI para usuarios inconsistentes  ⏳  (v0.5.0)

> Mínimo esfuerzo cognitivo, digitación rápida, industrial.

- [ ] Separación física: registro operativo vs analítica gerencial
- [ ] Autocompletar / sugerir / inferir / corregir en captura
- [ ] Validación automática en formularios
- [ ] Login y roles (`ui/login`)
- [ ] Pantallas: dashboard, movimientos, resumen, liquidación, indicadores, configuración

---

## Etapa 6 — Memoria organizacional consultable  ⏳  (v0.6.0)

> Convertir actividad humana fragmentada en inteligencia consultable.

- [ ] Consulta del timeline en lenguaje natural
      (*"¿qué ocurrió en el contrato X entre A y B?"*)
- [ ] Reconstrucción narrativa de cronologías corporativas
- [ ] Indicadores predictivos integrados al dashboard
- [ ] Exportación de memoria organizacional

---

## Hacia 1.0.0 — Estabilización

- [ ] Pruebas automatizadas de las capas
- [ ] Empaquetado / distribución (icono, splash, launcher)
- [ ] Documentación de usuario final
- [ ] Estrategia de respaldo de datos reales (fuera de git)
