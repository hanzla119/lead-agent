// Application State
let state = {
  privacyMode: false,
  activeFilter: 'all',
  searchQuery: '',
  filterValueTier: 'all',
  filterChannel: 'all',
  filterTechGap: 'all',
  filterSort: 'lead_score',
  leads: [],
  stats: {},
  targetCount: 10,
  selectedLead: null,
  activeVariantIndex: 0,
  activeModalChannel: 'email',
  ws: null,
  searchDebounceTimer: null
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
  statGoogleGaps: document.getElementById('stat-google-gaps'),
  statHotLeads: document.getElementById('stat-hot-leads'),
  statSentEmails: document.getElementById('stat-sent-emails'),
  privacyToggleBtn: document.getElementById('privacy-toggle-btn'),
  searchQueryInput: document.getElementById('search-query-input'),
  searchClearBtn: document.getElementById('search-clear-btn'),
  filterValueTier: document.getElementById('filter-value-tier'),
  filterChannel: document.getElementById('filter-channel'),
  filterTechGap: document.getElementById('filter-tech-gap'),
  filterSort: document.getElementById('filter-sort'),
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
      triggerSearchFilter();
    });
  });

  // Instant Search Input with debounce
  if (elements.searchQueryInput) {
    elements.searchQueryInput.addEventListener('input', (e) => {
      const val = e.target.value;
      state.searchQuery = val;
      if (elements.searchClearBtn) {
        elements.searchClearBtn.style.display = val ? 'block' : 'none';
      }
      clearTimeout(state.searchDebounceTimer);
      state.searchDebounceTimer = setTimeout(() => {
        triggerSearchFilter();
      }, 200);
    });
  }
}

function clearSearch() {
  if (elements.searchQueryInput) {
    elements.searchQueryInput.value = '';
    state.searchQuery = '';
    elements.searchClearBtn.style.display = 'none';
    triggerSearchFilter();
  }
}

function togglePrivacyMode() {
  state.privacyMode = !state.privacyMode;
  elements.privacyToggleBtn.classList.toggle('active', state.privacyMode);
  elements.privacyToggleBtn.innerHTML = state.privacyMode ? '🔒 Privacy Mode: ON' : '👁️ Privacy Mode: OFF';
  triggerSearchFilter();
}

// API Calls
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    state.stats = data;
    if (elements.statTotalLeads) elements.statTotalLeads.innerText = data.total_leads || 0;
    if (elements.statDeliverableEmails) elements.statDeliverableEmails.innerText = data.deliverable_emails || 0;
    if (elements.statGoogleGaps) elements.statGoogleGaps.innerText = data.google_ads_gaps || 0;
    if (elements.statHotLeads) elements.statHotLeads.innerText = data.hot_leads || 0;
    if (elements.statSentEmails) elements.statSentEmails.innerText = data.sent_emails || 0;
  } catch (e) {
    console.error('Failed to fetch stats:', e);
  }
}

async function fetchLeads() {
  triggerSearchFilter();
}

async function triggerSearchFilter() {
  const query = state.searchQuery.trim();
  const valueTier = elements.filterValueTier ? elements.filterValueTier.value : 'all';
  const channel = elements.filterChannel ? elements.filterChannel.value : 'all';
  const techGap = elements.filterTechGap ? elements.filterTechGap.value : 'all';
  const sortBy = elements.filterSort ? elements.filterSort.value : 'lead_score';
  const status = state.activeFilter;

  // Build query params
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (valueTier !== 'all') params.append('value_tier', valueTier);
  if (channel !== 'all') params.append('channel', channel);
  if (status !== 'all') params.append('status', status);
  if (techGap === 'google_ads_gaps') params.append('has_google_ads', 'false');
  if (techGap === 'pixel_leaks') params.append('has_meta_pixel', 'false');
  params.append('sort_by', sortBy);
  params.append('privacy_mode', state.privacyMode);

  try {
    const res = await fetch(`/api/leads/search?${params.toString()}`);
    const data = await res.json();
    state.leads = data;
    renderLeadsTable();
  } catch (e) {
    console.error('Failed to search leads:', e);
  }
}

async function startCampaign() {
  const niche = elements.nicheInput.value.trim();
  if (!niche) {
    showToast('Please enter a niche keyword (e.g. Shoes, Streetwear, Jewelry, Cosmetics)', 'error');
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
    showToast('Campaign started! Discovering stores & analyzing tracking gaps...', 'success');
  } catch (e) {
    showToast('Failed to start campaign: ' + e.message, 'error');
    elements.btnStartCampaign.disabled = false;
    elements.btnStartCampaign.innerHTML = `🚀 Start Autonomous Lead Agent`;
  }
}

