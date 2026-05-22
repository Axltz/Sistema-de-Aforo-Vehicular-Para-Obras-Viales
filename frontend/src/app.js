// ================================================================
// AFORO VEHICULAR — DASHBOARD APP.JS (VERSIÓN 100% LOCAL & OFFLINE)
// ================================================================
// Polling local de JSON/JSONL + Chart.js + Compresión Huffman + UI
// ================================================================

// ===== STATE =====
const state = {
  metricsHistory: [],     // Historial de métricas locales
  activeChart: "flow",    // flow | density | vehicles
  sparkData: { total: [], scene: [], flow: [] },
  lastHuffmanBlob: null,
};

let lastMetricId = null;  // Para evitar redibujar datos idénticos

// ===== DOM REFERENCES =====
const $ = (id) => document.getElementById(id);

const dom = {
  totalCount:     $("val-total-count"),
  vehiclesScene:  $("val-vehicles-scene"),
  flowRate:       $("val-flow-rate"),
  interaction:    $("val-interaction"),
  trafficState:   $("val-traffic-state"),
  flowBehavior:   $("val-flow-behavior"),
  progressBar:    $("progress-interaction"),
  alertBanner:    $("alert-banner"),
  clustersBox:    $("clusters-container"),
  metricsTbody:   $("metrics-tbody"),
  connStatus:     $("connection-status"),
  connText:       document.querySelector("#connection-status .status-text"),
  clock:          $("clock"),
  fileInput:      $("video-file-input"),
  fileInputText:  $("file-input-text"),
};

// ===== CLOCK =====
function updateClock() {
  const now = new Date();
  dom.clock.textContent = now.toLocaleTimeString("es-MX", { hour12: false });
}
setInterval(updateClock, 1000);
updateClock();

// ===== PARTICLE BACKGROUND =====
(function initParticles() {
  const canvas = $("particle-canvas");
  const ctx = canvas.getContext("2d");
  let particles = [];
  const COUNT = 60;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function createParticle() {
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.5 + 0.1,
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: COUNT }, createParticle);
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0, 168, 255, ${p.alpha})`;
      ctx.fill();
    }
    // Conexiones de partículas
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0, 168, 255, ${0.08 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }

  window.addEventListener("resize", resize);
  init();
  draw();
})();

// ===== CHART.JS SETUP =====
const chartColors = {
  flow:     { border: "#00e5ff", bg: "rgba(0,229,255,0.1)" },
  density:  { border: "#7b2dff", bg: "rgba(123,45,255,0.1)" },
  vehicles: { border: "#00e676", bg: "rgba(0,230,118,0.1)" },
};

const mainChartCtx = $("main-chart").getContext("2d");
const mainChart = new Chart(mainChartCtx, {
  type: "line",
  data: {
    labels: [],
    datasets: [{
      label: "Flujo (veh/min)",
      data: [],
      borderColor: chartColors.flow.border,
      backgroundColor: chartColors.flow.bg,
      borderWidth: 2,
      tension: 0.4,
      fill: true,
      pointRadius: 2,
      pointHoverRadius: 5,
      pointBackgroundColor: chartColors.flow.border,
    }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 400 },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(10,10,15,0.9)",
        borderColor: "rgba(0,168,255,0.3)",
        borderWidth: 1,
        titleFont: { family: "Orbitron", size: 10 },
        bodyFont: { family: "JetBrains Mono", size: 11 },
      },
    },
    scales: {
      x: {
        grid: { color: "rgba(255,255,255,0.03)" },
        ticks: { color: "#4a5568", font: { family: "JetBrains Mono", size: 9 }, maxTicksLimit: 10 },
      },
      y: {
        grid: { color: "rgba(255,255,255,0.03)" },
        ticks: { color: "#4a5568", font: { family: "JetBrains Mono", size: 9 } },
        beginAtZero: true,
      },
    },
  },
});

// Gráfico de Barras de Horas Pico (NUEVO)
const hoursChartCtx = $("hours-chart").getContext("2d");
const hoursChart = new Chart(hoursChartCtx, {
  type: "bar",
  data: {
    labels: Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`),
    datasets: [{
      label: "Vehículos Aforados",
      data: Array(24).fill(0),
      backgroundColor: "rgba(0, 229, 255, 0.25)",
      borderColor: "#00e5ff",
      borderWidth: 1.5,
      borderRadius: 4,
      hoverBackgroundColor: "rgba(0, 229, 255, 0.45)",
    }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(10,10,15,0.9)",
        borderColor: "rgba(0,168,255,0.3)",
        borderWidth: 1,
        titleFont: { family: "Orbitron", size: 10 },
        bodyFont: { family: "JetBrains Mono", size: 11 },
      },
    },
    scales: {
      x: {
        grid: { color: "rgba(255,255,255,0.02)" },
        ticks: { color: "#4a5568", font: { family: "JetBrains Mono", size: 8 } },
      },
      y: {
        grid: { color: "rgba(255,255,255,0.02)" },
        ticks: { color: "#4a5568", font: { family: "JetBrains Mono", size: 8 }, stepSize: 1 },
        beginAtZero: true,
      },
    },
  },
});

