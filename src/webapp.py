from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    Response,
    redirect,
    url_for,
)

from datetime import date
from pathlib import Path
import db
import auth

# Capas nuevas (Etapa 1: nucleo)
from services import (
    homologacion_service,
    financiero_service,
    costeo_service,
    contabilidad_service,
    analitica_service,
    prediccion_service,
    mdm_service,
    tecnico_service,
)
import timeline_engine
import event_engine
import config
import pdf_engine
from mdm import PermisoDenegado


BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)
app.secret_key = config.SECRET_KEY

db.inicializar()


# ---------------------------------------------------
# CONTROL DE ACCESO (Etapa 5)
# Separa registro operativo de analitica gerencial.
# ---------------------------------------------------

ANALITICA_PREFIJOS = (
    "/api/tablero", "/api/causal", "/api/correlaciones", "/api/prediccion",
    "/api/sobreconsumo", "/api/reportes", "/api/eventos", "/api/contabilidad",
    "/api/timeline", "/api/dashboard", "/api/costos-unitarios",
    "/api/resumen-tecnico",
)
CONFIG_PREFIJOS = ("/api/mdm", "/api/catalogo", "/api/homologar/equivalencia",
                   "/api/usuarios")
PUBLICO = ("/login", "/logout", "/static", "/favicon.ico")


@app.context_processor
def _inyectar_contexto():
    return {"puede_ver": config.puede_ver, "user": auth.usuario_actual()}


@app.before_request
def _guardia_acceso():
    ruta = request.path
    if any(ruta.startswith(p) for p in PUBLICO):
        return None

    usuario = auth.usuario_actual()
    if not usuario:
        return auth._no_autorizado(False)

    rol = usuario["rol"]
    es_api = ruta.startswith("/api/")

    def _denegar(pantalla):
        if es_api:
            return jsonify({"error": "rol sin permiso"}), 403
        return redirect(url_for(config.INICIO_POR_ROL.get(rol, "login")))

    if any(ruta.startswith(p) for p in CONFIG_PREFIJOS):
        if not config.puede_ver(rol, "configuracion"):
            return _denegar("configuracion")
    elif any(ruta.startswith(p) for p in ANALITICA_PREFIJOS):
        if not config.puede_ver(rol, "gerencial"):
            return _denegar("gerencial")
    return None


# ---------------------------------------------------
# FRONTEND
# ---------------------------------------------------

def _catalogos():
    return dict(
        responsables=db.obtener_responsables(),
        obras=db.obtener_obras(),
        centros=db.obtener_centros_de_costos(),
        items=db.obtener_items(),
        tipos=db.obtener_tipos_movimiento(),
    )


@app.route("/")
def home():
    usuario = auth.usuario_actual()
    if not usuario:
        return redirect(url_for("login"))
    return redirect(url_for(config.INICIO_POR_ROL.get(usuario["rol"], "operativo")))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = auth.verificar(
            request.form.get("usuario", ""), request.form.get("password", ""))
        if user:
            auth.iniciar_sesion(user)
            destino = request.form.get("next") or url_for(
                config.INICIO_POR_ROL.get(user["rol"], "operativo"))
            return redirect(destino)
        return render_template("login.html", error="Credenciales invalidas",
                               next=request.form.get("next"))
    if auth.usuario_actual():
        return redirect(url_for("home"))
    return render_template("login.html", next=request.args.get("next"))


@app.route("/logout")
def logout():
    auth.cerrar_sesion()
    return redirect(url_for("login"))


@app.route("/operativo")
@auth.rol_required("operativo")
def operativo():
    return render_template("operativo.html", pantalla="operativo",
                           hoy=date.today().isoformat(), **_catalogos())


@app.route("/gerencial")
@auth.rol_required("gerencial")
def gerencial():
    return render_template("gerencial.html", pantalla="gerencial", **_catalogos())


@app.route("/configuracion")
@auth.rol_required("configuracion")
def configuracion():
    return render_template("configuracion.html", pantalla="configuracion",
                           **_catalogos())


@app.route("/guia")
def guia():
    """Guia de uso original."""
    return render_template("index.html", **_catalogos())


