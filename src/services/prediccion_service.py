"""
prediccion_service.py — CAPA PREDICTIVA (fachada).

Orquesta los motores analitico y predictivo para la UI/API.
"""

import analytics_engine
import predictive_engine


# --- Motor causal / correlaciones ---
def causa_variacion_costo(**kwargs):
    return analytics_engine.motor_causal(**kwargs)


def correlaciones(**kwargs):
    return analytics_engine.motor_correlaciones(**kwargs)


# --- Predicciones ---
def predecir_gasto(**kwargs):
    return predictive_engine.predecir_gasto(**kwargs)


def predecir_produccion(**kwargs):
    return predictive_engine.predecir_produccion(**kwargs)


def predecir_facturacion(valor_contrato, duracion_dias, **kwargs):
    return predictive_engine.predecir_facturacion(
        valor_contrato, duracion_dias, **kwargs)


def detectar_sobreconsumo(**kwargs):
    return predictive_engine.detectar_sobreconsumo(**kwargs)
