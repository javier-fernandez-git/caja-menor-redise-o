// configuracion.js — catálogos, convergencia MDM, equivalencias y maestros.
(function () {
  const $ = (id) => document.getElementById(id);

  // --- Agregar al catálogo ---
  $("btn-cat").addEventListener("click", async () => {
    const tipo = $("cat-tipo").value;
    const nombre = $("cat-nombre").value.trim();
    if (!nombre) { toast("Escribe un nombre", true); return; }
    const r = await fetch(`/api/catalogo/${tipo}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre }),
    });
    const res = await r.json();
    if (res.ok) { toast("Agregado al catálogo"); $("cat-nombre").value = ""; }
    else toast(res.error || "No se pudo agregar", true);
  });

  // --- Resolver MDM ---
  $("btn-mdm").addEventListener("click", async () => {
    const dominio = $("mdm-dominio").value;
    const texto = $("mdm-texto").value.trim();
    if (!texto) return;
    const res = await (await fetch(`/api/mdm/resolver?dominio=${dominio}&texto=${encodeURIComponent(texto)}`)).json();
    const out = $("mdm-resultado");
    if (res.master_id) {
      const cls = res.score >= 1 ? "ok" : (res.score >= 0.7 ? "warn" : "bad");
      out.innerHTML = `<span class="chip ${cls}">#${res.master_id} · ${res.nombre_canonico} · ${res.metodo} (${res.score})</span>`;
    } else {
      const sug = res.sugerencia ? ` ¿Quizá "${res.sugerencia.nombre_canonico}"?` : "";
      out.innerHTML = `<span class="chip bad">No encontrado.${sug}</span>`;
    }
  });

  // --- Enseñar equivalencia ---
  $("btn-eq").addEventListener("click", async () => {
    const payload = {
      dominio: $("eq-dominio").value,
      variante: $("eq-variante").value.trim(),
      canonico: $("eq-canonico").value.trim().toUpperCase(),
    };
    if (!payload.variante || !payload.canonico) { toast("Variante y canónico requeridos", true); return; }
    const res = await (await fetch("/api/homologar/equivalencia", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })).json();
    if (res.ok) { toast("Equivalencia guardada"); $("eq-variante").value = ""; $("eq-canonico").value = ""; }
    else toast("No se pudo guardar", true);
  });

  // --- Listar maestros ---
  async function cargarMaestros() {
    const dominio = $("m-dominio").value;
    const ms = await (await fetch("/api/mdm/maestros?dominio=" + dominio)).json();
    const tb = $("tbody-maestros");
    tb.innerHTML = ms.length
      ? ms.map((m) => `<tr><td>${m.id}</td><td>${m.codigo || "—"}</td>
          <td>${m.nombre_canonico}</td><td>${m.area_propietaria || "—"}</td><td>${m.estado}</td></tr>`).join("")
      : '<tr><td colspan="5" class="hint">Sin maestros.</td></tr>';
  }
  $("m-dominio").addEventListener("change", cargarMaestros);
  cargarMaestros();

  // ===== Catálogo: editar / eliminar =====
  const CAT_API = { responsables: "/api/responsables", obras: "/api/obras", items: "/api/items", cc: "/api/cc" };
  const CAT_CAMPO = { responsables: "nombre", obras: "nombre", items: "nombre", cc: "contrato" };

  async function cargarCatalogo() {
    const tipo = $("ce-tipo").value;
    const rows = await (await fetch(CAT_API[tipo])).json();
    const campo = CAT_CAMPO[tipo];
    const tb = $("tbody-catalogo");
    tb.innerHTML = rows.length ? rows.map((r) => `
      <tr data-id="${r.id}">
        <td>${r.id}</td><td>${r[campo]}</td>
        <td>
          <button class="btn ghost" data-acc="editar" data-id="${r.id}" data-nombre="${r[campo]}">Editar</button>
          <button class="btn ghost" data-acc="eliminar" data-id="${r.id}">Eliminar</button>
        </td>
      </tr>`).join("") : '<tr><td colspan="3" class="hint">Vacío.</td></tr>';
  }

  $("tbody-catalogo").addEventListener("click", async (e) => {
    const btn = e.target.closest("button"); if (!btn) return;
    const tipo = $("ce-tipo").value, id = btn.dataset.id;
    if (btn.dataset.acc === "editar") {
      const nuevo = prompt("Nuevo nombre:", btn.dataset.nombre);
      if (!nuevo) return;
      const res = await (await fetch(`/api/catalogo/${tipo}/${id}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre: nuevo }),
      })).json();
      if (res.ok) { toast("Actualizado"); cargarCatalogo(); } else toast(res.error || "Error", true);
    } else if (btn.dataset.acc === "eliminar") {
      if (!confirm("¿Eliminar esta entrada?")) return;
      const r = await fetch(`/api/catalogo/${tipo}/${id}`, { method: "DELETE" });
      const res = await r.json();
      if (res.ok) { toast("Eliminado"); cargarCatalogo(); } else toast(res.error || "No se pudo eliminar", true);
    }
  });
  $("ce-tipo").addEventListener("change", cargarCatalogo);
  cargarCatalogo();

  // ===== Usuarios =====
  async function cargarUsuarios() {
    const us = await (await fetch("/api/usuarios")).json();
    $("tbody-usuarios").innerHTML = us.map((u) => `
      <tr><td>${u.usuario}<br><span class="hint">${u.nombre || ""}</span></td>
        <td>${u.rol}</td>
        <td>${u.activo ? '<span class="chip ok">activo</span>' : '<span class="chip bad">inactivo</span>'}</td>
        <td><button class="btn ghost" data-uid="${u.id}" data-activo="${u.activo}">${u.activo ? "Desactivar" : "Activar"}</button></td>
      </tr>`).join("");
  }
  $("btn-usuario").addEventListener("click", async () => {
    const payload = {
      usuario: $("u-usuario").value.trim(), nombre: $("u-nombre").value.trim(),
      password: $("u-pass").value, rol: $("u-rol").value,
    };
    if (!payload.usuario || !payload.password) { toast("Usuario y contraseña requeridos", true); return; }
    const res = await (await fetch("/api/usuarios", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    })).json();
    if (res.ok) { toast("Usuario creado"); ["u-usuario", "u-nombre", "u-pass"].forEach((id) => $(id).value = ""); cargarUsuarios(); }
    else toast(res.error || "No se pudo crear", true);
  });
  $("tbody-usuarios").addEventListener("click", async (e) => {
    const btn = e.target.closest("button"); if (!btn) return;
    const activo = btn.dataset.activo === "1";
    await fetch(`/api/usuarios/${btn.dataset.uid}/estado`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activo: !activo }),
    });
    toast("Estado actualizado"); cargarUsuarios();
  });
  cargarUsuarios();

  // ===== MDM crear maestro / alias =====
  $("btn-maestro-crear").addEventListener("click", async () => {
    const payload = {
      dominio: $("mc-dominio").value, nombre: $("mc-nombre").value.trim(),
      area_actor: $("mc-area").value.trim().toLowerCase(),
    };
    if (!payload.nombre || !payload.area_actor) { toast("Nombre y área requeridos", true); return; }
    const r = await fetch("/api/mdm/maestros", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    const res = await r.json();
    if (res.ok) { toast("Maestro creado #" + res.master_id); $("mc-nombre").value = ""; cargarMaestros(); }
    else toast(res.error || "No se pudo crear", true);
  });
  $("btn-alias").addEventListener("click", async () => {
    const payload = {
      dominio: $("mc-dominio").value, master_id: Number($("al-master").value),
      alias: $("al-alias").value.trim(), area_actor: $("mc-area").value.trim().toLowerCase() || null,
    };
    if (!payload.master_id || !payload.alias) { toast("ID maestro y alias requeridos", true); return; }
    const r = await fetch("/api/mdm/alias", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    const res = await r.json();
    if (res.ok) { toast("Alias agregado"); $("al-alias").value = ""; } else toast(res.error || "Error", true);
  });

  // ===== Permisos =====
  async function cargarPermisos() {
    const ps = await (await fetch("/api/mdm/permisos")).json();
    $("tbody-permisos").innerHTML = ps.length ? ps.map((p) => `
      <tr><td>${p.area}</td><td>${p.dominio}</td>
        <td>${p.puede_crear ? "✔" : "—"}</td><td>${p.puede_editar ? "✔" : "—"}</td></tr>`).join("")
      : '<tr><td colspan="4" class="hint">—</td></tr>';
  }
  $("btn-permiso").addEventListener("click", async () => {
    const payload = {
      area: $("p-area").value.trim().toLowerCase(), dominio: $("p-dominio").value,
      puede_crear: $("p-crear").checked, puede_editar: $("p-editar").checked,
    };
    if (!payload.area) { toast("Área requerida", true); return; }
    const res = await (await fetch("/api/mdm/permisos", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    })).json();
    if (res.ok) { toast("Permiso guardado"); cargarPermisos(); } else toast(res.error || "Error", true);
  });
  cargarPermisos();
})();
