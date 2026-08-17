// Application State
let state = {
  privacyMode: false,
  activeFilter: 'all',
  leads: [],
  stats: {},
  targetCount: 10,
  selectedLead: null,
  activeVariantIndex: 0,
  ws: null
};

// DOM Elements
const elements = {
  nicheInput: document.getElementById('niche-input'),
  platformSelect: document.getElementById('platform-select'),
  countrySelect: document.getElementById('country-select'),
  btnStartCampaign: document.getElementById('btn-start-campaign'),
  progressContainer: document.getElementById('progress-container'),
  progressBar: document.getElementById('progress-bar'),
  progressStepText: document.getElementById('progress-step-text'),
  progressPercentText: document.getElementById('progress-percent-text'),
  logTerminal: document.getElementById('log-terminal'),
  leadsTableBody: document.getElementById('leads-table-body'),
  statTotalLeads: document.getElementById('stat-total-leads'),
  statDeliverableEmails: document.getElementById('stat-deliverable-emails'),
  statPixelLeaks: document.getElementById('stat-pixel-leaks'),
  statApprovedQueue: document.getElementById('stat-approved-queue'),
  statSentEmails: document.getElementById('stat-sent-emails'),
  privacyToggleBtn: document.getElementById('privacy-toggle-btn'),
  reviewModal: document.getElementById('review-modal'),
  testEmailModal: document.getElementById('test-email-modal')
};

// Toast notification helper
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type === 'success' ? 'toast-success' : 'toast-error'}`;
  toast.innerHTML = `<span>${type === 'success' ? '✅' : '⚠️'}</span> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initWebSocket();
  fetchStats();
  fetchLeads();
  setupEventListeners();
});

// Setup WebSocket for Live Log Streaming
function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  
  try {
    state.ws = new WebSocket(wsUrl);
    
    state.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'campaign_update') {
        handleCampaignUpdate(msg.data);
      } else if (msg.type === 'lead_discovered') {
        fetchStats();
        fetchLeads();
      } else if (msg.type === 'sending_progress') {
        addLog(`📬 ${msg.message}`);
        showToast(msg.message, 'success');
      } else if (msg.type === 'sending_complete') {
        addLog(msg.message);
        showToast(msg.message, 'success');
        fetchStats();
        fetchLeads();
      }
    };
    
    state.ws.onclose = () => {
      setTimeout(initWebSocket, 3000);
    };
  } catch (e) {
    console.error('WebSocket error:', e);
  }
}

function handleCampaignUpdate(data) {
  if (!data) return;
  
  elements.progressContainer.style.display = 'block';
  elements.progressBar.style.width = `${data.progress_percentage}%`;
  elements.progressStepText.innerText = data.current_step || 'Processing...';
  elements.progressPercentText.innerText = `${data.progress_percentage}%`;
  
  if (data.logs && data.logs.length > 0) {
    elements.logTerminal.innerHTML = data.logs.map(l => `<div>${escapeHtml(l)}</div>`).join('');
    elements.logTerminal.scrollTop = elements.logTerminal.scrollHeight;
  }
  
  if (data.status === 'completed' || data.status === 'error') {
    elements.btnStartCampaign.disabled = false;
    elements.btnStartCampaign.innerHTML = `🚀 Start Autonomous Lead Agent`;
    fetchStats();
    fetchLeads();
    if (data.status === 'completed') {
      showToast('Lead generation campaign finished!', 'success');
    }
  }
}

function addLog(logText) {
  const div = document.createElement('div');
  div.innerText = logText;
  elements.logTerminal.appendChild(div);
  elements.logTerminal.scrollTop = elements.logTerminal.scrollHeight;
}

// Event Listeners
function setupEventListeners() {
  // Privacy Toggle
  elements.privacyToggleBtn.addEventListener('click', togglePrivacyMode);

  // Tag pills
  document.querySelectorAll('.tag-pill').forEach(pill => {
    pill.addEventListener('click', (e) => {
      elements.nicheInput.value = e.target.getAttribute('data-tag');
    });
  });

  // Tier buttons
  document.querySelectorAll('.tier-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.tier-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.targetCount = parseInt(btn.getAttribute('data-count'), 10);
    });
  });

  // Start campaign
  elements.btnStartCampaign.addEventListener('click', startCampaign);

  // Filter tabs
  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      state.activeFilter = tab.getAttribute('data-filter');
      renderLeadsTable();
    });
  });
}