// Gráfico de agrupaciones (Rosquilla)
const clusterChartCtx = $("cluster-chart").getContext("2d");
const clusterChart = new Chart(clusterChartCtx, {
  type: "doughnut",
  data: {
    labels: ["Sin riesgo"],
    datasets: [{
      data: [1],
      backgroundColor: ["rgba(0,229,255,0.2)"],
      borderColor: ["rgba(0,229,255,0.5)"],
      borderWidth: 1,
    }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "65%",
    plugins: {
      legend: {
        position: "bottom",
        labels: { color: "#8892b0", font: { size: 10 }, padding: 8, boxWidth: 12 },
      },
    },
  },
});

// Sparkline factory
function createSparkline(canvasId, color) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  return new Chart(ctx, {
    type: "line",
    data: { labels: [], datasets: [{ data: [], borderColor: color, borderWidth: 1.5, tension: 0.4, pointRadius: 0, fill: false }] },
    options: {
      responsive: false,
      animation: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: { x: { display: false }, y: { display: false } },
    },
  });
}

const sparkTotal = createSparkline("spark-total", "#00a8ff");
const sparkScene = createSparkline("spark-scene", "#00e5ff");
const sparkFlow  = createSparkline("spark-flow",  "#00e676");

function updateSparkline(chart, dataArr, value) {
  dataArr.push(value);
  if (dataArr.length > 20) dataArr.shift();
  chart.data.labels = dataArr.map((_, i) => i);
  chart.data.datasets[0].data = [...dataArr];
  chart.update("none");
}

// ===== CHART SWITCHER =====
document.querySelectorAll(".btn-chart").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".btn-chart").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.activeChart = btn.dataset.chart;
    rebuildMainChart();
  });
});

function rebuildMainChart() {
  const type = state.activeChart;
  const colors = chartColors[type];
  const labelMap = { flow: "Flujo (veh/min)", density: "Interacción %", vehicles: "Vehículos en escena" };
  const dataKeyMap = { flow: "flujo_por_minuto", density: "interaccion_pct", vehicles: "total_vehicles" };

  mainChart.data.labels = state.metricsHistory.map((m) => {
    const d = new Date(m.ts);
    return d.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  });
  mainChart.data.datasets[0].label = labelMap[type];
  mainChart.data.datasets[0].data = state.metricsHistory.map((m) => {
    const d = m.data || {};
    return d[dataKeyMap[type]] ?? 0;
  });
  mainChart.data.datasets[0].borderColor = colors.border;
  mainChart.data.datasets[0].backgroundColor = colors.bg;
  mainChart.data.datasets[0].pointBackgroundColor = colors.border;
  mainChart.update();
}

// ===== CÁLCULO DE HORAS PICO =====
function updateHoursChart() {
  const hourlyVolume = {};
  for (let h = 0; h < 24; h++) {
    hourlyVolume[h] = 0;
  }

  let prevCount = null;
  state.metricsHistory.forEach((row) => {
    if (prevCount === null) {
      prevCount = row.total_count ?? 0;
      return;
    }
    const diff = (row.total_count ?? 0) - prevCount;
    // Si hay un incremento real (sin contar caídas de reinicio de video)
    if (diff > 0) {
      const hour = new Date(row.ts).getHours();
      hourlyVolume[hour] = (hourlyVolume[hour] || 0) + diff;
    }
    prevCount = row.total_count ?? 0;
  });

  hoursChart.data.datasets[0].data = Array.from({ length: 24 }, (_, h) => hourlyVolume[h]);
  hoursChart.update();
}

