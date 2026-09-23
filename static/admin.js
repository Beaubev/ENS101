/* ENS 101 App - 1.0 — Staff Admin Logic */

(function () {
  'use strict';

  // In-memory state only (never stored in localStorage)
  let adminPassword = null;
  let allSuggestions = [];
  let activeStatusFilter = 'all';
  let activeCategoryFilter = 'all';
  let searchQuery = '';

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function showToast(message, duration = 3200) {
    const toast = $('#admin-toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => toast.classList.remove('show'), duration);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Authentication
  async function handleLogin(event) {
    event.preventDefault();
    const pwdInput = $('#admin-password');
    const submitBtn = $('#login-submit-btn');
    const errorEl = $('#login-error');
    const password = pwdInput.value;

    errorEl.hidden = true;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Verifying…';

    try {
      const resp = await fetch('/api/admin/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.error || 'Incorrect admin password.');
      }

      adminPassword = password;
      pwdInput.value = '';
      setAuthenticatedUI(true);
      await fetchSuggestions();
      showToast('Signed in to Staff Admin.');
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.hidden = false;
      pwdInput.focus();
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sign In';
    }
  }

  function handleLogout() {
    adminPassword = null;
    allSuggestions = [];
    setAuthenticatedUI(false);
    showToast('Signed out of Staff Admin.');
  }

  function setAuthenticatedUI(isAuth) {
    const statusDot = $('#admin-status-dot');
    const statusLabel = $('#admin-status-label');
    const loginPanel = $('#login-panel');
    const adminWorkspace = $('#admin-workspace');

    if (isAuth) {
      statusDot.className = 'status-dot unlocked';
      statusLabel.textContent = 'Unlocked';
      loginPanel.hidden = true;
      adminWorkspace.hidden = false;
    } else {
      statusDot.className = 'status-dot locked';
      statusLabel.textContent = 'Locked';
      loginPanel.hidden = false;
      adminWorkspace.hidden = true;
      $('#admin-password').value = '';
    }
  }

  // Data Fetching
  async function fetchSuggestions() {
    if (!adminPassword) return;

    const container = $('#suggestions-container');
    container.innerHTML = '<div class="loading-state">Loading suggestions…</div>';

    try {
      const resp = await fetch('/api/admin/suggestions', {
        method: 'GET',
        headers: { 'X-ENS101-Admin': adminPassword },
      });

      if (resp.status === 401) {
        handleLogout();
        showToast('Admin session expired or password incorrect.');
        return;
      }

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.error || 'Failed to load suggestions.');
      }

      allSuggestions = data.suggestions || [];
      updateMetrics(data.stats || {});
      renderSuggestions();
    } catch (err) {
      container.innerHTML = `<div class="empty-state">Error loading suggestions: ${escapeHtml(err.message)}</div>`;
      showToast(err.message);
    }
  }

  function updateMetrics(stats) {
    $('#metric-total').textContent = stats.total || 0;
    $('#metric-pending').textContent = stats.pending || 0;
    $('#metric-in-progress').textContent = stats.in_progress || 0;
    $('#metric-implemented').textContent = stats.implemented || 0;
    $('#metric-dismissed').textContent = stats.dismissed || 0;

    $('#count-all').textContent = stats.total || 0;
    $('#count-pending').textContent = stats.pending || 0;
    $('#count-in_progress').textContent = stats.in_progress || 0;
    $('#count-implemented').textContent = stats.implemented || 0;
    $('#count-dismissed').textContent = stats.dismissed || 0;
  }

  // Filtering & Rendering
  function getFilteredSuggestions() {
    return allSuggestions.filter((item) => {
      // Status filter
      if (activeStatusFilter !== 'all' && item.status !== activeStatusFilter) {
        return false;
      }
      // Category filter
      if (activeCategoryFilter !== 'all' && item.category !== activeCategoryFilter) {
        return false;
      }
      // Search query
      if (searchQuery) {
        const text = [
          item.suggestion || '',
          item.submitter || '',
          item.category || '',
          item.admin_notes || '',
        ].join(' ').toLowerCase();
        if (!text.includes(searchQuery)) {
          return false;
        }
      }
      return true;
    });
  }

  function renderSuggestions() {
    const container = $('#suggestions-container');
    const filtered = getFilteredSuggestions();

    if (filtered.length === 0) {
      container.innerHTML = '<div class="empty-state">No suggestions match the selected filters.</div>';
      return;
    }

    container.innerHTML = filtered.map((item) => renderSuggestionCard(item)).join('');
    bindCardEvents();
  }

  function formatStatusBadge(status) {
    const labels = {
      pending: '⏳ Pending',
      in_progress: '⚡ In Progress',
      implemented: '✓ Implemented',
      dismissed: '✕ Dismissed',
    };
    return `<span class="status-badge status-${escapeHtml(status)}">${labels[status] || escapeHtml(status)}</span>`;
  }

  function renderSuggestionCard(item) {
    const submitter = item.submitter ? escapeHtml(item.submitter) : 'Anonymous Mentor';
    const category = escapeHtml(item.category || 'General');
    const timeStr = item.created_at ? escapeHtml(item.created_at) : '';
    const suggestionText = escapeHtml(item.suggestion || '');
    const notes = item.admin_notes ? escapeHtml(item.admin_notes) : '';
    const status = item.status || 'pending';

    let implementationHtml = '';
    if (notes || status === 'implemented') {
      const isImplemented = status === 'implemented';
      const label = isImplemented ? 'Implementation Notes' : 'Staff Notes';
      const boxClass = isImplemented ? 'implementation-box' : 'implementation-box in-progress-box';
      const dateNotice = item.implemented_at ? `<span class="implementation-date">Implemented on ${escapeHtml(item.implemented_at)}</span>` : '';
      implementationHtml = `
        <div class="${boxClass}">
          <div class="implementation-header">
            <span class="implementation-label">${label}</span>
            ${dateNotice}
          </div>
          <p class="implementation-text">${notes || '<em>Marked implemented with no additional notes.</em>'}</p>
        </div>
      `;
    }

    // Action buttons based on status
    let actionButtons = '';
    if (status === 'pending') {
      actionButtons = `
        <button class="btn-action btn-progress" data-action="progress" data-id="${item.id}">Start Progress</button>
        <button class="btn-action btn-implement" data-action="implement" data-id="${item.id}">Mark Implemented</button>
        <button class="btn-action btn-dismiss" data-action="dismiss" data-id="${item.id}">Dismiss</button>
      `;
    } else if (status === 'in_progress') {
      actionButtons = `
        <button class="btn-action btn-implement" data-action="implement" data-id="${item.id}">Mark Implemented</button>
        <button class="btn-action btn-notes" data-action="edit-notes" data-id="${item.id}">Update Notes</button>
        <button class="btn-action btn-reopen" data-action="reopen" data-id="${item.id}">Back to Pending</button>
        <button class="btn-action btn-dismiss" data-action="dismiss" data-id="${item.id}">Dismiss</button>
      `;
    } else if (status === 'implemented') {
      actionButtons = `
        <button class="btn-action btn-notes" data-action="edit-notes" data-id="${item.id}">Edit Implementation Notes</button>
        <button class="btn-action btn-reopen" data-action="reopen" data-id="${item.id}">Reopen to Pending</button>
      `;
    } else if (status === 'dismissed') {
      actionButtons = `
        <button class="btn-action btn-reopen" data-action="reopen" data-id="${item.id}">Reopen to Pending</button>
      `;
    }

    return `
      <article class="suggestion-card" data-id="${item.id}">
        <div class="suggestion-header">
          <div class="suggestion-meta-left">
            <span class="submitter-name">${submitter}</span>
            <span class="category-badge">${category}</span>
            <span class="submission-time">${timeStr}</span>
          </div>
          <div class="suggestion-meta-right">
            ${formatStatusBadge(status)}
          </div>
        </div>
        <div class="suggestion-body">${suggestionText}</div>
        ${implementationHtml}
        <div class="suggestion-actions">
          <div class="action-buttons-group">
            ${actionButtons}
          </div>
          <button class="btn-delete" data-action="delete" data-id="${item.id}" title="Delete this suggestion">Delete</button>
        </div>
      </article>
    `;
  }

  function bindCardEvents() {
    $$('.btn-action, .btn-delete').forEach((btn) => {
      btn.addEventListener('click', handleCardAction);
    });
  }

  async function handleCardAction(event) {
    const btn = event.currentTarget;
    const action = btn.dataset.action;
    const id = parseInt(btn.dataset.id, 10);
    const item = allSuggestions.find((s) => s.id === id);

    if (!item) return;

    if (action === 'progress') {
      await updateSuggestionStatus(id, 'in_progress');
    } else if (action === 'implement') {
      openNotesModal(id, 'implemented', item.admin_notes || '');
    } else if (action === 'edit-notes') {
      openNotesModal(id, item.status, item.admin_notes || '');
    } else if (action === 'dismiss') {
      await updateSuggestionStatus(id, 'dismissed');
    } else if (action === 'reopen') {
      await updateSuggestionStatus(id, 'pending');
    } else if (action === 'delete') {
      if (confirm('Are you sure you want to permanently delete this suggestion?')) {
        await deleteSuggestion(id);
      }
    }
  }

  // Status & Notes Updates
  async function updateSuggestionStatus(id, status, notes = null) {
    if (!adminPassword) return;

    try {
      const payload = { id, status };
      if (notes !== null) {
        payload.admin_notes = notes;
      }

      const resp = await fetch('/api/admin/suggestions/status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-ENS101-Admin': adminPassword,
        },
        body: JSON.stringify(payload),
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.error || 'Failed to update suggestion status.');
      }

      showToast(data.message || 'Status updated.');
      await fetchSuggestions();
    } catch (err) {
      showToast(err.message || 'Error updating status.');
    }
  }

  async function deleteSuggestion(id) {
    if (!adminPassword) return;

    try {
      const resp = await fetch('/api/admin/suggestions/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-ENS101-Admin': adminPassword,
        },
        body: JSON.stringify({ id }),
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.error || 'Failed to delete suggestion.');
      }

      showToast('Suggestion deleted.');
      await fetchSuggestions();
    } catch (err) {
      showToast(err.message || 'Error deleting suggestion.');
    }
  }

  // Notes Modal
  function openNotesModal(id, targetStatus, currentNotes = '') {
    const modal = $('#notes-modal');
    $('#notes-suggestion-id').value = id;
    $('#notes-target-status').value = targetStatus;
    $('#notes-textarea').value = currentNotes;

    const titleEl = $('#notes-modal-title');
    const subtitleEl = $('#notes-modal-subtitle');

    if (targetStatus === 'implemented') {
      titleEl.textContent = 'Mark Implemented';
      subtitleEl.textContent = 'Record what was changed, updated, or deployed to address this suggestion.';
    } else {
      titleEl.textContent = 'Update Staff Notes';
      subtitleEl.textContent = 'Add internal notes or progress details regarding this suggestion.';
    }

    modal.hidden = false;
    $('#notes-textarea').focus();
  }

  function closeNotesModal() {
    $('#notes-modal').hidden = true;
  }

  async function handleNotesSubmit(event) {
    event.preventDefault();
    const id = parseInt($('#notes-suggestion-id').value, 10);
    const targetStatus = $('#notes-target-status').value;
    const notes = $('#notes-textarea').value.trim();

    closeNotesModal();
    await updateSuggestionStatus(id, targetStatus, notes);
  }

  // Change Password
  async function handleChangePassword(event) {
    event.preventDefault();
    const curPw = $('#current-pw').value;
    const newPw = $('#new-pw').value;
    const confirmPw = $('#confirm-pw').value;
    const statusEl = $('#pw-status');

    statusEl.textContent = '';
    statusEl.className = 'status-inline';

    if (newPw !== confirmPw) {
      statusEl.textContent = 'New passwords do not match.';
      statusEl.classList.add('error');
      return;
    }

    try {
      const resp = await fetch('/api/admin/password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-ENS101-Admin': adminPassword,
        },
        body: JSON.stringify({
          current_password: curPw,
          new_password: newPw,
        }),
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.error || 'Failed to update password.');
      }

      adminPassword = newPw;
      statusEl.textContent = 'Password updated successfully.';
      statusEl.classList.add('success');
      $('#current-pw').value = '';
      $('#new-pw').value = '';
      $('#confirm-pw').value = '';
      showToast('Admin password updated.');
    } catch (err) {
      statusEl.textContent = err.message;
      statusEl.classList.add('error');
    }
  }

  // Initialization & Event Listeners
  function init() {
    $('#login-form').addEventListener('submit', handleLogin);
    $('#logout-btn').addEventListener('click', handleLogout);
    $('#refresh-btn').addEventListener('click', fetchSuggestions);

    // Filter pills
    $$('.filter-pill').forEach((pill) => {
      pill.addEventListener('click', () => {
        $$('.filter-pill').forEach((p) => p.classList.remove('active'));
        pill.classList.add('active');
        activeStatusFilter = pill.dataset.status;
        renderSuggestions();
      });
    });

    // Metric cards click to filter
    $$('.metric-card').forEach((card) => {
      card.addEventListener('click', () => {
        const filter = card.dataset.filter;
        const matchingPill = $(`.filter-pill[data-status="${filter}"]`);
        if (matchingPill) matchingPill.click();
      });
    });

    // Category filter
    $('#category-filter').addEventListener('change', (e) => {
      activeCategoryFilter = e.target.value;
      renderSuggestions();
    });

    // Search filter
    $('#search-filter').addEventListener('input', (e) => {
      searchQuery = e.target.value.trim().toLowerCase();
      renderSuggestions();
    });

    // Notes modal
    $('#close-notes-modal').addEventListener('click', closeNotesModal);
    $('#cancel-notes-btn').addEventListener('click', closeNotesModal);
    $('#notes-form').addEventListener('submit', handleNotesSubmit);
    $('#notes-modal').addEventListener('click', (e) => {
      if (e.target === $('#notes-modal')) closeNotesModal();
    });

    // Change password
    $('#change-password-form').addEventListener('submit', handleChangePassword);

    // Esc key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeNotesModal();
      }
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
