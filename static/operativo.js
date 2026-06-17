// operativo.js — captura rápida con homologación, autocompletar y validación inline.
(function () {
  const $ = (id) => document.getElementById(id);
  const form = $("form-mov");
  const btn = $("btn-guardar");

  // Mapa nombre->id de items para resolver lo que escribe el digitador.
  const itemsPorNombre = {};
  document.querySelectorAll("#lista-items option").forEach((o) => {
    itemsPorNombre[o.value.trim().toUpperCase()] = o.value.trim();
  });

  // Fecha por defecto = hoy.
  $("fecha").value = window.HOY;

  // --- Homologación en vivo del ítem ---
  let homologarTimer = null;
  const itemInput = $("item_texto");
  const hint = $("homologacion-hint");

  itemInput.addEventListener("input", () => {
    const texto = itemInput.value.trim();
    // resolver item_id si coincide exacto con un catálogo
    const exacto = itemsPorNombre[texto.toUpperCase()];
    $("item_id").value = "";
    clearTimeout(homologarTimer);
    if (!texto) { hint.className = "hint"; hint.textContent = "Escribe el concepto; se homologa solo."; validar(); return; }
    homologarTimer = setTimeout(async () => {
      try {
        const r = await fetch(`/api/homologar?dominio=item&texto=${encodeURIComponent(texto)}`);
        const h = await r.json();
        const cls = h.score >= 1 ? "ok" : (h.score >= 0.7 ? "warn" : "bad");
        const etiqueta = h.score >= 1 ? "validado" : (h.score >= 0.7 ? "inferido" : "sin coincidencia");
        hint.innerHTML = `<span class="chip ${cls}">→ ${h.canonico || "?"} · ${etiqueta} (${h.score})</span>`;
      } catch (e) { hint.textContent = "(no se pudo homologar)"; }
      validar();
    }, 250);
    validar();
  });

  // --- Validación inline ---
  const monto = $("monto");
  monto.addEventListener("input", () => {
    monto.value = monto.value.replace(/[^\d]/g, "");
    $("monto-hint").textContent = monto.value ? pesos(monto.value) : "";
    validar();
  });
  ["responsable_id", "tipo_id", "fecha"].forEach((id) => $(id).addEventListener("change", validar));

  function validar() {
    const ok = $("responsable_id").value && $("tipo_id").value &&
               monto.value && Number(monto.value) > 0 && $("fecha").value;
    btn.disabled = !ok;
    monto.classList.toggle("invalid", !!monto.value && Number(monto.value) <= 0);
    return ok;
  }

  // Cargar items con id una vez para mapear nombre->id real.
  let itemsCatalogo = [];
  fetch("/api/items").then(r => r.json()).then(d => { itemsCatalogo = d; });

  function itemIdDeTexto() {
    const t = itemInput.value.trim().toUpperCase();
    const m = itemsCatalogo.find((i) => (i.nombre || "").toUpperCase() === t);
    return m ? m.id : null;
  }

  // --- Envío ---
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!validar()) return;
    btn.disabled = true;
    const payload = {
      responsable_id: Number($("responsable_id").value),
      tipo_id: Number($("tipo_id").value),
      cc_id: $("cc_id").value ? Number($("cc_id").value) : null,
      obra_id: $("obra_id").value ? Number($("obra_id").value) : null,
      item_id: itemIdDeTexto(),
      monto: Number(monto.value),
      fecha: $("fecha").value,
      observacion: $("observacion").value || itemInput.value || null,
      soporte: $("soporte").value || null,
    };
    try {
      const r = await fetch("/api/movimientos", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const res = await r.json();
      if (res.ok) {
        toast(`Recibo ${res.recibo} registrado · homologado a ${res.homologacion.canonico}`);
        limpiar();
        cargarUltimos();
        poblarProduccion();
      } else {
        toast(res.error || "No se pudo registrar", true);
        btn.disabled = false;
      }
    } catch (err) { toast("Error de red", true); btn.disabled = false; }
  });

  $("btn-limpiar").addEventListener("click", limpiar);
  function limpiar() {
    ["item_texto", "monto", "soporte", "observacion"].forEach((id) => $(id).value = "");
    $("monto-hint").textContent = "";
    hint.className = "hint"; hint.textContent = "Escribe el concepto; se homologa solo.";
    validar();
  }

  // --- Últimos movimientos ---
  async function cargarUltimos() {
    try {
      const r = await fetch("/api/movimientos");
      const movs = await r.json();
      const ult = movs.slice(-10).reverse();
      const tb = $("tbody-mov");
      if (!ult.length) { tb.innerHTML = '<tr><td colspan="6" class="hint">Sin movimientos.</td></tr>'; return; }
      tb.innerHTML = ult.map((m) => `
        <tr>
          <td>${m.recibo}</td><td>${m.fecha_movimiento || ""}</td>
          <td>${m.responsable || ""}</td><td>${m.tipo || ""}</td>
          <td>${m.item || "—"}</td><td class="num">${pesos(m.monto)}</td>
        </tr>`).join("");
    } catch (e) { /* noop */ }
  }
  // ===== Producción (unidades ejecutadas) =====
  $("prod-fecha").value = window.HOY;
  const prodMov = $("prod-mov");
  const prodUni = $("prod-unidad");
  const btnProd = $("btn-prod");

  async function poblarProduccion() {
    const [movs, unis] = await Promise.all([
      fetch("/api/movimientos").then((r) => r.json()),
      fetch("/api/unidades-constructivas").then((r) => r.json()),
    ]);
    prodMov.innerHTML = '<option value="">— Seleccione un recibo —</option>' +
      movs.slice(-30).reverse().map((m) =>
        `<option value="${m.id}">Recibo ${m.recibo} · ${m.fecha_movimiento || ""} · ${m.item || m.tipo || ""}</option>`).join("");
    prodUni.innerHTML = '<option value="">— Seleccione —</option>' +
      unis.map((u) => `<option value="${u.id}">${u.nombre}</option>`).join("");
  }

  function validarProd() {
    const ok = prodMov.value && prodUni.value &&
               $("prod-cantidad").value && Number($("prod-cantidad").value) > 0 &&
               $("prod-fecha").value;
    btnProd.disabled = !ok;
    return ok;
  }
  ["prod-mov", "prod-unidad", "prod-cantidad", "prod-fecha"].forEach((id) =>
    $(id).addEventListener("input", validarProd));

  $("form-prod").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!validarProd()) return;
    btnProd.disabled = true;
    const payload = {
      movimiento_id: Number(prodMov.value),
      unidad_constructiva_id: Number(prodUni.value),
      cantidad: Number($("prod-cantidad").value),
      fecha: $("prod-fecha").value,
      observacion: $("prod-obs").value || null,
    };
    try {
      const res = await (await fetch("/api/unidades-ejecutadas", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })).json();
      if (res.ok) {
        toast("Producción registrada");
        ["prod-cantidad", "prod-obs"].forEach((id) => $(id).value = "");
        validarProd();
      } else { toast(res.error || "No se pudo registrar", true); btnProd.disabled = false; }
    } catch (err) { toast("Error de red", true); btnProd.disabled = false; }
  });

  poblarProduccion();
  cargarUltimos();
})();