// ===== UI UPDATE =====
function updateDashboard(row) {
  const d = row.data || {};

  // Cards
  dom.totalCount.textContent    = row.total_count ?? 0;
  dom.vehiclesScene.textContent = d.total_vehicles ?? 0;
  dom.flowRate.textContent      = (d.flujo_por_minuto ?? 0).toFixed(1);
  dom.interaction.textContent   = `${(d.interaccion_pct ?? 0).toFixed(1)}%`;
  dom.trafficState.textContent  = d.fluidez_avance ?? "—";
  dom.flowBehavior.textContent  = d.velocidad_marcha ?? "—";

  // Progress bar
  const pct = Math.min(100, d.interaccion_pct ?? 0);
  dom.progressBar.style.width = `${pct}%`;

  // Colorear estado de la vía
  const stateEl = dom.trafficState;
  stateEl.style.setProperty("-webkit-text-fill-color", "");
  if ((d.fluidez_avance || "").includes("CONGESTION") || (d.fluidez_avance || "").includes("EMBOTELLAMIENTO")) {
    stateEl.style.color = "#ff3d3d";
    stateEl.style.setProperty("-webkit-text-fill-color", "#ff3d3d");
  } else if ((d.fluidez_avance || "").includes("LIBRE")) {
    stateEl.style.color = "#00e676";
    stateEl.style.setProperty("-webkit-text-fill-color", "#00e676");
  } else {
    stateEl.style.color = "#00e5ff";
    stateEl.style.setProperty("-webkit-text-fill-color", "#00e5ff");
  }

  // Alerta de embotellamiento
  if (d.alerta_embotellamiento) {
    dom.alertBanner.classList.remove("hidden");
  } else {
    dom.alertBanner.classList.add("hidden");
  }

  // Clusters
  const clusters = d.cluster_metrics || [];
  if (clusters.length === 0) {
    dom.clustersBox.innerHTML = `
      <div class="cluster-empty">
        <span class="cluster-empty-icon">✅</span>
        <span>Sin agrupaciones de riesgo</span>
      </div>`;
  } else {
    dom.clustersBox.innerHTML = clusters.map((c) => `
      <div class="cluster-item ${c.riesgo === 'ALTO' ? 'danger' : ''}">
        <span class="cluster-name">${c.nombre}</span>
        <span class="cluster-count">${c.conteo} veh</span>
        <span class="cluster-risk ${c.riesgo === 'ALTO' ? 'high' : 'low'}">${c.riesgo}</span>
      </div>
    `).join("");
  }

  // Clusters Doughnut Chart
  const clLabels = clusters.length ? clusters.map((c) => c.nombre) : ["Sin riesgo"];
  const clData   = clusters.length ? clusters.map((c) => c.conteo) : [1];
  const clColors = clusters.map((c) =>
    c.riesgo === "ALTO" ? "rgba(255,61,61,0.4)" : "rgba(0,168,255,0.3)"
  );
  clusterChart.data.labels = clLabels;
  clusterChart.data.datasets[0].data = clData;
  clusterChart.data.datasets[0].backgroundColor = clusters.length ? clColors : ["rgba(0,229,255,0.2)"];
  clusterChart.data.datasets[0].borderColor = clusters.length ? clColors.map((c) => c.replace("0.4", "0.7").replace("0.3", "0.6")) : ["rgba(0,229,255,0.5)"];
  clusterChart.update();

  // Sparklines
  updateSparkline(sparkTotal, state.sparkData.total, row.total_count ?? 0);
  updateSparkline(sparkScene, state.sparkData.scene, d.total_vehicles ?? 0);
  updateSparkline(sparkFlow,  state.sparkData.flow,  d.flujo_por_minuto ?? 0);
}