@app.route("/api/me")
def api_me():
    return jsonify(auth.usuario_actual() or {})


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


# ===================================================
# ETAPA 2 — INTELIGENCIA OPERACIONAL
# ===================================================

@app.route("/api/version")
def api_version():
    return jsonify(config.version_info())


# --- Motor causal: ¿por que subio el costo? ---
@app.route("/api/causal")
def api_causal():
    return jsonify(prediccion_service.causa_variacion_costo(
        contrato_id=request.args.get("contrato_id", type=int)
                    or request.args.get("obra_id", type=int),
        centro_costo_id=request.args.get("centro_costo_id", type=int)
                        or request.args.get("cc_id", type=int),
    ))


# --- Correlaciones multivariable ---
@app.route("/api/correlaciones")
def api_correlaciones():
    return jsonify(prediccion_service.correlaciones(
        umbral=request.args.get("umbral", default=0.5, type=float),
        **_filtros_temporales_simple(),
    ))


# --- Prediccion de gasto ---
@app.route("/api/prediccion/gasto")
def api_prediccion_gasto():
    return jsonify(prediccion_service.predecir_gasto(
        horizonte=request.args.get("horizonte", default=7, type=int),
        **_filtros_temporales_simple(),
    ))


# --- Prediccion de produccion ---
@app.route("/api/prediccion/produccion")
def api_prediccion_produccion():
    return jsonify(prediccion_service.predecir_produccion(
        horizonte=request.args.get("horizonte", default=7, type=int),
        **_filtros_temporales_simple(),
    ))


# --- Prediccion de facturacion / utilidad ---
@app.route("/api/prediccion/facturacion")
def api_prediccion_facturacion():
    valor = request.args.get("valor_contrato", type=float)
    dias = request.args.get("duracion_dias", type=int)
    if valor is None or dias is None:
        return jsonify({"error": "valor_contrato y duracion_dias requeridos"}), 400
    return jsonify(prediccion_service.predecir_facturacion(
        valor_contrato=valor, duracion_dias=dias,
        **_filtros_temporales_simple(),
    ))


# --- Deteccion de sobreconsumo / anomalias ---
@app.route("/api/sobreconsumo")
def api_sobreconsumo():
    return jsonify(prediccion_service.detectar_sobreconsumo(
        k=request.args.get("k", default=2.0, type=float),
        **_filtros_temporales_simple(),
    ))


def _filtros_temporales_simple():
    """contrato_id / centro_costo_id / fecha_ini / fecha_fin (sin responsable)."""
    return dict(
        contrato_id=request.args.get("contrato_id", type=int)
                    or request.args.get("obra_id", type=int),
        centro_costo_id=request.args.get("centro_costo_id", type=int)
                        or request.args.get("cc_id", type=int),
        fecha_ini=request.args.get("fecha_ini"),
        fecha_fin=request.args.get("fecha_fin"),
    )


# ===================================================
# ETAPA 3 — GOBERNANZA DE DATOS (MDM)
# ===================================================

@app.route("/api/mdm/dominios")
def api_mdm_dominios():
    return jsonify(mdm_service.dominios())


@app.route("/api/mdm/maestros")
def api_mdm_maestros():
    return jsonify(mdm_service.maestros(
        dominio=request.args.get("dominio"),
        estado=request.args.get("estado"),
    ))


@app.route("/api/mdm/maestros", methods=["POST"])
def api_mdm_crear_maestro():
    data = request.get_json(force=True, silent=True) or {}
    try:
        master_id = mdm_service.crear_maestro(
            dominio=data.get("dominio"),
            nombre=data.get("nombre"),
            area_actor=data.get("area_actor"),
            codigo=data.get("codigo"),
        )
        return jsonify({"ok": True, "master_id": master_id})
    except PermisoDenegado as exc:
        return jsonify({"ok": False, "error": str(exc)}), 403
    except (ValueError, Exception) as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


# --- Convergencia de IDs (Regla #3) ---
@app.route("/api/mdm/resolver")
def api_mdm_resolver():
    dominio = request.args.get("dominio")
    texto = request.args.get("texto", "")
    try:
        return jsonify(mdm_service.resolver(dominio, texto))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


