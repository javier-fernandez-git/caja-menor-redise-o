from flask import (
    Flask,
    render_template,
    jsonify,
    request
)

from pathlib import Path
import db


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