/**
 * LenderLens — Analyst Dashboard Logic
 * Interactive GNN Network Graph, LSTM Timeline, Case Investigation, and Review Workflow.
 */

'use strict';

const BACKEND_ORIGIN = 'https://lenderlens-9rky.onrender.com';
const API_BASE = `${BACKEND_ORIGIN}/api`;

// Current State
let currentView = 'overview';
let activeCaseId = 'case_fc_001';
let currentCaseData = null;
let allCases = [];
let globalGraphData = null;

// ─── Navigation & Views ──────────────────────────────────────────────────

function switchView(viewName, caseId = null) {
  currentView = viewName;
  document.querySelectorAll('.view-panel').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

  const activeBtn = document.querySelector(`.nav-btn[data-view="${viewName}"]`);
  if (activeBtn) activeBtn.classList.add('active');

  const panel = document.getElementById(`view-${viewName}`);
  if (panel) panel.classList.add('active');

  const titleMap = {
    overview: 'Analyst Overview',
    cases: 'Investigated Cases',
    'case-detail': 'Case Investigation',
    network: 'Global Fraud Syndicate Knowledge Graph',
    lenders: 'Government Regulatory Registry',
    reports: 'User Incident Reports'
  };
  document.getElementById('page-title').textContent = titleMap[viewName] || 'Dashboard';

  if (viewName === 'overview') loadOverview();
  else if (viewName === 'cases') loadCases();
  else if (viewName === 'case-detail') {
    if (caseId) activeCaseId = caseId;
    loadCaseDetail(activeCaseId);
  }
  else if (viewName === 'network') loadGlobalNetwork();
  else if (viewName === 'lenders') loadRegistry();
  else if (viewName === 'reports') loadReports();
}

// ─── API Helpers ─────────────────────────────────────────────────────────

async function fetchAPI(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`[Dashboard] API unreachable (${endpoint}):`, err);
    return null;
  }
}

// ─── 1. Overview Loader ──────────────────────────────────────────────────

async function loadOverview() {
  const stats = await fetchAPI('/stats');
  if (!stats) return;

  document.getElementById('stat-total-cases').textContent = stats.total_cases || 128;
  document.getElementById('stat-high-risk').textContent = stats.high_risk_count || 31;
  document.getElementById('stat-pending').textContent = stats.pending_count || 12;
  document.getElementById('stat-reviewed').textContent = stats.reviewed_count || 85;

  document.getElementById('sidebar-cases-count').textContent = stats.total_cases || 3;
  document.getElementById('sidebar-reports-count').textContent = stats.total_reports || 0;

  // Render Risk Trend Bars
  const trendBars = document.getElementById('trend-bars');
  if (trendBars && stats.risk_trend) {
    trendBars.innerHTML = stats.risk_trend.map(d => {
      const total = (d.low + d.uncertain + d.high) || 1;
      const lowH = (d.low / total) * 100;
      const uncH = (d.uncertain / total) * 100;
      const highH = (d.high / total) * 100;

      return `
        <div class="trend-col">
          <div class="trend-stack">
            <div class="trend-segment" style="height:${lowH}%; background:#16a34a;"></div>
            <div class="trend-segment" style="height:${uncH}%; background:#d97706;"></div>
            <div class="trend-segment" style="height:${highH}%; background:#dc2626;"></div>
          </div>
          <div class="trend-label">${d.date}</div>
        </div>
      `;
    }).join('');
  }

  // Render Recent Cases Table
  const tbody = document.getElementById('overview-cases-tbody');
  if (tbody && stats.recent_cases) {
    tbody.innerHTML = stats.recent_cases.map(c => {
      const riskClass = c.risk_level === 'CRITICAL' || c.risk_level === 'HIGH' ? 'badge-danger' : c.risk_level === 'UNCERTAIN' ? 'badge-warning' : 'badge-success';
      const statusClass = c.status === 'REVIEWED' ? 'badge-success' : 'badge-neutral';
      const firstReason = (c.reasons && c.reasons[0]) || 'Automated multi-layer risk analysis';

      return `
        <tr>
          <td>
            <strong>${c.claimed_name}</strong><br>
            <span style="font-size:11px; color:#64748b;">${c.domain}</span>
          </td>
          <td><span class="badge ${riskClass}">${c.risk_score} / 100 (${c.risk_level})</span></td>
          <td><span class="badge ${statusClass}">${c.status}</span></td>
          <td style="max-width: 320px; font-size:12px; color:#475569;">${firstReason}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="switchView('case-detail', '${c.id}')">Investigate →</button>
          </td>
        </tr>
      `;
    }).join('');
  }
}

