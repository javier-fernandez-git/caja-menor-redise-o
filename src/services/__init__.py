"""
Capa de servicios (orquestacion por capas).

Cada service coordina repositorios (db), motores (event_engine, normalizador,
timeline) y reglas de negocio, sin exponer SQL a la UI.
"""
