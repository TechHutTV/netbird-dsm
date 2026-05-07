#!/bin/sh
# NetBird DSM AppPortal — read-only connection status page.
# Served at /webman/3rdparty/netbird/index.cgi behind DSM auth.

PKGVAR="/var/packages/netbird/var"
PKGDEST="/var/packages/netbird/target"
NETBIRD="${PKGDEST}/bin/netbird.bin"
CONFIG_JSON="${PKGVAR}/config.json"
LOG_FILE="${PKGVAR}/netbird.log"
DOCS_URL="https://docs.netbird.io/get-started/install/synology"
DEFAULT_DASHBOARD_URL="https://app.netbird.io"

export NB_DAEMON_ADDR="unix://${PKGVAR}/netbird.sock"
export HOME="${PKGVAR}"

html_escape() {
    printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' -e 's/"/\&quot;/g'
}

NAS_HOSTNAME=$(hostname 2>/dev/null || uname -n 2>/dev/null)
[ -z "${NAS_HOSTNAME}" ] && NAS_HOSTNAME="this device"
NAS_HOSTNAME=$(html_escape "${NAS_HOSTNAME}")

# Inline SVG icons (Lucide subset).
ICON_GLOBE='<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
ICON_PIN='<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>'
ICON_PEERS='<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
ICON_RELAY='<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.9 16.1C1 12.2 1 5.8 4.9 1.9"/><path d="M7.8 4.7a6.14 6.14 0 0 0-.8 7.5"/><circle cx="12" cy="9" r="2"/><path d="M16.2 4.8c2 2 2.26 5.11.8 7.47"/><path d="M19.1 1.9a9.96 9.96 0 0 1 0 14.1"/><path d="M9.5 18h5"/><path d="m8 22 4-11 4 11"/></svg>'
ICON_EXIT='<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'
ICON_NB='<svg class="icon" viewBox="0 0 31 23" aria-hidden="true"><path d="M21.46 0.52c-3.65 0.33-5.46 2.43-6.15 3.49L4.66 22.47h12.86L30.19 0.52H21.46z" fill="currentColor"/><path d="M17.53 22.47L0 3.89s19.82-5.33 21.75 11.28l-4.22 7.3z" fill="currentColor"/><path d="M14.92 4.71L9.55 14.02l7.97 8.45 4.22-7.32C21.07 9.45 18.29 6.33 14.92 4.7" fill="currentColor" opacity="0.7"/></svg>'
ICON_PROFILE='<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
ICON_LOG='<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/></svg>'
ICON_CHEV='<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>'
ICON_EXTERNAL='<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'