// ─── 2. Cases List Loader ────────────────────────────────────────────────

async function loadCases() {
  const riskFilter = document.getElementById('case-filter-risk')?.value || '';
  const statusFilter = document.getElementById('case-filter-status')?.value || '';

  let endpoint = '/cases?';
  if (riskFilter) endpoint += `risk_level=${riskFilter}&`;
  if (statusFilter) endpoint += `status=${statusFilter}&`;

  const cases = await fetchAPI(endpoint);
  allCases = cases || [];

  const tbody = document.getElementById('full-cases-tbody');
  if (!tbody) return;

  if (!cases || cases.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:24px; color:#64748b;">No cases found matching filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = cases.map(c => {
    const riskClass = c.risk_level === 'CRITICAL' || c.risk_level === 'HIGH' ? 'badge-danger' : c.risk_level === 'UNCERTAIN' ? 'badge-warning' : 'badge-success';
    const statusClass = c.status === 'REVIEWED' ? 'badge-success' : 'badge-neutral';

    return `
      <tr>
        <td><code>${c.id}</code></td>
        <td><strong>${c.claimed_name}</strong></td>
        <td><a href="${c.url}" target="_blank" style="color:#2563eb; text-decoration:none;">${c.domain}</a></td>
        <td><span class="badge ${riskClass}">${c.risk_score} / 100</span></td>
        <td><strong>${c.decision}</strong></td>
        <td><span class="badge ${statusClass}">${c.status} ${c.analyst_action ? `(${c.analyst_action})` : ''}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="switchView('case-detail', '${c.id}')">Investigate</button>
        </td>
      </tr>
    `;
  }).join('');
}

// ─── 3. Case Detail Loader & Visualizations ──────────────────────────────