# --- Alias (convergencia) ---
@app.route("/api/mdm/alias")
def api_mdm_alias():
    return jsonify(mdm_service.alias(
        dominio=request.args.get("dominio"),
        master_id=request.args.get("master_id", type=int),
    ))


@app.route("/api/mdm/alias", methods=["POST"])
def api_mdm_crear_alias():
    data = request.get_json(force=True, silent=True) or {}
    try:
        mdm_service.registrar_alias(
            dominio=data.get("dominio"),
            master_id=data.get("master_id"),
            alias_texto=data.get("alias"),
            area_actor=data.get("area_actor"),
        )
        return jsonify({"ok": True})
    except PermisoDenegado as exc:
        return jsonify({"ok": False, "error": str(exc)}), 403
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


# --- Estado de un maestro ---
@app.route("/api/mdm/estado", methods=["POST"])
def api_mdm_estado():
    data = request.get_json(force=True, silent=True) or {}
    try:
        mdm_service.cambiar_estado(
            dominio=data.get("dominio"),
            master_id=data.get("master_id"),
            estado=data.get("estado"),
            area_actor=data.get("area_actor"),
        )
        return jsonify({"ok": True})
    except PermisoDenegado as exc:
        return jsonify({"ok": False, "error": str(exc)}), 403
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


# --- Permisos por area ---
@app.route("/api/mdm/permisos")
def api_mdm_permisos():
    return jsonify(mdm_service.permisos(area=request.args.get("area")))


# --- Alta en catalogos operativos (configuracion) ---
_CATALOGO_MAP = {
    "responsables": ("responsables", "nombre"),
    "obras": ("obras", "nombre"),
    "items": ("items", "nombre"),
    "cc": ("centro_de_costos", "contrato"),
}


@app.route("/api/catalogo/<tipo>", methods=["POST"])
def api_catalogo_agregar(tipo):
    destino = _CATALOGO_MAP.get(tipo)
    if not destino:
        return jsonify({"ok": False, "error": "tipo invalido"}), 400
    data = request.get_json(force=True, silent=True) or {}
    nombre = (data.get("nombre") or "").strip().upper()
    if not nombre:
        return jsonify({"ok": False, "error": "nombre requerido"}), 400
    tabla, columna = destino
    with db.conectar() as conn:
        conn.execute(
            f"INSERT OR IGNORE INTO {tabla} ({columna}) VALUES (?)", (nombre,))
    return jsonify({"ok": True})


# --- Catalogo de equivalencias administrable ---
@app.route("/api/homologar/equivalencia", methods=["POST"])
def api_homologar_equivalencia():
    data = request.get_json(force=True, silent=True) or {}
    ok = mdm_service.registrar_equivalencia(
        dominio=data.get("dominio", "item"),
        variante=data.get("variante"),
        canonico=data.get("canonico"),
        canonico_id=data.get("canonico_id"),
    )
    return jsonify({"ok": bool(ok)})


# ===================================================
# ETAPA 4 — ANALITICA AVANZADA + PDF
# ===================================================

@app.route("/api/tablero")
def api_tablero():
    return jsonify(analitica_service.tablero_gerencial(
        responsable_id=request.args.get("responsable_id", type=int),
        valor_contrato=request.args.get("valor_contrato", type=float),
        duracion_dias=request.args.get("duracion_dias", type=int),
        **_filtros_temporales_simple(),
    ))


def _pdf_response(contenido, nombre):
    return Response(
        contenido,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{nombre}"'},
    )


@app.route("/api/reportes/liquidacion.pdf")
def api_pdf_liquidacion():
    responsable_id = request.args.get("responsable_id", type=int)
    if not responsable_id:
        return jsonify({"error": "responsable_id requerido"}), 400
    contenido = pdf_engine.generar_liquidacion_pdf(
        responsable_id=responsable_id,
        obra_id=request.args.get("obra_id", type=int)
                or request.args.get("contrato_id", type=int),
        cc_id=request.args.get("cc_id", type=int)
              or request.args.get("centro_costo_id", type=int),
        fecha_ini=request.args.get("fecha_ini"),
        fecha_fin=request.args.get("fecha_fin"),
    )
    return _pdf_response(contenido, "liquidacion.pdf")


