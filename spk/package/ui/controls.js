/* Connection actions go through the DSM-authenticated CGI, never to a public
 * daemon endpoint. Keep form state separate from the periodically refreshed UI. */
(function () {
  'use strict';
  const byId = (id) => document.getElementById(id);
  const form = byId('enroll-form');
  if (!form) return;
  const loginStates = ['NeedsLogin', 'LoginFailed', 'SessionExpired'];
  let busy = false;
  let refreshing = false;
  let generation = 0;
  let available = true;
  let detailsAvailable = false;
  let detailsRefreshing = false;
  let bundle = {};
  let debug = {};
  let logs = byId('recent-logs').textContent.split('\n');
  let statusWarning = false;

  function message(text, error) {
    statusWarning = false;
    byId('control-message').textContent = text;
    byId('control-message').dataset.error = error ? 'true' : 'false';
  }

  function syncControls() {
    const state = byId('status-content').dataset.state;
    const login = loginStates.includes(state);
    const secure = window.location.protocol === 'https:';
    byId('connect').hidden = state !== 'Idle';
    byId('disconnect').hidden = !['Connected', 'Connecting'].includes(state);
    byId('disconnect-note').hidden = byId('disconnect').hidden;
    form.hidden = !login;
    if (!login) byId('setup-key').value = '';
    for (const id of ['connect', 'disconnect', 'enroll-fields']) {
      byId(id).disabled = busy || !secure || !available || bundle.state === 'running';
    }
    const notice = byId('controls-unavailable');
    notice.textContent = !secure ? 'Open DSM over HTTPS to use connection controls.' :
      state === 'Unavailable' ? 'Start NetBird in Package Center to use connection controls.' : '';
    notice.hidden = !notice.textContent;
    byId('connect').textContent = busy ? 'Working…' : 'Connect';
    byId('disconnect').textContent = busy ? 'Working…' : 'Disconnect';
    byId('enroll').textContent = busy ? 'Enrolling…' : 'Enroll and connect';
    const copy = byId('copy-ip');
    if (copy) copy.disabled = false;
    byId('diagnostics-fields').disabled = busy || !secure || !available || !detailsAvailable || bundle.state === 'running';
    byId('debug-start').hidden = debug.active === true;
    byId('debug-stop').hidden = debug.active !== true;
    byId('bundle-create').disabled = bundle.state === 'running';
    byId('bundle-download').disabled = busy || !secure || !available || !bundle.download;
  }

  async function refreshStatus() {
    if (busy || refreshing) return;
    if (bundle.state === 'running') {
      await refreshDetails();
      return;
    }
    refreshing = true;
    const current = generation;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch(window.location.href, {
        credentials: 'same-origin', cache: 'no-store', signal: controller.signal
      });
      if (current !== generation || busy) return;
      if (response.status === 401 || response.status === 403) {
        available = false;
        message('Your DSM session expired or no longer has administrator access. Sign in and reopen NetBird.', true);
        return;
      }
      if (!response.ok) throw new Error('Status unavailable');
      const next = new DOMParser().parseFromString(await response.text(), 'text/html');
      if (current !== generation || busy) return;
      for (const id of ['status-content', 'external-links']) {
        const replacement = next.getElementById(id);
        if (!replacement) throw new Error('Status unavailable');
        byId(id).replaceWith(document.importNode(replacement, true));
      }
      const log = next.querySelector('#recent-logs');
      if (log && !detailsAvailable) {
        logs = log.textContent.split('\n');
        filterLogs();
      }
      available = true;
      if (statusWarning) { message('', false); statusWarning = false; }
    } catch (error) {
      if (current !== generation || busy) return;
      available = false;
      message('Unable to refresh status. Check your connection to DSM before trying another action.', true);
      statusWarning = true;
    } finally {
      clearTimeout(timer);
      refreshing = false;
      syncControls();
      await refreshDetails();
    }
  }

  async function sessionToken(signal) {
    const current = new URLSearchParams(window.location.search).get('SynoToken');
    if (current) return current;
    const response = await fetch('/webman/login.cgi', {credentials: 'same-origin', cache: 'no-store', signal});
    if (!response.ok) throw new Error('Session unavailable');
    const session = await response.json();
    if (typeof session.SynoToken !== 'string' || !session.SynoToken) throw new Error('Session unavailable');
    return session.SynoToken;
  }

  async function act(payload) {
    if (busy || !available || window.location.protocol !== 'https:') return;
    busy = true;
    generation++;
    syncControls();
    const diagnostic = payload.action.startsWith('debug-') || payload.action.startsWith('bundle-');
    const showMessage = diagnostic ? diagnosticMessage : message;
    showMessage(diagnostic ? 'Working…' : payload.action === 'enroll' ? 'Enrolling this NAS…' :
      payload.action === 'disconnect' ? 'Disconnecting…' : 'Connecting…', false);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 45000);
    try {
      const token = await sessionToken(controller.signal);
      const response = await fetch('action.cgi', {
        method: 'POST', credentials: 'same-origin', cache: 'no-store',
        headers: {'Content-Type': 'application/json', 'X-SYNO-TOKEN': token, 'X-NetBird-Action': '1'},
        body: JSON.stringify(payload), signal: controller.signal
      });
      if (payload.action === 'bundle-download' && response.ok) {
        if (response.headers.get('Content-Type') !== 'application/zip') throw new Error('Invalid download');
        const url = URL.createObjectURL(await response.blob());
        const link = document.createElement('a');
        link.href = url; link.download = 'netbird-debug.zip';
        document.body.appendChild(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 60000);
        showMessage('Debug bundle downloaded.', false);
        return;
      }
      const result = await response.json();
      if (typeof result.message !== 'string' || typeof result.ok !== 'boolean') throw new Error('Invalid response');
      showMessage(result.message, !response.ok || !result.ok);
      if (payload.action === 'bundle-create' && response.ok && result.ok) {
        diagnosticMessage('', false);
        bundle = {state: 'running'};
        renderBundle();
      }
    } catch (error) {
      showMessage(diagnostic ? 'The diagnostics request could not be confirmed. Check its status before retrying.' :
        'The request could not be confirmed. Check the connection status before retrying. If you disconnected over NetBird, reopen DSM over your LAN.', true);
    } finally {
      clearTimeout(timer);
      delete payload.setupKey;
      busy = false;
      syncControls();
      await refreshStatus();
    }
  }

  byId('connect').addEventListener('click', () => act({action: 'connect'}));
  byId('disconnect').addEventListener('click', () => {
    if (window.confirm('Disconnect this NAS from NetBird? If you are accessing DSM through NetBird, this will close your connection. Enrollment will be kept.')) {
      act({action: 'disconnect'});
    }
  });
  function syncServerSelection() {
    const selfHosted = byId('server-self-hosted').checked;
    byId('management-field').hidden = !selfHosted;
    byId('management-url').required = selfHosted;
    byId('management-url').disabled = !selfHosted;
  }
  for (const id of ['server-cloud', 'server-self-hosted']) {
    byId(id).addEventListener('change', syncServerSelection);
  }
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (busy || !available || !form.reportValidity()) return;
    const payload = {
      action: 'enroll', setupKey: byId('setup-key').value.trim(),
      managementUrl: byId('server-self-hosted').checked ? byId('management-url').value.trim() : 'https://api.netbird.io:443'
    };
    byId('setup-key').value = '';
    act(payload);
  });

  function diagnosticMessage(text, error) {
    byId('diagnostic-message').textContent = text;
    byId('diagnostic-message').dataset.error = error ? 'true' : 'false';
  }

  function filterLogs() {
    const level = byId('log-filter').value;
    const search = byId('log-search').value.toLowerCase();
    const shown = logs.filter(line => line.toLowerCase().includes(search) &&
      (level === 'all' || (level === 'errors' ? /\b(ERRO\w*|FATL|FATAL|PANI\w*)\b/ : /\b(WARN\w*|ERRO\w*|FATL|FATAL|PANI\w*)\b/).test(line)));
    const pre = byId('recent-logs');
    pre.replaceChildren();
    for (const line of shown) {
      const span = document.createElement('span');
      span.className = /\b(ERRO\w*|FATL|FATAL|PANI\w*)\b/.test(line) ? 'lvl-error' : /\bWARN\w*\b/.test(line) ? 'lvl-warn' : /\bINFO\b/.test(line) ? 'lvl-info' : '';
      span.textContent = line + '\n';
      pre.appendChild(span);
    }
    if (!shown.length) pre.textContent = 'No matching log lines.';
    byId('log-count').textContent = `${shown.length} of ${logs.length} recent lines. Updates every 10 seconds.`;
  }

  function formatBytes(raw) {
    if (typeof raw !== 'string' || !/^\d+$/.test(raw)) return '—';
    let value = Number(raw), unit = 0;
    const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'];
    while (value >= 1024 && unit < units.length - 1) { value /= 1024; unit++; }
    return `${value.toFixed(unit ? 1 : 0)} ${units[unit]}`;
  }

  function handshake(raw) {
    const instant = Date.parse(raw);
    if (!Number.isFinite(instant) || instant <= 0) return 'Not yet';
    const seconds = Math.max(0, Math.floor((Date.now() - instant) / 1000));
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hr ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
  }

  function renderPeers(peers, total) {
    const rows = byId('peer-rows');
    rows.replaceChildren();
    for (const peer of peers) {
      const row = document.createElement('tr');
      const latency = /^\d+(\.\d+)?s$/.test(peer.latency) ? parseFloat(peer.latency) * 1000 : 0;
      const columns = [
        [peer.name || 'Unnamed peer', peer.ip || 'IP not reported'],
        [peer.state || 'Unknown', peer.connection],
        [latency > 0 ? `${latency < 1 ? '<1' : Math.round(latency)} ms` : '—'],
        [handshake(peer.handshake)],
        [formatBytes(peer.received), formatBytes(peer.sent)]
      ];
      for (const [primary, secondary] of columns) {
        const cell = document.createElement('td');
        cell.textContent = primary;
        if (secondary) {
          const detail = document.createElement('small'); detail.textContent = secondary; cell.appendChild(detail);
        }
        row.appendChild(cell);
      }
      rows.appendChild(row);
    }
    byId('peer-count').textContent = total ? `(${peers.length < total ? peers.length + ' of ' : ''}${total})` : '(0)';
    byId('peer-empty').hidden = peers.length > 0;
    byId('peer-empty').textContent = 'No peers are visible to this NAS. Check group assignments and access policies in your NetBird dashboard.';
    byId('peer-scroll').hidden = peers.length === 0;
  }

  function renderBundle() {
    byId('bundle-message').textContent = bundle.state === 'running' ? 'Creating the bundle… This can take a few minutes.' : bundle.message || '';
    byId('support-result').hidden = !bundle.supportCode;
    if (byId('support-code').textContent !== (bundle.supportCode || '')) {
      byId('support-code').textContent = bundle.supportCode || '';
      delete byId('copy-support-code').dataset.copied;
      byId('copy-support-code').title = 'Copy support code';
      byId('support-copy-feedback').textContent = '';
    }
    byId('bundle-download').hidden = !bundle.download;
    syncControls();
  }

  async function refreshDetails() {
    if (busy || detailsRefreshing) return;
    detailsRefreshing = true;
    const current = generation;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 12000);
    try {
      const token = await sessionToken(controller.signal);
      const response = await fetch('details.cgi', {credentials: 'same-origin', cache: 'no-store',
        headers: {'X-SYNO-TOKEN': token}, signal: controller.signal});
      if (!response.ok) throw new Error('Details unavailable');
      const data = await response.json();
      if (current !== generation || busy) return;
      if (data.ok && data.collecting) {
        bundle = data.bundle;
        renderBundle();
        byId('details-message').textContent = 'Collecting a debug bundle. Live status updates will resume when collection finishes.';
        return;
      }
      if (data.ok && data.unavailable) {
        detailsAvailable = false;
        bundle = data.bundle || {};
        renderBundle();
        byId('details-message').textContent = 'The daemon is unavailable. Previously shown values may be out of date. Saved bundles can still be downloaded.';
        return;
      }
      if (!data.ok || !data.health || !Array.isArray(data.peers) || !Array.isArray(data.logs)) throw new Error('Invalid details');
      for (const name of ['management', 'signal']) {
        const source = data.health[name], element = byId('health-' + name);
        element.textContent = !source.reported ? 'Not reported' : source.connected ? 'Connected' : 'Disconnected';
        element.dataset.health = source.connected ? 'good' : 'bad';
      }
      const relays = data.health.relays;
      const reachable = relays.filter(relay => relay.available).length;
      byId('health-relays').textContent = relays.length ? `${reachable} / ${relays.length} available` : 'Not reported';
      byId('health-relays').dataset.health = reachable ? 'good' : 'bad';
      renderPeers(data.peers, data.peerTotal);
      logs = data.logs; filterLogs();
      debug = data.debug || {};
      bundle = data.bundle || {};
      detailsAvailable = true;
      byId('debug-state').textContent = debug.active ?
        `Debug logging is active. Restores the previous level at ${new Date(debug.expires * 1000).toLocaleTimeString()}.` :
        `Current level: ${data.logLevel}. Temporary debug logging restores the previous level after ten minutes or when stopped.`;
      renderBundle();
      byId('details-message').textContent = 'Updated ' + new Date().toLocaleTimeString();
    } catch (error) {
      if (current !== generation || busy) return;
      detailsAvailable = false;
      byId('details-message').textContent = 'Live details are unavailable. Previously shown values may be out of date. Check NetBird in Package Center.';
    } finally {
      clearTimeout(timer);
      detailsRefreshing = false;
      syncControls();
    }
  }

  byId('log-filter').addEventListener('change', filterLogs);
  byId('log-search').addEventListener('input', filterLogs);
  byId('debug-start').addEventListener('click', () => act({action: 'debug-start'}));
  byId('debug-stop').addEventListener('click', () => act({action: 'debug-stop'}));
  byId('bundle-create').addEventListener('click', () => {
    if (bundle.state === 'running') return;
    act({action: 'bundle-create', destination: document.querySelector('input[name="bundle-destination"]:checked').value});
  });
  byId('bundle-download').addEventListener('click', () => act({action: 'bundle-download', id: bundle.id}));
  for (const option of document.querySelectorAll('input[name="bundle-destination"]')) {
    option.addEventListener('change', () => {
      const upload = document.querySelector('input[name="bundle-destination"]:checked').value === 'support';
      byId('bundle-create').textContent = upload ? 'Create and upload bundle' : 'Create debug bundle';
      byId('bundle-destination-note').textContent = upload ?
        'The bundle will be uploaded to NetBird’s support service, including for self-hosted networks.' :
        'The bundle stays on this NAS for download. No support code is generated until a bundle is uploaded.';
    });
  }

  // Delegate so refreshed status cards keep their copy button working.
  document.addEventListener('click', async (event) => {
    const button = event.target.closest('#copy-ip, #copy-support-code');
    if (!button || button.disabled) return;
    const support = button.id === 'copy-support-code';
    const value = support ? byId('support-code').textContent.trim() : byId('netbird-ip').textContent.trim().split('/')[0];
    const octets = value.split('.');
    if (!value || (!support && (octets.length !== 4 || octets.some((part) => !/^\d{1,3}$/.test(part) || Number(part) > 255)))) return;
    button.disabled = true;
    const feedback = byId(support ? 'support-copy-feedback' : 'copy-ip-feedback');
    feedback.textContent = '';
    let copied = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(value);
        copied = true;
      }
    } catch (error) { /* Try the HTTP-compatible fallback. */ }
    let field;
    if (!copied) {
      field = document.createElement('input');
      field.type = 'text'; field.readOnly = true; field.value = value;
      field.setAttribute('aria-label', support ? 'Support code' : 'NetBird IP address');
      feedback.appendChild(field); field.select();
      try { copied = document.execCommand('copy'); } catch (error) { /* Offer manual copy. */ }
    }
    button.disabled = false;
    if (copied) {
      button.dataset.copied = 'true'; button.title = 'Copied!';
      feedback.textContent = support ? 'Support code copied.' : 'IP address copied.'; button.focus();
    } else {
      feedback.insertBefore(document.createTextNode(support ? 'Copy this code:' : 'Copy this address:'), field);
      field.focus(); field.select();
    }
  });

  syncServerSelection();
  syncControls();
  filterLogs();
  refreshDetails();
  setInterval(refreshStatus, 10000);
})();