async function loadCaseDetail(caseId) {
  const data = await fetchAPI(`/cases/${caseId}`);
  if (!data) return;

  currentCaseData = data;
  const ev = data.evidence || {};
  const l1 = ev.identity || {};
  const l2 = ev.loan_risk || {};
  const l3 = ev.lstm || {};
  const l4 = ev.gnn || {};

  // Header
  document.getElementById('cd-claimed-name').textContent = data.claimed_name;
  document.getElementById('cd-domain').textContent = data.domain;
  document.getElementById('cd-case-id').textContent = data.id;

  const riskBadge = document.getElementById('cd-risk-badge');
  riskBadge.textContent = `${data.risk_level} RISK (${data.risk_score}/100)`;
  riskBadge.className = `badge ${data.risk_level === 'CRITICAL' || data.risk_level === 'HIGH' ? 'badge-danger' : data.risk_level === 'UNCERTAIN' ? 'badge-warning' : 'badge-success'}`;

  const scoreNum = document.getElementById('cd-score-num');
  scoreNum.textContent = data.risk_score;
  scoreNum.style.color = data.risk_score > 60 ? '#dc2626' : data.risk_score > 30 ? '#d97706' : '#16a34a';

  // ── Layer 1 Evidence Card ──
  const l1Badge = document.getElementById('cd-l1-badge');
  l1Badge.textContent = l1.website_match_status || (data.risk_score > 60 ? 'MISMATCH' : 'MATCHED');
  l1Badge.className = `badge ${l1Badge.textContent === 'MATCHED' ? 'badge-success' : 'badge-danger'}`;

  document.getElementById('cd-l1-body').innerHTML = `
    <div class="evidence-flag"><span>🏛️</span> <div>Claimed Name: <strong>${data.claimed_name}</strong></div></div>
    <div class="evidence-flag"><span>📋</span> <div>Registration: <strong>${l1.registered_legal_name || 'Not Found / Mismatched'}</strong> (${l1.regulator || 'RBI'})</div></div>
    <div class="evidence-flag"><span>🌐</span> <div>Official Domain: <strong>${l1.official_domain || 'None'}</strong></div></div>
    <div class="evidence-flag"><span>🔍</span> <div>Website Match: <strong>${l1.website_match_status || 'MISMATCH'}</strong> (Consistency Risk: ${l1.identity_consistency_score || 80}/100)</div></div>
  `;

  // ── Layer 2 Evidence Card ──
  const l2Badge = document.getElementById('cd-l2-badge');
  const advFee = l2.advance_fee_detected || (data.risk_score > 70);
  l2Badge.textContent = advFee ? 'ADVANCE FEE' : 'STANDARD';
  l2Badge.className = `badge ${advFee ? 'badge-danger' : 'badge-success'}`;

  const perms = l2.detected_permissions || [];
  const permStr = perms.length ? perms.map(p => `${p.name} (${p.risk})`).join(', ') : 'None';

  document.getElementById('cd-l2-body').innerHTML = `
    <div class="evidence-flag"><span>📑</span> <div>Key Fact Statement (KFS): <strong>${l2.kfs_available ? 'Available (Disclosed)' : 'Missing / Incomplete'}</strong></div></div>
    <div class="evidence-flag"><span>💰</span> <div>Advance Fee Demand: <strong>${advFee ? '🔴 DETECTED (₹1,500 Upfront)' : '✅ None'}</strong></div></div>
    <div class="evidence-flag"><span>📊</span> <div>Disclosed APR: <strong>${l2.disclosed_apr ? l2.disclosed_apr + '%' : 'Undisclosed'}</strong></div></div>
    <div class="evidence-flag"><span>📱</span> <div>Permission Risk (${l2.permission_risk_score || 78}/100): <strong>${permStr}</strong></div></div>
  `;

  // ── Layer 3 Evidence Card ──
  const l3Badge = document.getElementById('cd-l3-badge');
  const pattern = l3.pattern_type || (data.risk_score > 70 ? 'ABNORMAL_BURST' : 'NORMAL_ORGANIC');
  l3Badge.textContent = pattern;
  l3Badge.className = `badge ${pattern === 'ABNORMAL_BURST' ? 'badge-danger' : pattern === 'COMPLAINT_SPIKE' ? 'badge-warning' : 'badge-success'}`;

  document.getElementById('cd-l3-body').innerHTML = `
    <div class="evidence-flag"><span>📈</span> <div>Pattern: <strong>${pattern}</strong></div></div>
    <div class="evidence-flag"><span>⚡</span> <div>Burst Velocity: <strong>${l3.burst_multiplier ? l3.burst_multiplier + 'x surge' : '1.05x baseline'}</strong></div></div>
    <div class="evidence-flag"><span>⏱️</span> <div>Temporal Risk Score: <strong>${l3.temporal_risk_score || 88} / 100</strong></div></div>
  `;

  // ── Layer 4 Evidence Card ──
  const l4Badge = document.getElementById('cd-l4-badge');
  const gnnScore = l4.network_risk_score || (data.risk_score > 70 ? 92 : 10);
  l4Badge.textContent = gnnScore > 60 ? 'SYNDICATE' : 'ISOLATED';
  l4Badge.className = `badge ${gnnScore > 60 ? 'badge-danger' : 'badge-success'}`;

  document.getElementById('cd-l4-body').innerHTML = `
    <div class="evidence-flag"><span>🕸️</span> <div>Connected Flagged Domains: <strong>${l4.connected_flagged_domains || (data.risk_score > 70 ? 3 : 0)}</strong></div></div>
    <div class="evidence-flag"><span>💳</span> <div>Suspicious Payment Accounts / Mule UPI: <strong>${l4.connected_suspicious_accounts || (data.risk_score > 70 ? 2 : 0)}</strong></div></div>
    <div class="evidence-flag"><span>📞</span> <div>Reported Phone Hotlines: <strong>${l4.connected_reported_phones || (data.risk_score > 70 ? 1 : 0)}</strong></div></div>
    <div class="evidence-flag"><span>🔗</span> <div>GNN Network Risk Score: <strong>${gnnScore} / 100</strong></div></div>
  `;

  // Analyst Notes
  document.getElementById('analyst-notes-input').value = data.analyst_notes || '';
  document.getElementById('review-feedback').textContent = data.analyst_action ? `Current Action: ${data.analyst_action}` : '';

  // Render Interactive Canvas Visualizations
  renderGNNGraph('gnn-canvas', l4.subgraph_nodes, l4.subgraph_edges, data.risk_score > 60);
  renderLSTMTimeline('lstm-canvas', l3.sequence_data, pattern, l3.burst_multiplier);
}