@app.route("/api/reportes/financiero.pdf")
def api_pdf_financiero():
    contenido = pdf_engine.generar_reporte_financiero_pdf(
        responsable_id=request.args.get("responsable_id", type=int),
        **_filtros_temporales_simple(),
    )
    return _pdf_response(contenido, "reporte_financiero.pdf")


@app.route("/api/reportes/trazabilidad.pdf")
def api_pdf_trazabilidad():
    contenido = pdf_engine.generar_trazabilidad_pdf(**_filtros_temporales_simple())
    return _pdf_response(contenido, "trazabilidad.pdf")


# ===================================================
# CIERRE ETAPA 5 — completar operaciones desde la UI
# ===================================================

# --- Registro de produccion tecnica (operativo) ---
@app.route("/api/unidades-ejecutadas", methods=["POST"])
def api_registrar_unidad_ejecutada():
    data = request.get_json(force=True, silent=True) or {}
    try:
        res = tecnico_service.registrar_unidad_ejecutada(
            movimiento_id=data.get("movimiento_id"),
            unidad_constructiva_id=data.get("unidad_constructiva_id"),
            cantidad=data.get("cantidad"),
            observacion=data.get("observacion"),
            fecha=data.get("fecha"),
            usuario=data.get("usuario"),
        )
        return jsonify({"ok": True, **res})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


# --- Gestion de usuarios (admin) ---
@app.route("/api/usuarios")
def api_usuarios_listar():
    return jsonify(auth.listar_usuarios())


@app.route("/api/usuarios", methods=["POST"])
def api_usuarios_crear():
    data = request.get_json(force=True, silent=True) or {}
    try:
        auth.crear_usuario(
            usuario=data.get("usuario"),
            password=data.get("password"),
            rol=data.get("rol"),
            nombre=data.get("nombre"),
        )
        return jsonify({"ok": True})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.route("/api/usuarios/<int:usuario_id>/estado", methods=["POST"])
def api_usuarios_estado(usuario_id):
    data = request.get_json(force=True, silent=True) or {}
    auth.cambiar_estado_usuario(usuario_id, bool(data.get("activo")))
    return jsonify({"ok": True})


# --- MDM: alta de maestros / permisos desde la UI ---
@app.route("/api/mdm/permisos", methods=["POST"])
def api_mdm_permisos_actualizar():
    data = request.get_json(force=True, silent=True) or {}
    try:
        mdm_service.actualizar_permiso(
            area=data.get("area"),
            dominio=data.get("dominio"),
            puede_crear=data.get("puede_crear"),
            puede_editar=data.get("puede_editar"),
        )
        return jsonify({"ok": True})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


# --- Editar / eliminar catalogo ---
@app.route("/api/catalogo/<tipo>/<int:item_id>", methods=["POST"])
def api_catalogo_editar(tipo, item_id):
    destino = _CATALOGO_MAP.get(tipo)
    if not destino:
        return jsonify({"ok": False, "error": "tipo invalido"}), 400
    data = request.get_json(force=True, silent=True) or {}
    nombre = (data.get("nombre") or "").strip().upper()
    if not nombre:
        return jsonify({"ok": False, "error": "nombre requerido"}), 400
    tabla, columna = destino
    with db.conectar() as conn:
        conn.execute(f"UPDATE {tabla} SET {columna} = ? WHERE id = ?",
                     (nombre, item_id))
    return jsonify({"ok": True})


@app.route("/api/catalogo/<tipo>/<int:item_id>", methods=["DELETE"])
def api_catalogo_eliminar(tipo, item_id):
    destino = _CATALOGO_MAP.get(tipo)
    if not destino:
        return jsonify({"ok": False, "error": "tipo invalido"}), 400
    tabla, _ = destino
    try:
        with db.conectar() as conn:
            conn.execute(f"DELETE FROM {tabla} WHERE id = ?", (item_id,))
        return jsonify({"ok": True})
    except Exception:  # noqa: BLE001 - normalmente FK en uso
        return jsonify({"ok": False,
                        "error": "No se puede eliminar: esta en uso por "
                                 "movimientos u otros registros."}), 409


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