function addTableRow(row) {
  const d = row.data || {};
  const ts = new Date(row.ts).toLocaleString("es-MX", { hour12: false });
  const alertEmoji = d.alerta_embotellamiento ? "🚨 SÍ" : "✅ No";
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${ts}</td>
    <td>${row.total_count ?? 0}</td>
    <td>${d.total_vehicles ?? 0}</td>
    <td>${(d.flujo_por_minuto ?? 0).toFixed(1)}</td>
    <td>${(d.interaccion_pct ?? 0).toFixed(1)}%</td>
    <td>${d.fluidez_avance ?? "—"}</td>
    <td>${alertEmoji}</td>
  `;
  
  const emptyRow = dom.metricsTbody.querySelector(".empty-row");
  if (emptyRow) emptyRow.remove();
  dom.metricsTbody.prepend(tr);
  
  // Límite de 50 filas
  while (dom.metricsTbody.children.length > 50) {
    dom.metricsTbody.removeChild(dom.metricsTbody.lastChild);
  }
}

// ===== LOCAL DATA POLLING & FETCH =====

function getDailyLogPath() {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  return `../../data/logs/metrics_${yyyy}-${mm}-${dd}.jsonl`;
}

// Carga inicial del historial del día desde el .jsonl local
async function fetchDailyLog() {
  const path = getDailyLogPath();
  try {
    const response = await fetch(path);
    if (!response.ok) {
      console.warn("Aún no hay log histórico acumulado para hoy en:", path);
      return;
    }
    const text = await response.text();
    
    // Parsear líneas de JSONL
    const lines = text.split("\n");
    const history = [];
    for (const line of lines) {
      if (line.trim()) {
        try {
          const row = JSON.parse(line);
          history.push(row);
        } catch (e) {
          // Ignorar filas incompletas
        }
      }
    }
    
    state.metricsHistory = history;
    
    // Repoblar la tabla
    dom.metricsTbody.innerHTML = "";
    const reversed = [...history].reverse();
    for (const row of reversed) {
      addTableRow(row);
    }
    
    // Rellenar sparklines iniciales
    state.sparkData = { total: [], scene: [], flow: [] };
    const sparkHistory = history.slice(-20);
    sparkHistory.forEach((row) => {
      const d = row.data || {};
      state.sparkData.total.push(row.total_count ?? 0);
      state.sparkData.scene.push(d.total_vehicles ?? 0);
      state.sparkData.flow.push(d.flujo_por_minuto ?? 0);
    });
    
    rebuildMainChart();
    updateHoursChart();
    setConnected(true);
  } catch (err) {
    console.warn("Error cargando historial local:", err.message);
  }
}

// Polling periódico del JSON live en tiempo real
async function pollLiveMetrics() {
  try {
    const response = await fetch("../../data/metrics_live.json?t=" + Date.now());
    if (!response.ok) throw new Error("Archivo live no disponible");
    const row = await response.json();
    
    // Actualizar solo ante nuevos IDs
    if (row && row.id !== lastMetricId) {
      lastMetricId = row.id;
      
      updateDashboard(row);
      addTableRow(row);
      
      state.metricsHistory.push(row);
      if (state.metricsHistory.length > 200) state.metricsHistory.shift();
      
      rebuildMainChart();
      updateHoursChart();
      setConnected(true);
    }
  } catch (err) {
    setConnected(false, "Buscando backend...");
  }
}

function setConnected(ok, errMsg) {
  dom.connStatus.className = "status-indicator " + (ok ? "connected" : "error");
  dom.connText.textContent = ok ? "Servidor Local" : (errMsg || "Error");
}

// ===== VIDEO SOURCE SELECTOR =====
document.querySelectorAll(".btn-source").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".btn-source").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const src = btn.dataset.source;
    $("source-config-preloaded").classList.toggle("hidden", src !== "preloaded");
    $("source-config-stream").classList.toggle("hidden", src !== "stream");
  });
});

dom.fileInput.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (file) {
    dom.fileInputText.textContent = `📁 ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
    dom.fileInputText.style.color = "#00e5ff";
    alert(`Nota: Para procesar '${file.name}', cópialo a 'data/videos/' y ejecuta en tu terminal:\n\npython src/main.py --video data/videos/${file.name}`);
  }
});

$("btn-connect-stream").addEventListener("click", () => {
  const url = $("stream-url-input").value.trim();
  if (!url) return alert("Ingresa una URL de stream válida");
  alert(`Cámara IP configurada.\n\nPara conectarla, abre una terminal y ejecuta:\n\npython src/main.py --video "${url}"`);
});

// ===== EXPORT JSON =====
$("btn-export-json").addEventListener("click", () => {
  if (state.metricsHistory.length === 0) return alert("No hay datos para exportar.");
  const json = JSON.stringify(state.metricsHistory, null, 2);
  downloadFile(json, "aforo_vehicular_data.json", "application/json");
});

// ===== REFRESH DATA =====
$("btn-refresh-data").addEventListener("click", () => {
  dom.metricsTbody.innerHTML = `<tr class="empty-row"><td colspan="7">Cargando datos locales...</td></tr>`;
  state.metricsHistory = [];
  state.sparkData = { total: [], scene: [], flow: [] };
  fetchDailyLog();
});

// ===== HUFFMAN COMPRESSION =====
class HuffmanNode {
  constructor(char, freq, left = null, right = null) {
    this.char = char;
    this.freq = freq;
    this.left = left;
    this.right = right;
  }
}