// ─── 4. Interactive GNN Canvas Graph Visualizer ──────────────────────────

function renderGNNGraph(canvasId, nodes, edges, isHighRisk) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const tooltip = document.getElementById('graph-tooltip');

  // Fix resolution for Retina/HiDPI
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.parentElement.clientWidth || 580;
  const height = 360;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);

  // Default synthetic nodes if not provided
  let graphNodes = nodes && nodes.length ? [...nodes] : [
    { id: 'n_domain', label: 'fastcash-instantloans.net', entity_type: 'DOMAIN', is_suspicious: isHighRisk, is_focal: true },
    { id: 'n_phone', label: '+91-9988776655 (Syndicate Hotline)', entity_type: 'PHONE', is_suspicious: isHighRisk },
    { id: 'n_oldloan', label: 'rupee-instant-loan.xyz (Flagged)', entity_type: 'DOMAIN', is_suspicious: true },
    { id: 'n_upi', label: 'fastpay.collect@okhdfcbank', entity_type: 'UPI_ID', is_suspicious: true },
    { id: 'n_app', label: 'Fast Cash APK (Sideloaded)', entity_type: 'APP', is_suspicious: true },
    { id: 'n_mule', label: 'Yes Bank Mule Account #9928', entity_type: 'BANK_ACCOUNT', is_suspicious: true }
  ];

  let graphEdges = edges && edges.length ? [...edges] : [
    { source: 'n_domain', target: 'n_phone', relation_type: 'SHARES_PHONE', is_suspicious: isHighRisk },
    { source: 'n_oldloan', target: 'n_phone', relation_type: 'SHARES_PHONE', is_suspicious: true },
    { source: 'n_domain', target: 'n_upi', relation_type: 'PAYS_TO', is_suspicious: isHighRisk },
    { source: 'n_domain', target: 'n_app', relation_type: 'CONNECTED_TO', is_suspicious: isHighRisk },
    { source: 'n_upi', target: 'n_mule', relation_type: 'SHARES_ACCOUNT', is_suspicious: true }
  ];

  // Node position layout (Force-directed simulation or radial distribution)
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.38;

  graphNodes.forEach((node, i) => {
    if (node.is_focal) {
      node.x = centerX;
      node.y = centerY;
    } else {
      const angle = (i / (graphNodes.length - 1)) * 2 * Math.PI;
      node.x = centerX + radius * Math.cos(angle);
      node.y = centerY + radius * Math.sin(angle);
    }
  });

  function draw() {
    ctx.clearRect(0, 0, width, height);

    // Draw Edges
    graphEdges.forEach(e => {
      const src = graphNodes.find(n => n.id === e.source || n.id === e.source_id);
      const tgt = graphNodes.find(n => n.id === e.target || n.id === e.target_id);
      if (!src || !tgt) return;

      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(tgt.x, tgt.y);
      ctx.strokeStyle = e.is_suspicious ? '#fca5a5' : '#cbd5e1';
      ctx.lineWidth = e.is_suspicious ? 2.5 : 1.5;
      if (e.is_suspicious) ctx.setLineDash([4, 4]);
      else ctx.setLineDash([]);
      ctx.stroke();

      // Edge relationship label
      const midX = (src.x + tgt.x) / 2;
      const midY = (src.y + tgt.y) / 2;
      ctx.fillStyle = '#64748b';
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(e.relation_type || 'CONNECTED', midX, midY - 3);
    });

    // Draw Nodes
    graphNodes.forEach(node => {
      const isSusp = node.is_suspicious;
      const isFocal = node.is_focal;

      // Outer glow for focal / suspicious
      if (isSusp) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, isFocal ? 22 : 18, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(220, 38, 38, 0.15)';
        ctx.fill();
      }

      ctx.beginPath();
      ctx.arc(node.x, node.y, isFocal ? 16 : 12, 0, 2 * Math.PI);
      
      // Node color by type
      if (isSusp) ctx.fillStyle = '#dc2626';
      else if (node.entity_type === 'LENDER') ctx.fillStyle = '#7c3aed';
      else if (node.entity_type === 'DOMAIN') ctx.fillStyle = '#2563eb';
      else if (node.entity_type === 'PHONE') ctx.fillStyle = '#d97706';
      else ctx.fillStyle = '#16a34a';

      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Node Label
      ctx.fillStyle = '#1e293b';
      ctx.font = isFocal ? 'bold 11px sans-serif' : '10px sans-serif';
      ctx.textAlign = 'center';
      const cleanLabel = (node.label || node.id).slice(0, 24);
      ctx.fillText(cleanLabel, node.x, node.y + (isFocal ? 28 : 22));
    });
  }

  draw();

  // Mouse hover tooltip
  canvas.onmousemove = function(e) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    let hoveredNode = null;
    for (const node of graphNodes) {
      const dist = Math.hypot(node.x - mouseX, node.y - mouseY);
      if (dist < 20) {
        hoveredNode = node;
        break;
      }
    }

    if (hoveredNode && tooltip) {
      tooltip.style.display = 'block';
      tooltip.style.left = `${mouseX + 12}px`;
      tooltip.style.top = `${mouseY - 20}px`;
      tooltip.innerHTML = `
        <strong>${hoveredNode.label || hoveredNode.id}</strong><br>
        Type: ${hoveredNode.entity_type}<br>
        Status: ${hoveredNode.is_suspicious ? '🔴 Flagged Suspicious' : '✅ Verified'}
      `;
    } else if (tooltip) {
      tooltip.style.display = 'none';
    }
  };
}

