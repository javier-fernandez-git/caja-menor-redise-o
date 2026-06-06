from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import db

app = FastAPI()

from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")

# Permitir conexión desde HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────
# ENDPOINT: OBRAS
# ─────────────────────────────
@app.get("/obras")
def obtener_obras():
    return db.obtener_obras()


# ─────────────────────────────
# AGREGAR OBRA
# ─────────────────────────────
@app.post("/obras")
def agregar_obra(nombre: str):
    with db.conectar() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO obras (nombre) VALUES (?)", (nombre.upper(),)
        )
    return {"ok": True}