# Pull the per-instance dashboard URL from the daemon's config so self-hosted
# users link to their own panel. Falls back to NetBird Cloud when unset.
DASHBOARD_URL=$(sed -n 's/.*"AdminURL"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "${CONFIG_JSON}" 2>/dev/null | head -1)
[ -z "${DASHBOARD_URL}" ] && DASHBOARD_URL="${DEFAULT_DASHBOARD_URL}"
DASHBOARD_URL=$(html_escape "${DASHBOARD_URL}")

STATUS_RAW=$("${NETBIRD}" status 2>/dev/null)

CARD_ROWS=""
HINT=""
META=""
SHOW_DASHBOARD=0

if echo "${STATUS_RAW}" | grep -q "Daemon status: NeedsLogin"; then
    STATUS_LABEL="Not Configured"
    DOT_CLASS="bg-yellow"
    STATE_CLASS="state-needslogin"
    HINT='Run <code>sudo netbird up --setup-key &hellip;</code> via SSH to enroll this device.'
elif echo "${STATUS_RAW}" | grep -q "^Management: Connected"; then
    STATUS_LABEL="Connected"
    DOT_CLASS="bg-green"
    STATE_CLASS="state-connected"
    SHOW_DASHBOARD=1

    NB_FQDN=$(html_escape "$(echo "${STATUS_RAW}" | sed -n 's/^FQDN: //p')")
    NB_IP=$(html_escape "$(echo "${STATUS_RAW}" | sed -n 's/^NetBird IP: //p')")
    PEERS=$(html_escape "$(echo "${STATUS_RAW}" | sed -n 's/^Peers count: //p')")
    RELAYS=$(html_escape "$(echo "${STATUS_RAW}" | sed -n 's/^Relays: //p')")
    DAEMON_VER=$(html_escape "$(echo "${STATUS_RAW}" | sed -n 's/^Daemon version: //p')")
    PROFILE=$(html_escape "$(echo "${STATUS_RAW}" | sed -n 's/^Profile: //p')")
    META="${NB_FQDN}"

    # Best-effort exit-node detection: a network with destination 0.0.0.0/0.
    # Output format may vary; we look for any nearby peer hostname. Defaults to None.
    NET_LIST=$("${NETBIRD}" networks list 2>/dev/null)
    EXIT_NODE=$(echo "${NET_LIST}" | awk '
        /0\.0\.0\.0\/0/ { in_block = 1 }
        in_block && /[Pp]eer[s]?:/ {
            sub(/.*: */, "")
            sub(/^[[:space:]]*-?[[:space:]]*/, "")
            print
            exit
        }
        in_block && /^[[:space:]]*$/ { in_block = 0 }
    ' | head -1)
    [ -z "${EXIT_NODE}" ] && EXIT_NODE="None"
    EXIT_NODE=$(html_escape "${EXIT_NODE}")

    CARD_ROWS=$(cat <<ROWS
        <li>
          <span class="label">${ICON_GLOBE}Domain Name</span>
          <span class="value">${NB_FQDN}</span>
        </li>
        <li>
          <span class="label">${ICON_PIN}NetBird IP</span>
          <span class="value">${NB_IP}</span>
        </li>
        <li>
          <span class="label">${ICON_PEERS}Peers Connected</span>
          <span class="value">${PEERS}</span>
        </li>
        <li>
          <span class="label">${ICON_RELAY}Relays</span>
          <span class="value">${RELAYS}</span>
        </li>
        <li>
          <span class="label">${ICON_EXIT}Exit Node</span>
          <span class="value">${EXIT_NODE}</span>
        </li>
        <li>
          <span class="label">${ICON_NB}Agent Version</span>
          <span class="value">${DAEMON_VER}</span>
        </li>
        <li>
          <span class="label">${ICON_PROFILE}Profile</span>
          <span class="value">${PROFILE}</span>
        </li>
ROWS
)
else
    STATUS_LABEL="Disconnected"
    DOT_CLASS="bg-red"
    STATE_CLASS="state-disconnected"
    HINT="Daemon not reachable or no active connection."
fi

# Recent log lines (HTML-escaped, then INFO/WARN/ERROR colorized).
LOG_HTML=""
if [ -r "${LOG_FILE}" ]; then
    LOG_HTML=$(tail -n 25 "${LOG_FILE}" 2>/dev/null \
        | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' \
        | sed -E \
              -e 's/(WARN[A-Z]*)/<span class="lvl-warn">\1<\/span>/' \
              -e 's/(ERRO[RA-Z]*)/<span class="lvl-error">\1<\/span>/' \
              -e 's/(INFO)/<span class="lvl-info">\1<\/span>/')
fi
[ -z "${LOG_HTML}" ] && LOG_HTML="(log file is empty or unreadable)"

echo "Content-Type: text/html; charset=utf-8"
echo ""

cat <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="10">
  <title>NetBird Client - ${NAS_HOSTNAME}</title>
  <link rel="icon" type="image/svg+xml" href='data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 31 23"><path d="M21.46 0.52c-3.65 0.33-5.46 2.43-6.15 3.49L4.66 22.47h12.86L30.19 0.52H21.46z" fill="%23F68330"/><path d="M17.53 22.47L0 3.89s19.82-5.33 21.75 11.28l-4.22 7.3z" fill="%23F68330"/><path d="M14.92 4.71L9.55 14.02l7.97 8.45 4.22-7.32C21.07 9.45 18.29 6.33 14.92 4.7" fill="%23F05252"/></svg>'>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    :root {
      --bg: #181a1d;
      --card: #1c1e21;
      --border: #2e3238;
      --border-strong: #363b40;
      --row-border: #25282d;
      --text: #f3f4f6;
      --text-dim: #9CA3AF;
      --text-soft: #b7c0c6;
      --netbird: #f68330;
      --green: #31C48D;
      --yellow: #E3A008;
      --red: #F05252;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      min-height: 100vh;
      padding: 2.5rem 1.5rem 4rem;
      -webkit-font-smoothing: antialiased;
      letter-spacing: 0.01em;
    }
    main { max-width: 560px; margin: 0 auto; }
    .brand {
      display: flex; align-items: center; gap: 0.625rem;
      margin-bottom: 1.75rem;
      color: var(--text-dim); font-size: 0.8125rem;
      text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500;
    }
    .brand svg { height: 18px; width: auto; }
    .header {
      display: flex; align-items: center; gap: 0.75rem;
      font-size: 0.95rem; font-weight: 500; color: var(--text-dim);
    }
    .header .state-connected    { color: var(--green); }
    .header .state-needslogin   { color: var(--yellow); }
    .header .state-disconnected { color: var(--red); }
    .header .sep { color: var(--border-strong); }
    .header .meta { color: var(--text-soft); }
    .dot {
      width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0;
      animation: pulse 2.4s ease-in-out infinite;
    }
    .dot.bg-green  { background: var(--green);  box-shadow: 0 0 0 4px rgba(49, 196, 141, 0.18); }
    .dot.bg-yellow { background: var(--yellow); box-shadow: 0 0 0 4px rgba(227, 160, 8, 0.18); }
    .dot.bg-red    { background: var(--red);    box-shadow: 0 0 0 4px rgba(240, 82, 82, 0.18); }
    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50%      { transform: scale(1.08); }
    }
    .hint {
      margin: 1rem 0 0 1.875rem;
      color: var(--text-dim); font-size: 0.875rem; line-height: 1.55; max-width: 480px;
    }
    code {
      background: var(--row-border); color: var(--netbird);
      padding: 0.125rem 0.4rem; border-radius: 4px;
      font-size: 0.8125rem; font-family: ui-monospace, 'SFMono-Regular', Consolas, monospace;
    }
    .card {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 8px; overflow: hidden; margin-top: 1.5rem;
    }
    .list { list-style: none; margin: 0; padding: 0; }
    .list li {
      display: flex; align-items: center; justify-content: space-between;
      gap: 1rem; padding: 0.875rem 1rem;
      border-bottom: 1px solid var(--row-border);
      font-size: 0.84rem; min-height: 48px;
    }
    .list li:last-child { border-bottom: none; }
    .label {
      display: inline-flex; align-items: center; gap: 0.625rem;
      color: var(--text-soft); line-height: 1;
    }
    .icon {
      width: 16px; height: 16px; flex-shrink: 0;
      color: var(--text-dim); display: block;
    }
    .value {
      color: var(--text-dim); font-family: ui-monospace, 'SFMono-Regular', Consolas, monospace;
      font-size: 0.84rem; text-align: right;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    details.log {
      margin-top: 1rem; background: var(--card);
      border: 1px solid var(--border); border-radius: 8px; overflow: hidden;
    }
    details.log > summary {
      list-style: none; cursor: pointer; padding: 0.875rem 1rem;
      display: flex; align-items: center; justify-content: space-between;
      font-size: 0.84rem; color: var(--text-soft); user-select: none;
    }
    details.log > summary::-webkit-details-marker { display: none; }
    details.log > summary .left { display: inline-flex; align-items: center; gap: 0.625rem; }
    details.log > summary .chev {
      width: 16px; height: 16px; color: var(--text-dim); transition: transform 0.15s;
    }
    details.log[open] > summary .chev { transform: rotate(180deg); }
    details.log[open] > summary { border-bottom: 1px solid var(--row-border); }
    details.log pre {
      margin: 0; padding: 0.75rem 1rem 1rem;
      max-height: 280px; overflow: auto;
      font-family: ui-monospace, 'SFMono-Regular', Consolas, monospace;
      font-size: 0.75rem; line-height: 1.6; color: var(--text-dim);
      background: #16181b; white-space: pre;
    }
    details.log pre .lvl-info  { color: #76A9FA; }
    details.log pre .lvl-warn  { color: #E3A008; }
    details.log pre .lvl-error { color: #F05252; }
    .actions {
      display: flex; gap: 0.625rem; margin-top: 1rem; justify-content: flex-end;
    }
    .btn {
      display: inline-flex; align-items: center; gap: 0.5rem;
      padding: 0.5rem 0.875rem; border-radius: 6px;
      font-size: 0.84rem; font-weight: 500; text-decoration: none;
      transition: background 0.15s, color 0.15s, border-color 0.15s; cursor: pointer;
      border: 1px solid var(--border-strong);
      color: var(--text-soft); background: var(--card);
    }
    .btn:hover { background: #25282d; color: var(--text); }
    .btn .icon { width: 14px; height: 14px; color: currentColor; }
    .btn-primary { background: var(--netbird); border-color: var(--netbird); color: #fff; }
    .btn-primary:hover { background: #f46d1b; border-color: #f46d1b; color: #fff; }
  </style>
</head>
<body>
  <main>
    <div class="brand">
      <svg viewBox="0 0 31 23" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <path d="M21.4631 0.523438C17.8173 0.857913 16.0028 2.95675 15.3171 4.01871L4.66406 22.4734H17.5163L30.1929 0.523438H21.4631Z" fill="#F68330"/>
        <path d="M17.5265 22.4737L0 3.88525C0 3.88525 19.8177 -1.44128 21.7493 15.1738L17.5265 22.4737Z" fill="#F68330"/>
        <path d="M14.9236 4.70563L9.54688 14.0208L17.5158 22.4747L21.7385 15.158C21.0696 9.44682 18.2851 6.32784 14.9236 4.69727" fill="#F05252"/>
      </svg>
      NetBird
    </div>
    <div class="header">
      <span class="dot ${DOT_CLASS}"></span>
      <span class="${STATE_CLASS}">${STATUS_LABEL}</span>
$([ -n "${META}" ] && printf '      <span class="sep">·</span><span class="meta">%s</span>\n' "${META}")
    </div>
$([ -n "${HINT}" ] && printf '    <p class="hint">%s</p>\n' "${HINT}")
$([ -n "${CARD_ROWS}" ] && printf '    <div class="card">\n      <ul class="list">\n%s\n      </ul>\n    </div>\n' "${CARD_ROWS}")
    <details class="log">
      <summary>
        <span class="left">${ICON_LOG}Recent Activity</span>
        ${ICON_CHEV}
      </summary>
      <pre>${LOG_HTML}</pre>
    </details>
    <div class="actions">
      <a class="btn" href="${DOCS_URL}" target="_blank" rel="noopener">${ICON_EXTERNAL}Open Docs</a>
$([ "${SHOW_DASHBOARD}" = "1" ] && printf '      <a class="btn btn-primary" href="%s" target="_blank" rel="noopener">%sOpen Dashboard</a>\n' "${DASHBOARD_URL}" "${ICON_EXTERNAL}")
    </div>
  </main>
</body>
</html>
EOF