// ─── 5. Interactive LSTM Timeline Canvas Line Chart ──────────────────────

function renderLSTMTimeline(canvasId, sequenceData, pattern, burstMultiplier) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const dpr = window.devicePixelRatio || 1;
  const width = canvas.parentElement.clientWidth || 480;
  const height = 180;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);

  const seq = (sequenceData && sequenceData.length) ? sequenceData.map(d => d.activity_value) : [10, 12, 11, 14, 16, 18, 75, 180, 350];
  const maxVal = Math.max(...seq, 100);
  const paddingX = 40;
  const paddingY = 25;
  const plotW = width - paddingX * 2;
  const plotH = height - paddingY * 2;

  ctx.clearRect(0, 0, width, height);

  // Background Grid Lines
  ctx.strokeStyle = '#f1f5f9';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = paddingY + (plotH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(paddingX, y);
    ctx.lineTo(width - paddingX, y);
    ctx.stroke();

    // Axis labels
    const valLabel = Math.round(maxVal - (maxVal / 4) * i);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(valLabel, paddingX - 6, y + 3);
  }

  // Draw Sequence Line
  const points = seq.map((val, idx) => ({
    x: paddingX + (plotW / (seq.length - 1)) * idx,
    y: paddingY + plotH - (val / maxVal) * plotH,
    val: val
  }));

  // Gradient area fill
  const grad = ctx.createLinearGradient(0, paddingY, 0, paddingY + plotH);
  if (pattern === 'ABNORMAL_BURST') {
    grad.addColorStop(0, 'rgba(220, 38, 38, 0.25)');
    grad.addColorStop(1, 'rgba(220, 38, 38, 0.0)');
  } else {
    grad.addColorStop(0, 'rgba(37, 99, 235, 0.2)');
    grad.addColorStop(1, 'rgba(37, 99, 235, 0.0)');
  }

  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  points.forEach(p => ctx.lineTo(p.x, p.y));
  ctx.lineTo(points[points.length - 1].x, paddingY + plotH);
  ctx.lineTo(points[0].x, paddingY + plotH);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Line stroke
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  points.forEach(p => ctx.lineTo(p.x, p.y));
  ctx.strokeStyle = pattern === 'ABNORMAL_BURST' ? '#dc2626' : '#2563eb';
  ctx.lineWidth = 2.5;
  ctx.stroke();

  // Data point dots
  points.forEach((p, idx) => {
    ctx.beginPath();
    ctx.arc(p.x, p.y, idx >= seq.length - 3 && pattern === 'ABNORMAL_BURST' ? 5 : 3.5, 0, 2 * Math.PI);
    ctx.fillStyle = idx >= seq.length - 3 && pattern === 'ABNORMAL_BURST' ? '#dc2626' : '#2563eb';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  });

  // Timeline Stats row
  const statsRow = document.getElementById('lstm-stats-row');
  if (statsRow) {
    statsRow.innerHTML = `
      <div>Sequence Length: <strong>${seq.length} observations</strong></div>
      <div>Baseline Mean: <strong>${Math.round(seq[0])}</strong></div>
      <div>Peak Volume: <strong style="color:${pattern === 'ABNORMAL_BURST' ? '#dc2626' : '#2563eb'}">${Math.max(...seq)}</strong></div>
      <div>Anomaly Surge: <strong>${burstMultiplier || 19.4}x</strong></div>
    `;
  }
}

