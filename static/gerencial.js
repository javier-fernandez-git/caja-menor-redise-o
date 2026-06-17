// gerencial.js — tablero gerencial, causal, alertas y enlaces a PDF.
(function () {
  const $ = (id) => document.getElementById(id);

  function filtros() {
    const p = new URLSearchParams();
    if ($("f-contrato").value) p.set("contrato_id", $("f-contrato").value);
    if ($("f-cc").value) p.set("centro_costo_id", $("f-cc").value);
    if ($("f-ini").value) p.set("fecha_ini", $("f-ini").value);
    if ($("f-fin").value) p.set("fecha_fin", $("f-fin").value);
    return p;
  }

  async function cargarTablero() {
    const p = filtros();
    if ($("f-valor").value) p.set("valor_contrato", $("f-valor").value.replace(/\D/g, ""));
    if ($("f-dias").value) p.set("duracion_dias", $("f-dias").value.replace(/\D/g, ""));
    const t = await (await fetch("/api/tablero?" + p.toString())).json();

    $("k-caja").textContent = pesos(t.caja.saldo);
    $("k-obra").textContent = pesos(t.costo_obra);
    $("k-util").textContent = t.utilidad_estimada != null ? pesos(t.utilidad_estimada) : "n/d";
    $("k-alert").textContent = t.total_alertas;

    $("tbody-top").innerHTML = (t.top_gastos || []).length
      ? t.top_gastos.map((g) => `<tr><td>${g.item}</td><td class="num">${pesos(g.valor)}</td></tr>`).join("")
      : '<tr><td colspan="2" class="hint">Sin gastos.</td></tr>';

    const c = t.confiabilidad || {};
    $("tbody-conf").innerHTML = `
      <tr><td>Validados</td><td class="num">${c.validados ?? 0} (${c.pct_validados ?? 0}%)</td></tr>
      <tr><td>Inferidos</td><td class="num">${c.inferidos ?? 0}</td></tr>
      <tr><td>Sospechosos</td><td class="num">${c.sospechosos ?? 0} (${c.pct_sospechosos ?? 0}%)</td></tr>`;

    $("tbody-alert").innerHTML = (t.alertas || []).length
      ? t.alertas.map((a) => `<tr><td>${a.fecha}</td><td>${a.item}</td>
          <td class="num">${pesos(a.valor)}</td><td class="num">${pesos(a.umbral)}</td>
          <td class="num">${pesos(a.exceso)}</td></tr>`).join("")
      : '<tr><td colspan="5" class="hint">Sin alertas en el periodo.</td></tr>';
  }

  async function cargarCausal() {
    const p = new URLSearchParams();
    if ($("f-contrato").value) p.set("contrato_id", $("f-contrato").value);
    if ($("f-cc").value) p.set("centro_costo_id", $("f-cc").value);
    try {
      const c = await (await fetch("/api/causal?" + p.toString())).json();
      $("causal-resumen").textContent = c.resumen || "Sin datos suficientes.";
    } catch (e) { $("causal-resumen").textContent = "No disponible."; }
  }

  function actualizarPDFs() {
    const q = filtros().toString();
    $("pdf-fin").href = "/api/reportes/financiero.pdf?" + q;
    $("pdf-trz").href = "/api/reportes/trazabilidad.pdf?" + q;

    const liq = $("pdf-liq");
    const resp = $("f-responsable").value;
    if (resp) {
      const lp = filtros();
      lp.set("responsable_id", resp);
      liq.href = "/api/reportes/liquidacion.pdf?" + lp.toString();
      liq.style.pointerEvents = ""; liq.style.opacity = "";
      liq.title = "Liquidación del responsable seleccionado";
    } else {
      liq.removeAttribute("href");
      liq.style.pointerEvents = "none"; liq.style.opacity = ".5";
      liq.title = "Selecciona un responsable para habilitar la liquidación";
    }
  }

  function aplicar() { cargarTablero(); cargarCausal(); actualizarPDFs(); }
  $("btn-aplicar").addEventListener("click", aplicar);
  $("f-responsable").addEventListener("change", actualizarPDFs);
  aplicar();
})();
