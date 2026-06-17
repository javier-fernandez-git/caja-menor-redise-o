from flask import (
    Flask,
    render_template,
    jsonify,
    request
)

from pathlib import Path
import db

# Capas nuevas (Etapa 1: nucleo)
from services import (
    homologacion_service,
    financiero_service,
    costeo_service,
    contabilidad_service,
    analitica_service,
)
import timeline_engine
import event_engine


BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

db.inicializar()


# ---------------------------------------------------
# FRONTEND
# ---------------------------------------------------

@app.route("/")
def home():

    responsables = db.obtener_responsables()
    obras = db.obtener_obras()
    centros = db.obtener_centros_de_costos()
    items = db.obtener_items()
    tipos = db.obtener_tipos_movimiento()

    return render_template(
        "index.html",
        responsables=responsables,
        obras=obras,
        centros=centros,
        items=items,
        tipos=tipos
    )


# ---------------------------------------------------
# API ITEMS
# ---------------------------------------------------

@app.route("/api/items")
def api_items():

    return jsonify(db.obtener_items())


# ---------------------------------------------------
# API UNIDADES CONSTRUCTIVAS
# ---------------------------------------------------

@app.route("/api/unidades-constructivas")
def api_unidades_constructivas():

    return jsonify(db.obtener_unidades_constructivas())


# ---------------------------------------------------
# API RESPONSABLES
# ---------------------------------------------------

@app.route("/api/responsables")
def api_responsables():

    return jsonify(db.obtener_responsables())


# ---------------------------------------------------
# API OBRAS
# ---------------------------------------------------

@app.route("/api/obras")
def api_obras():

    return jsonify(db.obtener_obras())


# ---------------------------------------------------
# API TIPOS
# ---------------------------------------------------

@app.route("/api/tipos")
def api_tipos():

    return jsonify(db.obtener_tipos_movimiento())


# ---------------------------------------------------
# API CENTROS DE COSTOS
# ---------------------------------------------------

@app.route("/api/cc")
def api_cc():

    return jsonify(db.obtener_centros_de_costos())


@app.route("/api/movimientos")
def api_movimientos():

    return jsonify(db.listar_movimientos(
        responsable_id=request.args.get("responsable_id", type=int),
        obra_id=request.args.get("obra_id", type=int),
        fecha_ini=request.args.get("fecha_ini"),
        fecha_fin=request.args.get("fecha_fin"),
        tipo=request.args.get("tipo"),
        cc_id=request.args.get("cc_id", type=int),
    ))


@app.route("/api/unidades-ejecutadas")
def api_unidades_ejecutadas():

    return jsonify(db.consultar_unidades_ejecutadas(
        movimiento_id=request.args.get("movimiento_id", type=int),
        responsable_id=request.args.get("responsable_id", type=int),
        obra_id=request.args.get("obra_id", type=int),
        fecha_ini=request.args.get("fecha_ini"),
        fecha_fin=request.args.get("fecha_fin"),
    ))


@app.route("/api/resumen-tecnico")
def api_resumen_tecnico():

    return jsonify(db.generar_resumen_tecnico(
        responsable_id=request.args.get("responsable_id", type=int),
        obra_id=request.args.get("obra_id", type=int),
        fecha_ini=request.args.get("fecha_ini"),
        fecha_fin=request.args.get("fecha_fin"),
    ))


# ===================================================
# CAPAS NUEVAS (Etapa 1: nucleo)
# ===================================================

def _filtros_temporales():
    """Filtros comunes leidos de la query string."""
    return dict(
        contrato_id=request.args.get("contrato_id", type=int)
                    or request.args.get("obra_id", type=int),
        centro_costo_id=request.args.get("centro_costo_id", type=int)
                        or request.args.get("cc_id", type=int),
        responsable_id=request.args.get("responsable_id", type=int),
        fecha_ini=request.args.get("fecha_ini"),
        fecha_fin=request.args.get("fecha_fin"),
    )


# --- Homologacion semantica ---
@app.route("/api/homologar")
def api_homologar():
    texto = request.args.get("texto", "")
    dominio = request.args.get("dominio", "item")
    return jsonify(homologacion_service.homologar(texto, dominio))


# --- Registro financiero (orquestado: persiste + emite evento) ---
@app.route("/api/movimientos", methods=["POST"])
def api_registrar_movimiento():
    data = request.get_json(force=True, silent=True) or {}
    try:
        resultado = financiero_service.registrar_movimiento(
            responsable_id=data.get("responsable_id"),
            tipo_id=data.get("tipo_id"),
            monto=data.get("monto", 0),
            cc_id=data.get("cc_id"),
            item_id=data.get("item_id"),
            obra_id=data.get("obra_id"),
            fecha=data.get("fecha"),
            observacion=data.get("observacion"),
            soporte=data.get("soporte"),
            usuario=data.get("usuario"),
        )
        return jsonify({"ok": True, **resultado})
    except Exception as exc:  # noqa: BLE001 - reportar al cliente
        return jsonify({"ok": False, "error": str(exc)}), 400


# --- Eventos corporativos (event sourcing) ---
@app.route("/api/eventos")
def api_eventos():
    return jsonify(event_engine.consultar_eventos(
        tipo_evento=request.args.get("tipo_evento"),
        score_minimo=request.args.get("score_minimo", type=float),
        **_filtros_temporales(),
    ))


# --- Dos contabilidades (caja vs obra) ---
@app.route("/api/contabilidad")
def api_contabilidad():
    return jsonify(contabilidad_service.estado(**_filtros_temporales()))


# --- Timeline corporativo ---
@app.route("/api/timeline")
def api_timeline():
    return jsonify(timeline_engine.reconstruir_timeline(**_filtros_temporales()))


# --- Dashboard gerencial ---
@app.route("/api/dashboard")
def api_dashboard():
    return jsonify(analitica_service.dashboard(**_filtros_temporales()))


# --- Costos unitarios reales ---
@app.route("/api/costos-unitarios")
def api_costos_unitarios():
    return jsonify(costeo_service.calcular_costos_unitarios(
        responsable_id=request.args.get("responsable_id", type=int),
        obra_id=request.args.get("obra_id", type=int),
        fecha_ini=request.args.get("fecha_ini"),
        fecha_fin=request.args.get("fecha_fin"),
    ))


# ---------------------------------------------------

if __name__ == "__main__":

    print("\n====================================")
    print(" SERVIDOR WEB CAJA MENOR")
    print(" http://127.0.0.1:8000")
    print("====================================\n")

    app.run(
        host="127.0.0.1",
        port=8000,
        debug=True
    )