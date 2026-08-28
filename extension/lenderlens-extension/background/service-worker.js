/**
 * LenderLens — Background Service Worker (Manifest V3)
 * Manages tab tracking, badge updates, and communication between extension popup & content scripts.
 */

'use strict';

const BACKEND_ORIGIN = 'https://lenderlens-9rky.onrender.com';
const API_BASE = `${BACKEND_ORIGIN}/api`;

// Cache of tab states
const tabCache = new Map();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const tabId = sender.tab?.id;

  switch (message.type) {
    case 'PAGE_DETECTED':
      if (tabId) {
        tabCache.set(tabId, message.data);
        updateBadge(tabId, message.data.risk_score || 0);
      }
      sendResponse({ status: 'received' });
      break;

    case 'GET_STATE':
      const data = tabCache.get(message.tabId);
      sendResponse({ state: data || null });
      break;

    case 'OPEN_DASHBOARD':
      chrome.tabs.create({ url: `${BACKEND_ORIGIN}/dashboard/index.html` });
      sendResponse({ status: 'ok' });
      break;
  }

  return true;
});

function updateBadge(tabId, score) {
  if (score > 70) {
    chrome.action.setBadgeText({ tabId, text: '!!!' }).catch(() => {});
    chrome.action.setBadgeBackgroundColor({ tabId, color: '#dc2626' }).catch(() => {});
  } else if (score > 30) {
    chrome.action.setBadgeText({ tabId, text: '!' }).catch(() => {});
    chrome.action.setBadgeBackgroundColor({ tabId, color: '#d97706' }).catch(() => {});
  } else if (score > 0) {
    chrome.action.setBadgeText({ tabId, text: '✓' }).catch(() => {});
    chrome.action.setBadgeBackgroundColor({ tabId, color: '#16a34a' }).catch(() => {});
  } else {
    chrome.action.setBadgeText({ tabId, text: '' }).catch(() => {});
  }
}

chrome.tabs.onRemoved.addListener((tabId) => {
  tabCache.delete(tabId);
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.status === 'loading') {
    tabCache.delete(tabId);
    chrome.action.setBadgeText({ tabId, text: '' }).catch(() => {});
  }
});
