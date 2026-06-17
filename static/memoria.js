// memoria.js — consulta en lenguaje natural + reconstrucción narrativa + export.
(function () {
  const $ = (id) => document.getElementById(id);

  async function preguntar() {
    const q = $("q").value.trim();
    if (!q) return;
    const res = await (await fetch("/api/memoria/consultar?q=" + encodeURIComponent(q))).json();
    $("respuesta").style.display = "block";
    $("resp-texto").textContent = res.respuesta || "Sin respuesta.";
    const meta = [];
    if (res.intencion) meta.push("intención: " + res.intencion);
    if (res.contrato) meta.push("contrato: " + res.contrato.nombre);
    if (res.periodo) meta.push(`periodo: ${res.periodo.ini || "?"} → ${res.periodo.fin || "?"}`);
    $("resp-meta").textContent = meta.join("  ·  ");
  }
  $("btn-preguntar").addEventListener("click", preguntar);
  $("q").addEventListener("keydown", (e) => { if (e.key === "Enter") preguntar(); });
  document.querySelectorAll("[data-ej]").forEach((b) =>
    b.addEventListener("click", () => { $("q").value = b.dataset.ej; preguntar(); }));

  // --- Narrativa + export ---
  function filtros() {
    const p = new URLSearchParams();
    if ($("m-contrato").value) p.set("contrato_id", $("m-contrato").value);
    if ($("m-ini").value) p.set("fecha_ini", $("m-ini").value);
    if ($("m-fin").value) p.set("fecha_fin", $("m-fin").value);
    return p;
  }
  async function narrar() {
    const res = await (await fetch("/api/memoria/narrativa?" + filtros().toString())).json();
    $("narrativa").textContent = res.narrativa || "Sin datos.";
  }
  function actualizarExport() {
    const q = filtros().toString();
    $("exp-md").href = "/api/memoria/exportar?formato=md&" + q;
    $("exp-json").href = "/api/memoria/exportar?formato=json&" + q;
  }
  $("btn-narrar").addEventListener("click", () => { narrar(); actualizarExport(); });
  ["m-contrato", "m-ini", "m-fin"].forEach((id) => $(id).addEventListener("change", actualizarExport));
  actualizarExport();
})();
