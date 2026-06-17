"""
auth.py — AUTENTICACION Y ROLES (Etapa 5)

Login con contrasena hasheada (werkzeug) y sesiones Flask. Separa el registro
operativo de la analitica gerencial mediante roles:

    digitador -> solo captura operativa
    gerente   -> solo analitica gerencial
    admin     -> todo + configuracion

Usuarios sembrados por defecto (CAMBIAR en produccion):
    admin / admin123       (admin)
    digitador / dig123     (digitador)
    gerente / ger123       (gerente)
"""

from datetime import datetime
from functools import wraps

from flask import session, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

import db
import config


USUARIOS_DEFAULT = [
    ("admin", "admin123", "admin", "Administrador"),
    ("gerente", "ger123", "gerente", "Gerencia"),
    ("digitador", "dig123", "digitador", "Digitador"),
]


# ----------------------------------------------------------------------
# Gestion de usuarios
# ----------------------------------------------------------------------

def crear_usuario(usuario, password, rol, nombre=None):
    if rol not in config.ROLES:
        raise ValueError(f"Rol invalido: {rol}")
    with db.conectar() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO usuarios
                (usuario, password_hash, rol, nombre, activo, creado_en)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (usuario.strip().lower(), generate_password_hash(password), rol,
             nombre or usuario, datetime.now().isoformat(timespec="seconds")),
        )


def sembrar_usuarios_default():
    with db.conectar() as conn:
        hay = conn.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"]
    if hay:
        return
    for usuario, password, rol, nombre in USUARIOS_DEFAULT:
        crear_usuario(usuario, password, rol, nombre)


def listar_usuarios():
    with db.conectar() as conn:
        return [
            {"id": r["id"], "usuario": r["usuario"], "rol": r["rol"],
             "nombre": r["nombre"], "activo": r["activo"]}
            for r in conn.execute(
                "SELECT id, usuario, rol, nombre, activo FROM usuarios ORDER BY usuario")
        ]


def cambiar_estado_usuario(usuario_id, activo):
    with db.conectar() as conn:
        conn.execute("UPDATE usuarios SET activo = ? WHERE id = ?",
                     (1 if activo else 0, usuario_id))


def verificar(usuario, password):
    """Retorna el dict del usuario si las credenciales son validas, si no None."""
    with db.conectar() as conn:
        fila = conn.execute(
            "SELECT * FROM usuarios WHERE usuario = ? AND activo = 1",
            (usuario.strip().lower(),),
        ).fetchone()
    if fila and check_password_hash(fila["password_hash"], password):
        return {"id": fila["id"], "usuario": fila["usuario"],
                "rol": fila["rol"], "nombre": fila["nombre"]}
    return None


# ----------------------------------------------------------------------
# Sesion
# ----------------------------------------------------------------------

def iniciar_sesion(user):
    session["uid"] = user["id"]
    session["usuario"] = user["usuario"]
    session["rol"] = user["rol"]
    session["nombre"] = user["nombre"]


def cerrar_sesion():
    session.clear()


def usuario_actual():
    if "uid" not in session:
        return None
    return {"id": session["uid"], "usuario": session["usuario"],
            "rol": session["rol"], "nombre": session.get("nombre")}


# ----------------------------------------------------------------------
# Decoradores de proteccion
# ----------------------------------------------------------------------

def _no_autorizado(api):
    if api or request.path.startswith("/api/"):
        return jsonify({"error": "no autorizado"}), 401
    return redirect(url_for("login", next=request.path))


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "uid" not in session:
            return _no_autorizado(False)
        return fn(*args, **kwargs)
    return wrapper


def rol_required(*pantallas):
    """Exige que el rol del usuario tenga acceso a alguna de las pantallas."""
    def decorador(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            rol = session.get("rol")
            if not rol:
                return _no_autorizado(False)
            if not any(config.puede_ver(rol, p) for p in pantallas):
                # Logueado pero sin permiso: a su pantalla de inicio.
                if request.path.startswith("/api/"):
                    return jsonify({"error": "rol sin permiso"}), 403
                return redirect(url_for(config.INICIO_POR_ROL.get(rol, "login")))
            return fn(*args, **kwargs)
        return wrapper
    return decorador
