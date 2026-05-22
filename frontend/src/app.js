// ================================================================
// AFORO VEHICULAR — DASHBOARD APP.JS
// ================================================================
// Supabase Realtime + Chart.js + Huffman Compression + UI Logic
// ================================================================

// ===== SUPABASE CONFIG =====
const SUPABASE_URL  = "https://aeospnvtmvgcffolnllr.supabase.co";
const SUPABASE_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlb3NwbnZ0bXZnY2Zmb2xubGxyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkxNTU1NzMsImV4cCI6MjA5NDczMTU3M30.8Uupw8SzpDjEFXZFcihUAilD4QD57Fw490SzgwPEOvs";

const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON);

// ===== STATE =====
const state = {
  metricsHistory: [],     // All fetched rows
  activeChart: "flow",    // flow | density | vehicles
  sparkData: { total: [], scene: [], flow: [] },
  lastHuffmanBlob: null,
};

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
    // Draw connections
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

// Cluster doughnut chart
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

  // Colorize traffic state
  const stateEl = dom.trafficState;
  stateEl.style.setProperty("-webkit-text-fill-color", "");
  if ((d.fluidez_avance || "").includes("CONGESTION")) {
    stateEl.style.color = "#ff3d3d";
    stateEl.style.setProperty("-webkit-text-fill-color", "#ff3d3d");
  } else if ((d.fluidez_avance || "").includes("LIBRE")) {
    stateEl.style.color = "#00e676";
    stateEl.style.setProperty("-webkit-text-fill-color", "#00e676");
  } else {
    stateEl.style.color = "#00e5ff";
    stateEl.style.setProperty("-webkit-text-fill-color", "#00e5ff");
  }

  // Alert banner
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

  // Cluster doughnut
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
  // Remove empty row
  const emptyRow = dom.metricsTbody.querySelector(".empty-row");
  if (emptyRow) emptyRow.remove();
  dom.metricsTbody.prepend(tr);
  // Keep max 50 rows
  while (dom.metricsTbody.children.length > 50) {
    dom.metricsTbody.removeChild(dom.metricsTbody.lastChild);
  }
}

// ===== SUPABASE DATA =====
async function fetchInitialData() {
  try {
    const { data, error } = await sb
      .from("metrics")
      .select("*")
      .order("ts", { ascending: true })
      .limit(100);

    if (error) throw error;

    state.metricsHistory = data || [];

    // Populate table
    const reversed = [...(data || [])].reverse();
    for (const row of reversed) {
      addTableRow(row);
    }

    // Update dashboard with latest
    if (data && data.length > 0) {
      updateDashboard(data[data.length - 1]);
    }

    rebuildMainChart();
    setConnected(true);
  } catch (err) {
    console.error("Error fetching initial data:", err);
    setConnected(false, err.message);
  }
}

function subscribeToRealtime() {
  sb.channel("metrics-realtime")
    .on("postgres_changes", { event: "INSERT", schema: "public", table: "metrics" }, (payload) => {
      const row = payload.new;
      state.metricsHistory.push(row);
      if (state.metricsHistory.length > 200) state.metricsHistory.shift();

      updateDashboard(row);
      addTableRow(row);
      rebuildMainChart();
    })
    .subscribe((status) => {
      if (status === "SUBSCRIBED") {
        setConnected(true);
      }
    });
}

function setConnected(ok, errMsg) {
  dom.connStatus.className = "status-indicator " + (ok ? "connected" : "error");
  dom.connText.textContent = ok ? "Conectado" : (errMsg || "Error");
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
  }
});

$("btn-connect-stream").addEventListener("click", () => {
  const url = $("stream-url-input").value.trim();
  if (!url) return alert("Ingresa una URL de stream válida");
  alert(`Conexión a stream configurada: ${url}\n\nNota: El stream se procesará en el backend de Python. Asegúrate de que main.py use esta URL.`);
});

// ===== EXPORT JSON =====
$("btn-export-json").addEventListener("click", () => {
  if (state.metricsHistory.length === 0) return alert("No hay datos para exportar.");
  const json = JSON.stringify(state.metricsHistory, null, 2);
  downloadFile(json, "aforo_vehicular_data.json", "application/json");
});

// ===== REFRESH DATA =====
$("btn-refresh-data").addEventListener("click", () => {
  dom.metricsTbody.innerHTML = `<tr class="empty-row"><td colspan="7">Cargando datos...</td></tr>`;
  state.metricsHistory = [];
  state.sparkData = { total: [], scene: [], flow: [] };
  fetchInitialData();
});

// ===== HUFFMAN COMPRESSION =====
// Full Huffman implementation in JavaScript

class HuffmanNode {
  constructor(char, freq, left = null, right = null) {
    this.char = char;
    this.freq = freq;
    this.left = left;
    this.right = right;
  }
}

function buildHuffmanTree(text) {
  // 1. Count frequencies
  const freq = {};
  for (const ch of text) {
    freq[ch] = (freq[ch] || 0) + 1;
  }

  // 2. Build priority queue (min-heap via array sort)
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

  // 3. Build codes
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
  
  // Encode text to binary string
  let binaryStr = "";
  for (const ch of text) {
    binaryStr += codes[ch];
  }

  // Pack binary string into Uint8Array
  const paddingBits = (8 - (binaryStr.length % 8)) % 8;
  binaryStr += "0".repeat(paddingBits);

  const bytes = new Uint8Array(binaryStr.length / 8);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(binaryStr.substring(i * 8, (i + 1) * 8), 2);
  }

  // Build header: JSON with codes table + padding info
  const header = JSON.stringify({ codes, padding: paddingBits });
  const headerBytes = new TextEncoder().encode(header);

  // Format: [4 bytes header length][header][compressed data]
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

  // Serialize metrics to JSON string
  const jsonText = JSON.stringify(state.metricsHistory);
  const result = huffmanEncode(jsonText);

  state.lastHuffmanBlob = new Blob([result.compressed], { type: "application/octet-stream" });

  // Populate modal
  $("huff-original").textContent   = formatBytes(result.originalSize);
  $("huff-compressed").textContent = formatBytes(result.compressedSize);
  $("huff-ratio").textContent      = `${result.ratio}%`;
  $("huff-symbols").textContent    = result.symbolCount;

  // Show top 10 codes
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

  // Show modal
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

// ===== UTILITY FUNCTIONS =====
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
  await fetchInitialData();
  subscribeToRealtime();

  // Polling fallback every 5s
  setInterval(async () => {
    try {
      const { data, error } = await sb
        .from("metrics")
        .select("*")
        .order("ts", { ascending: false })
        .limit(1);

      if (error || !data || data.length === 0) return;

      const latest = data[0];
      const lastKnown = state.metricsHistory[state.metricsHistory.length - 1];

      if (!lastKnown || latest.id !== lastKnown.id) {
        state.metricsHistory.push(latest);
        if (state.metricsHistory.length > 200) state.metricsHistory.shift();
        updateDashboard(latest);
        addTableRow(latest);
        rebuildMainChart();
      }
    } catch (_) { /* silent fallback */ }
  }, 5000);
})();
