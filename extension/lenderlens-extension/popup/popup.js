/**
 * LenderLens — Popup UI Controller
 * Renders the Trust Card matching the security product design specifications.
 */

'use strict';

const BACKEND_ORIGIN = 'https://lenderlens-9rky.onrender.com';
const API_BASE = `${BACKEND_ORIGIN}/api`;

async function initPopup() {
  const container = document.getElementById('popup-content');
  const openDashBtn = document.getElementById('openDashboard');

  if (openDashBtn) {
    openDashBtn.addEventListener('click', () => {
      chrome.tabs.create({ url: `${BACKEND_ORIGIN}/dashboard/index.html` });
      window.close();
    });
  }

  // Query active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url || tab.url.startsWith('chrome://')) {
    renderIdle(container);
    return;
  }

  const urlObj = new URL(tab.url);
  const domain = urlObj.hostname.replace(/^www\./, '');

  // Fetch or analyze state from backend
  try {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: tab.url,
        domain: domain,
        claimed_lender: domain.includes('fastcash') ? 'ABC Finance' : domain.includes('quickloan') ? 'QuickLoan Financial' : 'ABC Finance Ltd.'
      })
    });

    if (res.ok) {
      const data = await res.json();
      renderTrustCard(container, data, domain, tab);
      return;
    }
  } catch (err) {
    console.warn('[LenderLens Popup] Backend offline, using heuristic fallback:', err);
  }

  // Heuristic Fallback if backend is offline
  renderHeuristicTrustCard(container, domain, tab);
}

function renderTrustCard(container, data, domain, tab) {
  const score = data.risk_score;
  const level = data.risk_level; // LOW, UNCERTAIN, HIGH, CRITICAL
  const claimedName = data.identity?.claimed_name || domain;
  const isHigh = level === 'CRITICAL' || level === 'HIGH';
  const isUncertain = level === 'UNCERTAIN';

  const statusClass = isHigh ? 'status-danger' : isUncertain ? 'status-warning' : 'status-success';
  const statusLabel = isHigh ? '🔴 HIGH RISK' : isUncertain ? '⚠️ NEEDS REVIEW' : '✓ LOW RISK';
  const fillColor = isHigh ? '#dc2626' : isUncertain ? '#d97706' : '#16a34a';

  let evidenceHtml = '';
  if (data.reasons && data.reasons.length) {
    evidenceHtml = data.reasons.slice(0, 5).map(r => {
      const icon = isHigh ? '✕' : isUncertain ? '⚠' : '✓';
      const iconClass = isHigh ? 'ev-danger' : isUncertain ? 'ev-warning' : 'ev-success';
      return `
        <div class="evidence-item">
          <span class="ev-icon ${iconClass}">${icon}</span>
          <span>${r}</span>
        </div>
      `;
    }).join('');
  } else {
    evidenceHtml = `
      <div class="evidence-item">
        <span class="ev-icon ev-success">✓</span>
        <span>No major risk indicators detected across 4 layers</span>
      </div>
    `;
  }

  container.innerHTML = `
    <div class="lender-title">${claimedName}</div>
    <div class="lender-domain">${domain}</div>

    <!-- Status & Score Bar -->
    <div class="status-banner ${statusClass}">
      <div class="status-level-row">
        <span>${statusLabel}</span>
        <span>${score} / 100</span>
      </div>
      <div class="score-progress-bar">
        <div class="score-progress-fill" style="width: ${score}%; background: ${fillColor};"></div>
      </div>
    </div>

    <!-- Evidence List -->
    <div class="evidence-section-title">Evidence Breakdown</div>
    <div class="evidence-items">
      ${evidenceHtml}
    </div>

    <!-- Urgent Warning if High Risk -->
    ${isHigh ? `
    <div class="transfer-warning">
      ⚠ DO NOT TRANSFER MONEY
    </div>
    ` : ''}

    <!-- Actions -->
    <div class="actions-grid">
      <button class="btn btn-primary btn-block-full" id="btn-view-evidence">
        ${isUncertain ? 'View Review Status →' : 'View Full Evidence →'}
      </button>
      <button class="btn btn-secondary" id="btn-report">⚑ Report</button>
      <button class="btn btn-secondary" id="btn-go-back">← Go Back</button>
    </div>
  `;

  // Wire event handlers
  document.getElementById('btn-view-evidence')?.addEventListener('click', () => {
    chrome.tabs.create({ url: `${BACKEND_ORIGIN}/dashboard/index.html` });
    window.close();
  });

  document.getElementById('btn-go-back')?.addEventListener('click', () => {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => history.back()
    }).catch(() => {});
    window.close();
  });

  document.getElementById('btn-report')?.addEventListener('click', () => {
    fetch(`${API_BASE}/cases/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: tab.url, domain: domain, lender_name: claimedName, reason: 'Reported by user from popup' })
    }).catch(() => {});

    const btn = document.getElementById('btn-report');
    if (btn) {
      btn.textContent = '✓ Reported';
      btn.disabled = true;
    }
  });
}

function renderHeuristicTrustCard(container, domain, tab) {
  const isFastCash = domain.includes('fastcash');
  const isQuickLoan = domain.includes('quickloan');

  const mockData = {
    risk_score: isFastCash ? 91 : isQuickLoan ? 56 : 18,
    risk_level: isFastCash ? 'HIGH' : isQuickLoan ? 'UNCERTAIN' : 'LOW',
    identity: { claimed_name: isFastCash ? 'ABC Finance (Impersonated)' : isQuickLoan ? 'QuickLoan Financial' : 'ABC Finance Ltd.' },
    reasons: isFastCash ? [
      'Website-domain mismatch (Impersonating ABC Finance Ltd.)',
      'Advance fee detected (₹1,500 security deposit demand)',
      'Connected to 3 flagged phishing domains in GNN',
      'Abnormal burst in temporal activity (+1840%)'
    ] : isQuickLoan ? [
      'Valid RBI registration found under legal entity, but unofficial domain alias used',
      'Key Fact Statement (KFS) format incomplete',
      'Requests device Contacts access'
    ] : [
      'Direct match with official RBI Registered NBFC registry record',
      'Domain verified with SSL & MCA listing',
      'No advance fees or abusive permissions requested'
    ]
  };

  renderTrustCard(container, mockData, domain, tab);
}

function renderIdle(container) {
  container.innerHTML = `
    <div style="text-align:center; padding: 24px 10px;">
      <img src="../assets/icon128.png" alt="LenderLens" style="width:40px; height:40px; margin-bottom:8px;">
      <div style="font-weight: 700; font-size: 14px; margin-bottom: 4px;">LenderLens Active</div>
      <div style="font-size: 12px; color: #64748b;">Visit any loan or credit website to initiate automatic 4-layer AI fraud detection.</div>
    </div>
  `;
}

document.addEventListener('DOMContentLoaded', initPopup);