// Render Table
function renderLeadsTable() {
  const leads = state.leads || [];

  if (leads.length === 0) {
    elements.leadsTableBody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; padding: 2.5rem; color: var(--text-muted);">
          No leads matching your search/filters. Click <strong>"Start Autonomous Lead Agent"</strong> to harvest high-converting leads.
        </td>
      </tr>
    `;
    return;
  }

  elements.leadsTableBody.innerHTML = leads.map(lead => {
    const hasEmail = !!lead.email;
    const score = lead.lead_score || 50;
    const tier = lead.lead_tier || 'Silver';
    const estRev = lead.est_monthly_revenue || '$10k-$50k';

    // Score Badge
    const scoreClass = score >= 70 ? 'score-hot' : 'score-warm';
    const scoreDisplay = `
      <div style="display:flex; flex-direction:column; gap:0.25rem;">
        <div><span class="score-badge ${scoreClass}">🔥 ${score}/100</span></div>
        <span class="badge ${tier === 'Gold' || tier === 'Platinum' ? 'tier-tag-gold' : 'badge-indigo'}" style="font-size:0.7rem;">
          ${escapeHtml(tier)} (${escapeHtml(estRev)})
        </span>
      </div>
    `;

    // Decision-Maker & Social Profiles
    const founderDisplay = lead.founder_name 
      ? `<div style="font-weight:700; color:#fff; font-size:0.85rem;">👤 ${escapeHtml(lead.founder_name)}</div>`
      : `<div style="color:var(--text-dim); font-size:0.75rem;">👤 Founder / Owner</div>`;

    const emailBadge = hasEmail 
      ? `<div style="font-size:0.75rem; color:var(--emerald); margin-top:2px;">📧 ${escapeHtml(lead.email)}</div>`
      : `<div style="font-size:0.75rem; color:var(--rose); margin-top:2px;">No email</div>`;

    const socialLinks = [];
    if (lead.linkedin) socialLinks.push(`<a href="${escapeHtml(lead.linkedin)}" target="_blank" class="channel-icon-link" title="LinkedIn Profile">💼</a>`);
    if (lead.instagram) socialLinks.push(`<a href="${escapeHtml(lead.instagram)}" target="_blank" class="channel-icon-link" title="Instagram Profile">📸</a>`);
    if (lead.facebook) socialLinks.push(`<a href="${escapeHtml(lead.facebook)}" target="_blank" class="channel-icon-link" title="Facebook Page">📘</a>`);
    if (lead.reddit_username) socialLinks.push(`<a href="https://reddit.com/user/${escapeHtml(lead.reddit_username)}" target="_blank" class="channel-icon-link" title="Reddit User">💬</a>`);

    const socialDisplay = socialLinks.length > 0
      ? `<div style="display:flex; gap:0.3rem; margin-top:0.35rem;">${socialLinks.join('')}</div>`
      : '';

    // Tech Audit Badges
    const googleAdsBadge = lead.has_google_ads
      ? `<span class="badge badge-emerald" style="font-size:0.68rem;">Google Ads Active</span>`
      : `<span class="badge badge-rose" style="font-size:0.68rem;" title="Missing Google Shopping & Search ad capture">❌ No Google Ads</span>`;

    const pixelBadge = lead.has_meta_pixel
      ? `<span class="badge badge-emerald" style="font-size:0.68rem;">Meta Pixel</span>`
      : `<span class="badge badge-rose" style="font-size:0.68rem;">❌ Pixel Leak</span>`;

    // Status Badge
    let statusBadge = `<span class="badge badge-indigo">Pending</span>`;
    if (lead.review_status === 'approved') statusBadge = `<span class="badge badge-emerald">✓ Approved</span>`;
    if (lead.review_status === 'sent') statusBadge = `<span class="badge badge-emerald" style="background: rgba(16,185,129,0.25);">✉️ Sent</span>`;
    if (lead.review_status === 'failed') statusBadge = `<span class="badge badge-rose">Failed</span>`;

    return `
      <tr>
        <td>
          <div style="font-weight: 700; font-size:0.9rem;">${escapeHtml(lead.store_name || lead.domain)}</div>
          <a href="${escapeHtml(lead.url)}" target="_blank" style="font-size: 0.75rem; color: var(--cyan); text-decoration: none;">${escapeHtml(lead.domain)} ↗</a>
          <div style="font-size:0.7rem; color:var(--text-dim); margin-top:2px;">${escapeHtml(lead.platform)} • ${escapeHtml(lead.country)}</div>
        </td>
        <td>${scoreDisplay}</td>
        <td>
          ${founderDisplay}
          ${emailBadge}
          ${socialDisplay}
        </td>
        <td>
          <div style="display:flex; flex-direction:column; gap:0.25rem;">
            ${googleAdsBadge}
            ${pixelBadge}
          </div>
        </td>
        <td>
          <div style="font-size: 0.78rem; max-width: 220px; color: var(--text-main); font-weight:600; line-height:1.3;" title="${escapeHtml(lead.primary_opportunity || '')}">
            ${escapeHtml(lead.primary_opportunity || 'Scale $10k->$30k/mo in 45 days via Google Ads')}
          </div>
          <span style="font-size:0.68rem; color: var(--cyan); display:block; margin-top:3px;">🎯 45-Day 0.5-2x ROAS Hook</span>
        </td>
        <td>${statusBadge}</td>
        <td>
          <div style="display:flex; gap:0.35rem; flex-wrap:wrap;">
            <button class="btn-secondary" style="padding: 0.35rem 0.65rem; font-size:0.75rem;" onclick="openReviewModal(${lead.id})">🔍 Pitch Suite</button>
            ${hasEmail && lead.review_status !== 'sent' ? `<button class="btn-secondary" style="padding: 0.35rem 0.65rem; font-size:0.75rem; color:var(--emerald); border-color:var(--emerald);" onclick="quickApprove(${lead.id})">✓</button>` : ''}
            <button class="btn-secondary" style="padding: 0.35rem 0.5rem; font-size:0.75rem; color:var(--rose); border-color:rgba(244,63,94,0.3);" onclick="deleteLeadAction(${lead.id})" title="Delete lead">🗑️</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// Multi-Channel Modal Controller
function openReviewModal(leadId) {
  const lead = state.leads.find(l => l.id === leadId);
  if (!lead) return;

  state.selectedLead = JSON.parse(JSON.stringify(lead));
  state.activeVariantIndex = lead.selected_pitch_index || 0;

  // Header & Badges
  document.getElementById('modal-store-name').innerText = lead.store_name || lead.domain;
  document.getElementById('modal-domain').innerText = lead.domain;
  document.getElementById('modal-opportunity').innerText = lead.primary_opportunity || 'Scale Shopify store from $10k to $30k/mo in 45 days (0.5–2x ROAS boost)';
  document.getElementById('modal-founder').innerText = lead.founder_name || 'Founder / Owner';
  document.getElementById('modal-recipient').innerText = lead.email || 'No email (Use LinkedIn/IG)';
  document.getElementById('modal-tier-badge').innerText = `${lead.lead_tier || 'Silver'} Tier (${lead.est_monthly_revenue || '$10k-$50k'})`;
  document.getElementById('modal-score-badge').innerText = `Score: ${lead.lead_score || 50}/100`;

  // Render Multi-Channel Copies
  renderModalVariants();
  populateSocialChannels();
  switchModalChannel('email');

  elements.reviewModal.classList.add('open');
}

function closeReviewModal() {
  elements.reviewModal.classList.remove('open');
  state.selectedLead = null;
}

function switchModalChannel(channel) {
  state.activeModalChannel = channel;
  
  // Update Tab buttons
  document.querySelectorAll('.channel-tab').forEach(tab => {
    tab.classList.toggle('active', tab.getAttribute('data-channel') === channel);
  });

  // Toggle Content Blocks
  ['email', 'linkedin', 'instagram', 'reddit', 'loom'].forEach(ch => {
    const el = document.getElementById(`channel-content-${ch}`);
    if (el) el.style.display = ch === channel ? 'block' : 'none';
  });
}

function populateSocialChannels() {
  const lead = state.selectedLead;
  const multi = lead.multi_channel_pitches || {};
  const founder = lead.founder_name || 'there';
  const store = lead.store_name || lead.domain;
  const niche = lead.niche || 'e-commerce';
  const country = lead.country || 'UK';

  // LinkedIn
  const liNote = (multi.linkedin && multi.linkedin.connection_note) || 
    `Hey ${founder}, loved ${store}'s ${niche} collection! We help Shopify brands at ~$10k/mo scale to $30k/mo in 45 days via Google Ads (0.5-2x ROAS boost guaranteed). Would love to connect and share a 2-min breakdown!`;
  const liInmail = (multi.linkedin && multi.linkedin.inmail) || 
    `Hey ${founder}, thanks for connecting! Put together a 2-min breakdown showing how ${store} can capture high-intent Google Shopping traffic in ${country} with a guaranteed ROAS lift. Would it be okay to drop the link here?`;

  document.getElementById('modal-linkedin-note').value = liNote;
  document.getElementById('modal-linkedin-inmail').value = liInmail;

  // Instagram
  const igDm = (multi.instagram && multi.instagram.dm_script) || 
    `Hey team! Loved your ${niche} collection 🙌 Quick question: are you guys currently capturing high-intent search buyers on Google Shopping? We guarantee scaling Shopify stores from $10k to $30k/mo within 45 days (0.5x-2x ROAS boost). Would you be open to a 2-min breakdown showing how?`;
  document.getElementById('modal-instagram-dm').value = igDm;

  // Reddit
  const redditDm = (multi.reddit && multi.reddit.dm_pitch) || 
    `Hey! Saw your post regarding scaling your Shopify store and managing ad performance. One thing that consistently helps our e-com clients scale from $10k/mo to $30k/mo in 45 days is capturing search intent via Google Shopping/PMax with a 0.5-2x ROAS boost. Happy to share our 3-step roadmap if helpful—no pitch, just actionable steps.`;
  document.getElementById('modal-reddit-dm').value = redditDm;

  // Loom Video Script
  const loomScript = (multi.loom_script && multi.loom_script.video_outline) || 
    `1. (0-5s) Showcase ${store}'s top product & compliment aesthetic.\n2. (5-15s) Show Google Search results where competitors in ${niche} are bidding on their keywords.\n3. (15-25s) Present the 45-day roadmap: Google Shopping feed optimization + PMax scale to go from $10k to $30k/mo with 0.5-2x ROAS guarantee.\n4. (25-30s) Call to action: 'Let me know if you'd like me to send the full keyword map.'`;
  document.getElementById('modal-loom-script').value = loomScript;
}

function copyChannelText(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  
  el.select();
  navigator.clipboard.writeText(el.value).then(() => {
    showToast('Copied to clipboard! 📋 Paste directly into chat/outreach', 'success');
  }).catch(() => {
    showToast('Copy failed, please select and copy manually', 'error');
  });
}

function renderModalVariants() {
  const variants = state.selectedLead.pitch_variants || [];
  const container = document.getElementById('modal-variant-pills');

  if (variants.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem;">Standard 45-Day Google Ads scaling pitch ready</div>';
    document.getElementById('modal-subject-input').value = `scaling ${state.selectedLead.store_name} from $10k to $30k/mo in 45 days (Google Ads)?`;
    document.getElementById('modal-body-input').value = `Hi ${state.selectedLead.founder_name || state.selectedLead.store_name},\n\nWe specialize in scaling Shopify brands from ~$10k/month to $30k/month within 45 days through high-intent Google Shopping & Search Ads (guaranteed 0.5x–2x ROAS increase, or we work free).\n\nMind if I send over a quick 2-minute video breakdown of how your top competitors are capturing your search sales?\n\nBest regards,\nTalha Yousaf\nDigital Marketer & Shopify Growth Specialist`;
    return;
  }

  container.innerHTML = variants.map((v, idx) => `
    <div class="pitch-variant-pill ${idx === state.activeVariantIndex ? 'active' : ''}" onclick="selectVariant(${idx})">
      ${idx === 0 ? '🎯 Flagship: ' : `Angle ${idx + 1}: `}${escapeHtml(v.angle)}
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
    showToast(`Approved ${state.selectedLead.store_name} for batch outreach queue!`, 'success');
    closeReviewModal();
    fetchStats();
    triggerSearchFilter();
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
    triggerSearchFilter();
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
      triggerSearchFilter();
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
    triggerSearchFilter();
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
        triggerSearchFilter();
      }, 1000);
    } else {
      showToast('Error sending email: ' + data.error, 'error');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<span>✉️ Send Email Right Now (1-Click)</span>`;
      }
    }
  } catch (e) {
    showToast('Send failed: ' + e.message, 'error');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>✉️ Send Email Right Now (1-Click)</span>`;
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