function buildHuffmanTree(text) {
  const freq = {};
  for (const ch of text) {
    freq[ch] = (freq[ch] || 0) + 1;
  }

  let nodes = Object.entries(freq).map(([ch, f]) => new HuffmanNode(ch, f));
  
  if (nodes.length === 0) return { root: null, codes: {}, freq: {} };
  if (nodes.length === 1) {
    const root = new HuffmanNode(null, nodes[0].freq, nodes[0]);
    return { root, codes: { [nodes[0].char]: "0" }, freq };
  }

  while (nodes.length > 1) {
    nodes.sort((a, b) => a.freq - b.freq);
    const left = nodes.shift();
    const right = nodes.shift();
    const parent = new HuffmanNode(null, left.freq + right.freq, left, right);
    nodes.push(parent);
  }

  const codes = {};
  function traverse(node, code) {
    if (!node) return;
    if (node.char !== null) {
      codes[node.char] = code || "0";
      return;
    }
    traverse(node.left, code + "0");
    traverse(node.right, code + "1");
  }
  traverse(nodes[0], "");

  return { root: nodes[0], codes, freq };
}

function huffmanEncode(text) {
  const { codes, freq } = buildHuffmanTree(text);
  
  let binaryStr = "";
  for (const ch of text) {
    binaryStr += codes[ch];
  }

  const paddingBits = (8 - (binaryStr.length % 8)) % 8;
  binaryStr += "0".repeat(paddingBits);

  const bytes = new Uint8Array(binaryStr.length / 8);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(binaryStr.substring(i * 8, (i + 1) * 8), 2);
  }

  const header = JSON.stringify({ codes, padding: paddingBits });
  const headerBytes = new TextEncoder().encode(header);

  const headerLen = new Uint32Array([headerBytes.length]);
  const headerLenBytes = new Uint8Array(headerLen.buffer);

  const result = new Uint8Array(4 + headerBytes.length + bytes.length);
  result.set(headerLenBytes, 0);
  result.set(headerBytes, 4);
  result.set(bytes, 4 + headerBytes.length);

  return {
    compressed: result,
    originalSize: new TextEncoder().encode(text).length,
    compressedSize: result.length,
    ratio: (result.length / new TextEncoder().encode(text).length * 100).toFixed(1),
    symbolCount: Object.keys(codes).length,
    codes,
    freq,
  };
}

$("btn-export-huffman").addEventListener("click", () => {
  if (state.metricsHistory.length === 0) return alert("No hay datos para exportar.");

  const jsonText = JSON.stringify(state.metricsHistory);
  const result = huffmanEncode(jsonText);

  state.lastHuffmanBlob = new Blob([result.compressed], { type: "application/octet-stream" });

  $("huff-original").textContent   = formatBytes(result.originalSize);
  $("huff-compressed").textContent = formatBytes(result.compressedSize);
  $("huff-ratio").textContent      = `${result.ratio}%`;
  $("huff-symbols").textContent    = result.symbolCount;

  const sortedCodes = Object.entries(result.freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  $("huffman-codes").innerHTML = sortedCodes.map(([ch, f]) => {
    const displayChar = ch === " " ? "⎵" : ch === "\n" ? "\\n" : ch === "\t" ? "\\t" : ch === '"' ? '\\"' : ch;
    return `
      <div class="huffman-code-row">
        <span class="huffman-code-char">'${displayChar}'</span>
        <span class="huffman-code-bits">${result.codes[ch]}</span>
        <span class="huffman-code-freq">×${f}</span>
      </div>`;
  }).join("");

  $("huffman-modal").classList.remove("hidden");
});

$("modal-close").addEventListener("click", () => {
  $("huffman-modal").classList.add("hidden");
});

$("huffman-modal").addEventListener("click", (e) => {
  if (e.target === $("huffman-modal")) {
    $("huffman-modal").classList.add("hidden");
  }
});

$("btn-download-hfm").addEventListener("click", () => {
  if (!state.lastHuffmanBlob) return;
  const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  downloadBlob(state.lastHuffmanBlob, `aforo_data_${ts}.hfm`);
});

// ===== UTILITIES =====
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1024 / 1024).toFixed(2) + " MB";
}

function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type });
  downloadBlob(blob, filename);
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ===== INIT =====
(async function init() {
  // Cargar historial inicial diario
  await fetchDailyLog();
  
  // Encender el polling en tiempo real cada 2 segundos
  pollLiveMetrics();
  setInterval(pollLiveMetrics, 2000);
  
  // Actualizar el historial jsonl de fondo cada 15 segundos
  setInterval(fetchDailyLog, 15000);
})();