function togglePrivacyMode() {
  state.privacyMode = !state.privacyMode;
  elements.privacyToggleBtn.classList.toggle('active', state.privacyMode);
  elements.privacyToggleBtn.innerHTML = state.privacyMode ? '🔒 Privacy Mode: ON' : '👁️ Privacy Mode: OFF';
  fetchLeads();
}

// API Calls
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    state.stats = data;
    elements.statTotalLeads.innerText = data.total_leads || 0;
    elements.statDeliverableEmails.innerText = data.deliverable_emails || 0;
    elements.statPixelLeaks.innerText = data.pixel_leaks || 0;
    elements.statApprovedQueue.innerText = data.approved_queue || 0;
    elements.statSentEmails.innerText = data.sent_emails || 0;
  } catch (e) {
    console.error('Failed to fetch stats:', e);
  }
}

async function fetchLeads() {
  try {
    const res = await fetch(`/api/leads?privacy_mode=${state.privacyMode}`);
    const data = await res.json();
    state.leads = data;
    renderLeadsTable();
  } catch (e) {
    console.error('Failed to fetch leads:', e);
  }
}

async function startCampaign() {
  const niche = elements.nicheInput.value.trim();
  if (!niche) {
    showToast('Please enter a niche keyword (e.g. Shoes, Streetwear, Cosmetics)', 'error');
    return;
  }

  const payload = {
    niche: niche,
    platform: elements.platformSelect.value,
    country: elements.countrySelect.value,
    target_count: state.targetCount
  };

  elements.btnStartCampaign.disabled = true;
  elements.btnStartCampaign.innerHTML = `<span>⏳ Agent Working...</span>`;
  elements.progressContainer.style.display = 'block';
  elements.logTerminal.innerHTML = '<div>Initiating discovery engine...</div>';

  try {
    const res = await fetch('/api/campaign/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    showToast('Campaign started! Discovering stores...', 'success');
  } catch (e) {
    showToast('Failed to start campaign: ' + e.message, 'error');
    elements.btnStartCampaign.disabled = false;
    elements.btnStartCampaign.innerHTML = `🚀 Start Autonomous Lead Agent`;
  }
}

// Render Table
function renderLeadsTable() {
  let filtered = [...state.leads];

  if (state.activeFilter === 'ready_for_review') {
    filtered = filtered.filter(l => l.email && l.review_status === 'pending');
  } else if (state.activeFilter === 'pixel_leaks') {
    filtered = filtered.filter(l => !l.has_meta_pixel);
  } else if (state.activeFilter === 'approved') {
    filtered = filtered.filter(l => l.review_status === 'approved');
  } else if (state.activeFilter === 'sent') {
    filtered = filtered.filter(l => l.review_status === 'sent');
  }

  if (filtered.length === 0) {
    elements.leadsTableBody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; padding: 2.5rem; color: var(--text-muted);">
          No leads found in this view. Click <strong>"Start Autonomous Lead Agent"</strong> to harvest leads.
        </td>
      </tr>
    `;
    return;
  }

  elements.leadsTableBody.innerHTML = filtered.map(lead => {
    const hasEmail = !!lead.email;
    const emailDisplay = hasEmail 
      ? `<span class="badge badge-emerald">📧 ${escapeHtml(lead.email)}</span>`
      : `<span class="badge badge-rose">No public email</span>`;

    const pixelBadge = lead.has_meta_pixel
      ? `<span class="badge badge-emerald">Meta Pixel Active</span>`
      : `<span class="badge badge-rose">❌ Missing Meta Pixel</span>`;

    let statusBadge = `<span class="badge badge-indigo">Pending Review</span>`;
    if (lead.review_status === 'approved') statusBadge = `<span class="badge badge-emerald">✓ Approved</span>`;
    if (lead.review_status === 'sent') statusBadge = `<span class="badge badge-emerald" style="background: rgba(16,185,129,0.25);">✉️ Sent</span>`;
    if (lead.review_status === 'failed') statusBadge = `<span class="badge badge-rose">Failed</span>`;
    if (lead.review_status === 'rejected') statusBadge = `<span class="badge badge-rose">Skipped</span>`;

    const pitchCount = (lead.pitch_variants && lead.pitch_variants.length) || 0;

    return `
      <tr>
        <td>
          <div style="font-weight: 700;">${escapeHtml(lead.store_name || lead.domain)}</div>
          <a href="${escapeHtml(lead.url)}" target="_blank" style="font-size: 0.75rem; color: var(--cyan); text-decoration: none;">${escapeHtml(lead.domain)} ↗</a>
        </td>
        <td>
          <span class="badge badge-indigo">${escapeHtml(lead.platform)}</span>
          <span style="font-size: 0.75rem; color: var(--text-dim); display:block; margin-top:2px;">${escapeHtml(lead.country)}</span>
        </td>
        <td>${emailDisplay}</td>
        <td>${pixelBadge}</td>
        <td>
          <div style="font-size: 0.8rem; max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(lead.primary_opportunity || '')}">
            ${escapeHtml(lead.primary_opportunity || 'N/A')}
          </div>
          ${pitchCount > 0 ? `<span style="font-size:0.7rem; color: var(--primary);">✨ ${pitchCount} AI Pitches Ready</span>` : ''}
        </td>
        <td>${statusBadge}</td>
        <td>
          <div style="display:flex; gap:0.4rem;">
            ${hasEmail ? `<button class="btn-secondary" style="padding: 0.35rem 0.65rem; font-size:0.75rem;" onclick="openReviewModal(${lead.id})">🔍 Review Pitch</button>` : ''}
            ${hasEmail && lead.review_status !== 'sent' ? `<button class="btn-secondary" style="padding: 0.35rem 0.65rem; font-size:0.75rem; color:var(--emerald); border-color:var(--emerald);" onclick="quickApprove(${lead.id})">✓ Approve</button>` : ''}
            <button class="btn-secondary" style="padding: 0.35rem 0.5rem; font-size:0.75rem; color:var(--rose); border-color:rgba(244,63,94,0.3);" onclick="deleteLeadAction(${lead.id})" title="Delete lead">🗑️</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// Modal Review & Multi-Pitch Selector
function openReviewModal(leadId) {
  const lead = state.leads.find(l => l.id === leadId);
  if (!lead) return;

  state.selectedLead = JSON.parse(JSON.stringify(lead));
  state.activeVariantIndex = lead.selected_pitch_index || 0;

  document.getElementById('modal-store-name').innerText = lead.store_name || lead.domain;
  document.getElementById('modal-domain').innerText = lead.domain;
  document.getElementById('modal-opportunity').innerText = lead.primary_opportunity || 'CRO & ROAS Scaling';
  document.getElementById('modal-recipient').innerText = lead.email || 'No email found';

  renderModalVariants();
  elements.reviewModal.classList.add('open');
}

function closeReviewModal() {
  elements.reviewModal.classList.remove('open');
  state.selectedLead = null;
}

function renderModalVariants() {
  const variants = state.selectedLead.pitch_variants || [];
  const container = document.getElementById('modal-variant-pills');

  if (variants.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem;">Standard pitch ready</div>';
    document.getElementById('modal-subject-input').value = `Growth idea for ${state.selectedLead.store_name}`;
    document.getElementById('modal-body-input').value = `Hi ${state.selectedLead.store_name} team,\n\nI was looking at your store and noticed an opportunity to scale your ROAS.\n\nBest,\nTalha Yousaf\nDigital Marketer & E-Commerce Specialist`;
    return;
  }

  container.innerHTML = variants.map((v, idx) => `
    <div class="pitch-variant-pill ${idx === state.activeVariantIndex ? 'active' : ''}" onclick="selectVariant(${idx})">
      Variant ${idx + 1}: ${escapeHtml(v.angle)}
    </div>
  `).join('');

  const activeVar = variants[state.activeVariantIndex] || variants[0];
  document.getElementById('modal-subject-input').value = activeVar.subject || '';
  document.getElementById('modal-body-input').value = activeVar.body || '';
}

function selectVariant(idx) {
  saveCurrentModalEdits();
  state.activeVariantIndex = idx;
  renderModalVariants();
}

function saveCurrentModalEdits() {
  if (!state.selectedLead || !state.selectedLead.pitch_variants) return;
  const currSub = document.getElementById('modal-subject-input').value;
  const currBody = document.getElementById('modal-body-input').value;
  
  if (state.selectedLead.pitch_variants[state.activeVariantIndex]) {
    state.selectedLead.pitch_variants[state.activeVariantIndex].subject = currSub;
    state.selectedLead.pitch_variants[state.activeVariantIndex].body = currBody;
  }
}

async function approveModalLead() {
  saveCurrentModalEdits();
  const leadId = state.selectedLead.id;
  
  try {
    await fetch(`/api/leads/${leadId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: 'approved',
        selected_pitch_index: state.activeVariantIndex,
        pitch_variants: state.selectedLead.pitch_variants
      })
    });
    showToast(`Approved ${state.selectedLead.store_name} for outreach queue!`, 'success');
    closeReviewModal();
    fetchStats();
    fetchLeads();
  } catch (e) {
    showToast('Failed to approve lead: ' + e.message, 'error');
  }
}

async function quickApprove(leadId) {
  try {
    await fetch(`/api/leads/${leadId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'approved' })
    });
    showToast('Lead marked as Approved ✓', 'success');
    fetchStats();
    fetchLeads();
  } catch (e) {
    showToast('Failed to approve: ' + e.message, 'error');
  }
}

async function deleteLeadAction(leadId) {
  if (!confirm('Are you sure you want to delete this lead?')) return;
  try {
    const res = await fetch(`/api/leads/${leadId}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Lead deleted successfully', 'success');
      fetchStats();
      fetchLeads();
    } else {
      showToast('Failed to delete lead', 'error');
    }
  } catch (e) {
    showToast('Delete error: ' + e.message, 'error');
  }
}

async function pruneDatabaseAction() {
  if (!confirm('Clean database by removing non-store/agency domains and dummy placeholder emails?')) return;
  try {
    const res = await fetch('/api/leads/prune', { method: 'POST' });
    const data = await res.json();
    showToast(data.message || `Pruned ${data.pruned_count} invalid records`, 'success');
    fetchStats();
    fetchLeads();
  } catch (e) {
    showToast('Prune error: ' + e.message, 'error');
  }
}

async function sendModalLeadNow() {
  saveCurrentModalEdits();
  const leadId = state.selectedLead.id;
  const subj = document.getElementById('modal-subject-input').value;
  const body = document.getElementById('modal-body-input').value;
  const btn = document.getElementById('btn-modal-send');

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳ Sending Email...</span>`;
  }

  try {
    const res = await fetch('/api/outreach/send-single', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lead_id: leadId,
        variant_id: state.activeVariantIndex,
        custom_subject: subj,
        custom_body: body
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Email successfully delivered to ${state.selectedLead.store_name}! 🚀`, 'success');
      if (btn) btn.innerHTML = `<span>✅ Email Sent!</span>`;
      setTimeout(() => {
        closeReviewModal();
        fetchStats();
        fetchLeads();
      }, 1000);
    } else {
      showToast('Error sending email: ' + data.error, 'error');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<span>✉️ Send Right Now (1-Click)</span>`;
      }
    }
  } catch (e) {
    showToast('Send failed: ' + e.message, 'error');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>✉️ Send Right Now (1-Click)</span>`;
    }
  }
}

async function sendAllApprovedBatch() {
  const approvedLeads = state.leads.filter(l => l.review_status === 'approved' && l.email);
  if (approvedLeads.length === 0) {
    showToast('No leads currently marked as Approved. Click "Approve" first.', 'error');
    return;
  }

  try {
    const res = await fetch('/api/outreach/send-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lead_ids: approvedLeads.map(l => l.id),
        delay_seconds: 30
      })
    });
    const data = await res.json();
    showToast(data.message, 'success');
  } catch (e) {
    showToast('Batch send failed: ' + e.message, 'error');
  }
}

// Test Email Modal
function openTestEmailModal() {
  elements.testEmailModal.classList.add('open');
}

function closeTestEmailModal() {
  elements.testEmailModal.classList.remove('open');
}

async function sendTestEmailAction() {
  const target = document.getElementById('test-email-target').value.trim();
  if (!target) {
    showToast('Please enter a test email address.', 'error');
    return;
  }

  const btn = document.getElementById('btn-send-test-email');
  btn.disabled = true;
  btn.innerText = 'Sending test...';

  try {
    const res = await fetch('/api/outreach/test-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_email: target,
        subject: 'Live Outreach Verification - Talha Yousaf Agent',
        message: 'Hello Talha,\n\nThis is a verified test email dispatched from your autonomous lead generation platform.\n\nEverything is properly configured and ready for live client outreach!'
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Test email delivered to ${target}!`, 'success');
      closeTestEmailModal();
    } else {
      showToast(`SMTP Error: ${data.error}`, 'error');
    }
  } catch (e) {
    showToast('Test failed: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerText = 'Send Test Email';
  }
}

// Exports
function exportCSV() {
  window.location.href = `/api/export/csv?privacy_mode=${state.privacyMode}`;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