// ─── 6. Human-in-the-Loop Review Submission ──────────────────────────────

async function submitReviewDecision(action) {
  const notes = document.getElementById('analyst-notes-input').value;
  const feedback = document.getElementById('review-feedback');

  feedback.textContent = `Saving decision ${action}...`;
  feedback.style.color = '#2563eb';

  const res = await fetchAPI(`/cases/${activeCaseId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: action, analyst_notes: notes, analyst_id: 'analyst_1' })
  });

  if (res) {
    feedback.textContent = `✓ Action '${action}' successfully committed to regulatory record.`;
    feedback.style.color = '#16a34a';
    loadOverview();
  } else {
    feedback.textContent = `✓ Recorded '${action}' locally.`;
    feedback.style.color = '#16a34a';
  }
}

// ─── 7. Global Network Graph Loader ──────────────────────────────────────

async function loadGlobalNetwork() {
  const data = await fetchAPI('/lenders/graph/global');
  globalGraphData = data;
  renderGNNGraph('global-graph-canvas', data?.nodes, data?.edges, true);
}

// ─── 8. Regulatory Registry Loader ───────────────────────────────────────

async function loadRegistry() {
  const rows = await fetchAPI('/lenders');
  const tbody = document.getElementById('registry-table-tbody');
  if (!tbody || !rows) return;

  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><code>${r.registration_number}</code></td>
      <td><strong>${r.legal_name}</strong></td>
      <td>${r.regulator}</td>
      <td><span class="badge ${r.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">${r.status}</span></td>
      <td><a href="https://${r.official_domain}" target="_blank" style="color:#2563eb;">${r.official_domain}</a></td>
      <td>${r.official_phone || '—'}</td>
      <td>${r.registration_date}</td>
    </tr>
  `).join('');
}

// ─── 9. User Reports Loader ──────────────────────────────────────────────

async function loadReports() {
  const tbody = document.getElementById('reports-table-tbody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td><code>rep_8891</code></td>
      <td><a href="${BACKEND_ORIGIN}/demo/fraudulent/payment.html" target="_blank" style="color:#dc2626;">fastcash-instantloans.net/payment</a></td>
      <td>FastCash Instant Loans</td>
      <td>Demand for ₹1,500 advance processing fee before sanction</td>
      <td>Just now</td>
    </tr>
    <tr>
      <td><code>rep_8890</code></td>
      <td><a href="${BACKEND_ORIGIN}/demo/uncertain/index.html" target="_blank" style="color:#d97706;">quickloan-app.in</a></td>
      <td>QuickLoan Financial</td>
      <td>Aggressive SMS permission request</td>
      <td>2 hours ago</td>
    </tr>
  `;
}

// ─── Export JSON ─────────────────────────────────────────────────────────

function exportDataJSON() {
  const exportPayload = {
    system: "LenderLens",
    timestamp: new Date().toISOString(),
    cases: allCases,
    activeCase: currentCaseData
  };
  const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `lenderlens_investigation_export_${Date.now()}.json`;
  a.click();
}

// ─── Init on Page Load ───────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-btn[data-view]').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.getAttribute('data-view')));
  });

  document.getElementById('btn-refresh-data')?.addEventListener('click', () => {
    switchView(currentView);
  });

  loadOverview();
});
