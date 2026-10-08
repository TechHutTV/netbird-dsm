#!/bin/sh
# NetBird DSM AppPortal — connection status and administrator controls.
# Served at /webman/3rdparty/netbird/index.cgi behind DSM auth.

# AppPortal launcher privileges do not protect direct CGI requests. Authenticate
# using DSM's request environment before reading config, status, or logs.
if ! DSM_USER=$(/usr/syno/synoman/webman/modules/authenticate.cgi 2>/dev/null) || [ -z "${DSM_USER}" ]; then
    printf 'Status: 401 Unauthorized\r\nContent-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nReferrer-Policy: no-referrer\r\n\r\n'
    cat <<'HTML'
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>NetBird — DSM sign-in required</title></head>
<body>
<p>Sign in to <a href="/webman/index.cgi">DSM</a> with an administrator account, then reopen NetBird.</p>
<script>
// DSM may open the launcher without a SynoToken. Obtain it through the existing
// same-origin DSM session; the CGI still validates that session on every request.
fetch('/webman/login.cgi', { credentials: 'same-origin', cache: 'no-store' })
    .then(function (response) {
        if (!response.ok) throw new Error('DSM session unavailable');
        return response.json();
    })
    .then(function (session) {
        if (typeof session.SynoToken !== 'string' || !session.SynoToken) return;
        var current = new URLSearchParams(window.location.search).get('SynoToken');
        if (current === session.SynoToken) return; // Do not loop on a rejected session.
        window.location.replace('/webman/3rdparty/netbird/index.cgi?SynoToken=' + encodeURIComponent(session.SynoToken));
    })
    .catch(function () {}); // Keep the DSM sign-in link available on failure.
</script>
</body>
</html>
HTML
    exit 0
fi

# Resolve groups for the authenticated identity, never the CGI process user.
DSM_GROUPS=$(/usr/bin/id -nG -- "${DSM_USER}" 2>/dev/null) || DSM_GROUPS=""
case " ${DSM_GROUPS} " in
    *" administrators "*) ;;
    *)
        printf 'Status: 403 Forbidden\r\nContent-Type: text/plain; charset=utf-8\r\nCache-Control: no-store\r\nReferrer-Policy: no-referrer\r\n\r\nDSM administrator access is required.\n'
        exit 0
        ;;
esac

PKGVAR="/var/packages/netbird/var"
PKGDEST="/var/packages/netbird/target"
NETBIRD="${PKGDEST}/bin/netbird.bin"
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

ICON_COPY='<svg class="icon icon-copy" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'
ICON_CHECK='<svg class="icon icon-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>'

# Keep CLI failure distinct from a disconnected or unconfigured daemon. Require
# exactly one JSON object with an explicit state before rendering any fields.
DAEMON_STATE=""
STATUS_ERROR=""
read_status() {
    # Debug-bundle collection can briefly hold the daemon's status lock. Keep
    # an initial page load bounded while the separate job endpoint reports progress.
    if command -v timeout >/dev/null 2>&1; then
        timeout 5 "${NETBIRD}" status --json
    else
        "${NETBIRD}" status --json
    fi
}
if ! command -v jq >/dev/null 2>&1; then
    STATUS_ERROR="The status page requires jq to read NetBird status."
elif ! STATUS_JSON=$(read_status 2>/dev/null); then
    STATUS_ERROR="Unable to read NetBird status. The daemon may not be running."
elif ! DAEMON_STATE=$(printf '%s' "${STATUS_JSON}" | jq -ers '
    if length == 1 and (.[0] | type) == "object" then
        .[0].daemonStatus | select(type == "string" and length > 0)
    else error("invalid status response") end
' 2>/dev/null); then
    STATUS_ERROR="NetBird returned invalid status information."
fi

# Filters are fixed by this script. Values are escaped as HTML, never evaluated
# as shell code; missing or incorrectly typed fields are displayed as unknown.
json_field() {
    value=$(printf '%s' "${STATUS_JSON}" | jq -r "$1" 2>/dev/null) || value=""
    [ -n "${value}" ] || value="—"
    html_escape "${value}"
}

CARD_ROWS=""
HINT=""
META=""
SHOW_DASHBOARD=0

STATUS_LABEL="Status unavailable"
DOT_CLASS="bg-red"
STATE_CLASS="state-disconnected"
if [ -n "${STATUS_ERROR}" ]; then
    HINT="${STATUS_ERROR}"
else
    case "${DAEMON_STATE}" in
        NeedsLogin)
            STATUS_LABEL="Not Configured"
            DOT_CLASS="bg-yellow"
            STATE_CLASS="state-needslogin"
            HINT='Enroll this NAS with a setup key from your NetBird dashboard.'
            ;;
        LoginFailed|SessionExpired)
            STATUS_LABEL="Login Required"
            DOT_CLASS="bg-yellow"
            STATE_CLASS="state-needslogin"
            HINT='Use a setup key to sign in again, or use the CLI for interactive login.'
            ;;
        Connecting)
            STATUS_LABEL="Connecting"
            DOT_CLASS="bg-yellow"
            STATE_CLASS="state-needslogin"
            HINT="NetBird is connecting."
            ;;
        Connected)
            STATUS_LABEL="Connected"
            DOT_CLASS="bg-green"
            STATE_CLASS="state-connected"
            SHOW_DASHBOARD=1
            ;;
        Idle)
            STATUS_LABEL="Disconnected"
            HINT="NetBird is not connected."
            ;;
        *) HINT="Unrecognized NetBird state: $(html_escape "${DAEMON_STATE}")" ;;
    esac
fi

if [ "${SHOW_DASHBOARD}" = 1 ]; then
    # Use the connected profile's management origin, since enrollment may leave
    # AdminURL at its Cloud default. Assume the self-hosted dashboard shares it.
    DASHBOARD_URL=$(printf '%s' "${STATUS_JSON}" | jq -er --arg cloud "${DEFAULT_DASHBOARD_URL}" '
        .management.url | select(type == "string") |
        capture("^(?<scheme>https?)://(?<host>[^/?#@\\\\[:space:][:cntrl:]]+)([/?#]|$)"; "i") |
        if (.host | test("^api\\.(netbird\\.io|wiretrustee\\.com)(:[0-9]+)?$"; "i"))
        then $cloud else .scheme + "://" + .host end
    ' 2>/dev/null) || DASHBOARD_URL=""
    [ -n "${DASHBOARD_URL}" ] || DASHBOARD_URL="${DEFAULT_DASHBOARD_URL}"
    DASHBOARD_URL=$(html_escape "${DASHBOARD_URL}")

    NB_FQDN=$(json_field '.fqdn | select(type == "string")')
    NB_IP=$(json_field '.netbirdIp | select(type == "string")')
    PEERS=$(json_field '.peers | [.connected, .total] | map(if type == "number" and . >= 0 and . == floor then tostring else "—" end) | join(" / ")')
    # A NAS can have direct and relayed peers at the same time. Relay availability
    # alone does not indicate whether any peer traffic is using a relay.
    CONNECTION_TYPES=$(json_field '
        .peers |
        if .connected == 0 then "No connected peers"
        elif (.details | type) != "array" then "Not reported"
        else
            [.details[] | select(type == "object") | select(.status == "Connected")] as $connected |
            if ($connected | length) != .connected then "Not reported"
            else
                ($connected | map(select(.connectionType == "P2P")) | length) as $p2p |
                ($connected | map(select(.connectionType == "Relayed")) | length) as $relayed |
                (($connected | length) - $p2p - $relayed) as $unknown |
                "\($p2p) P2P · \($relayed) relayed" +
                (if $unknown > 0 then " · \($unknown) unknown" else "" end)
            end
        end
    ')
    RELAYS=$(json_field '.relays | [.available, .total] | map(if type == "number" and . >= 0 and . == floor then tostring else "—" end) | join(" / ")')
    DAEMON_VER=$(json_field '.daemonVersion | select(type == "string")')
    PROFILE=$(json_field '.profileName | select(type == "string")')
    META="${NB_FQDN}"

    # Status JSON lists routes but does not identify the selected exit node.
    EXIT_NODE="Not reported"

    CARD_ROWS=$(cat <<ROWS
        <li>
          <span class="label">${ICON_GLOBE}Domain Name</span>
          <span class="value">${NB_FQDN}</span>
        </li>
        <li>
          <span class="label">${ICON_PIN}NetBird IP</span>
          <span class="ip-value">
            <span id="netbird-ip" class="value">${NB_IP}</span>
            <button id="copy-ip" class="btn btn-copy" type="button" aria-label="Copy IP address" title="Copy IP address" disabled>${ICON_COPY}${ICON_CHECK}</button>
          </span>
        </li>
        <li>
          <span class="label">${ICON_PEERS}Peers Connected</span>
          <span class="value">${PEERS}</span>
        </li>
        <li>
          <span class="label" title="Connection type is determined separately for each connected peer.">${ICON_PEERS}Connection Types</span>
          <span class="value">${CONNECTION_TYPES}</span>
        </li>
        <li>
          <span class="label">${ICON_RELAY}Relays Available</span>
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
fi

CONTROL_STATE="Unavailable"
case "${DAEMON_STATE}" in
    NeedsLogin|LoginFailed|SessionExpired|Connecting|Connected|Idle)
        [ -z "${STATUS_ERROR}" ] && CONTROL_STATE="${DAEMON_STATE}" ;;
esac

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
echo "Cache-Control: no-store"
echo "Referrer-Policy: no-referrer"
echo "X-Content-Type-Options: nosniff"
echo "X-Frame-Options: SAMEORIGIN"
echo "Content-Security-Policy: frame-ancestors 'self'; base-uri 'none'; form-action 'self'"
echo ""

cat <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
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
    main { max-width: 760px; margin: 0 auto; }
    .brand {
      display: flex; align-items: center; gap: 0.625rem;
      margin-bottom: 1.75rem;
      color: var(--text-dim); font-size: 0.8125rem;
      text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500;
    }
    .brand svg { height: 18px; width: auto; }
    .header {
      display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem;
      font-size: 0.95rem; font-weight: 500; color: var(--text-dim);
    }
    .header .state-connected    { color: var(--green); }
    .header .state-needslogin   { color: var(--yellow); }
    .header .state-disconnected { color: var(--red); }
    .header .sep { color: var(--border-strong); }
    .header .meta { color: var(--text-soft); overflow-wrap: anywhere; min-width: 0; }
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
    .ip-value {
      display: flex; align-items: center; justify-content: flex-end;
      flex-wrap: wrap; gap: 0.5rem; min-width: 0;
    }
    .copy-feedback { margin: 0.75rem 0 0; font-size: 0.8125rem; color: var(--text-soft); }
    .copy-feedback:empty { display: none; }
    .copy-feedback input {
      width: 11rem; margin-left: 0.5rem; padding: 0.25rem;
      color: var(--text); background: var(--card); border: 1px solid var(--border-strong);
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
    .btn:focus-visible { outline: 2px solid var(--netbird); outline-offset: 2px; }
    .btn:disabled { opacity: 0.5; cursor: default; }
    .btn-copy { padding: 0.375rem; flex-shrink: 0; border-color: transparent; background: transparent; }
    .btn .icon { width: 14px; height: 14px; color: currentColor; }
    .btn-copy .icon-check, .btn-copy[data-copied="true"] .icon-copy { display: none; }
    .btn-copy[data-copied="true"] .icon-check { display: block; color: var(--green); }
    .btn-primary { background: var(--netbird); border-color: var(--netbird); color: #fff; }
    .btn-primary:hover { background: #f46d1b; border-color: #f46d1b; color: #fff; }
    [hidden] { display: none !important; }
    .controls { margin-top: 1.25rem; }
    .control-actions { display: flex; gap: 0.625rem; }
    .enrollment { padding: 1.25rem; margin-top: 0; }
    .enrollment h2 { margin: 0 0 0.5rem; font-size: 1rem; font-weight: 600; }
    .enrollment p, .control-message, .control-note {
      font-size: 0.8125rem; line-height: 1.55; color: var(--text-soft);
    }
    .enrollment p { margin: 0 0 1.25rem; }
    .enrollment fieldset { border: 0; padding: 0; margin: 0; min-width: 0; }
    .enrollment label { display: block; margin: 1rem 0 0.4rem; font-size: 0.8125rem; }
    .enrollment input:not([type="radio"]) {
      width: 100%; padding: 0.625rem 0.75rem; border-radius: 6px;
      border: 1px solid var(--border-strong); background: var(--bg);
      color: var(--text); font: inherit; font-size: 0.875rem;
    }
    .enrollment input:not([type="radio"]):focus { outline: 2px solid var(--netbird); outline-offset: 2px; }
    .server-choice legend { padding: 0; margin-bottom: 0.4rem; font-size: 0.8125rem; }
    .server-options { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
    .server-options label { position: relative; margin: 0; cursor: pointer; }
    .server-options input {
      position: absolute; opacity: 0; width: 1px; height: 1px; margin: 0;
    }
    .server-options span {
      display: block; padding: 0.75rem 0.5rem; border-radius: 6px; text-align: center;
      border: 1px solid var(--border-strong); color: var(--text-soft); background: var(--bg);
    }
    .server-options input:checked + span {
      border-color: var(--netbird); color: var(--netbird); background: #30241c;
    }
    .server-options input:focus-visible + span { outline: 2px solid var(--netbird); outline-offset: 2px; }
    .server-options input:disabled + span { opacity: 0.5; cursor: default; }
    .enrollment .btn { margin-top: 1.25rem; }
    .control-message { margin: 0.75rem 0 0; }
    .control-message:empty { display: none; }
    .control-message[data-error="true"] { color: var(--red); }
    .control-note { color: var(--text-dim); margin: 0.625rem 0 0; }
    .enrollment small { display: block; color: var(--text-dim); font-size: 0.75rem; margin-top: 0.4rem; line-height: 1.5; }
    .notice { padding: 0.875rem 1rem; border: 1px solid var(--yellow); border-radius: 8px; color: var(--yellow); font-size: 0.8125rem; line-height: 1.5; margin-bottom: 1.25rem; }
    .health { margin-top: 1.25rem; padding: 1rem; }
    .health h2 { margin: 0 0 0.875rem; font-size: 0.875rem; font-weight: 600; }
    .health-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
    .health-grid span { display: block; font-size: 0.75rem; color: var(--text-dim); margin-bottom: 0.35rem; }
    .health-grid strong { font-size: 0.8125rem; font-weight: 500; }
    [data-health="good"] { color: var(--green); }
    [data-health="bad"] { color: var(--yellow); }
    .detail-note { font-size: 0.75rem; color: var(--text-dim); line-height: 1.5; margin: 0.75rem 0 0; }
    .peer-scroll { overflow-x: auto; padding: 0 1rem 1rem; }
    .peer-table { width: 100%; min-width: 650px; border-collapse: collapse; font-size: 0.75rem; }
    .peer-table th, .peer-table td { text-align: left; padding: 0.65rem 0.6rem; border-bottom: 1px solid var(--row-border); vertical-align: top; }
    .peer-table th { color: var(--text-soft); font-weight: 500; }
    .peer-table td { overflow-wrap: anywhere; max-width: 190px; }
    .peer-table small { display: block; color: var(--text-dim); margin-top: 0.3rem; }
    .peer-empty { padding: 0 1rem 1rem; margin: 0; color: var(--text-dim); font-size: 0.8125rem; }
    .troubleshooting { padding: 0 1rem 1rem; }
    .troubleshooting h3 { margin: 1.25rem 0 0.625rem; font-size: 0.875rem; font-weight: 500; }
    .troubleshooting fieldset { margin: 0; padding: 0; border: 0; min-width: 0; }
    .tool-row { display: flex; flex-wrap: wrap; gap: 0.625rem; align-items: center; }
    .log-tools { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; }
    .log-tools select, .log-tools input { min-width: 0; padding: 0.5rem; color: var(--text); background: var(--bg); border: 1px solid var(--border-strong); border-radius: 6px; font: inherit; font-size: 0.75rem; }
    .log-tools input { flex: 1; width: 40%; }
    .troubleshooting pre { margin: 0; border: 1px solid var(--border); border-radius: 6px; }
    .bundle-destination { display: block; font-size: 0.8125rem; margin: 0.75rem 0; }
    .bundle-destination input { accent-color: var(--netbird); margin-right: 0.4rem; }
    .support-result { margin-top: 0.875rem; padding: 0.875rem; border: 1px solid var(--border-strong); border-radius: 6px; }
    .support-result label { display: block; font-size: 0.75rem; color: var(--text-dim); margin-bottom: 0.5rem; }
    .support-code { font-family: ui-monospace, monospace; font-size: 0.75rem; overflow-wrap: anywhere; user-select: all; }
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
    <div id="status-content" data-state="${CONTROL_STATE}">
    <div class="header">
      <span class="dot ${DOT_CLASS}"></span>
      <span class="${STATE_CLASS}">${STATUS_LABEL}</span>
$([ -n "${META}" ] && printf '      <span class="sep">·</span><span class="meta">%s</span>\n' "${META}")
    </div>
$([ -n "${HINT}" ] && printf '    <p class="hint">%s</p>\n' "${HINT}")
$([ -n "${CARD_ROWS}" ] && printf '    <div class="card">\n      <ul class="list">\n%s\n      </ul>\n    </div>\n' "${CARD_ROWS}")
    <p id="copy-ip-feedback" class="copy-feedback" role="status"></p>
    </div>
    <section class="controls" aria-label="Connection controls">
      <p id="controls-unavailable" class="notice" role="status" hidden></p>
      <div class="control-actions">
        <button id="connect" class="btn btn-primary" type="button" hidden disabled>Connect</button>
        <button id="disconnect" class="btn" type="button" hidden disabled>Disconnect</button>
      </div>
      <p id="disconnect-note" class="control-note" hidden>Disconnecting keeps your enrollment and leaves the service running.</p>
      <form id="enroll-form" class="card enrollment" autocomplete="off" hidden>
        <h2>Connect this NAS</h2>
        <p>Use a setup key from your NetBird dashboard to join your network.</p>
        <fieldset id="enroll-fields" disabled>
          <fieldset class="server-choice">
            <legend>Management server</legend>
            <div class="server-options">
              <label><input id="server-cloud" type="radio" name="server-kind" value="cloud" checked><span>NetBird Cloud</span></label>
              <label><input id="server-self-hosted" type="radio" name="server-kind" value="self-hosted"><span>Self-hosted</span></label>
            </div>
          </fieldset>
          <div id="management-field" hidden>
            <label for="management-url">Management URL</label>
            <input id="management-url" type="url" placeholder="https://netbird.example.com" maxlength="2048" spellcheck="false" autocomplete="off" disabled>
          </div>
          <label for="setup-key">Setup key</label>
          <input id="setup-key" type="password" required minlength="16" maxlength="256" autocomplete="off" spellcheck="false" autocapitalize="none" aria-describedby="setup-key-hint">
          <small id="setup-key-hint">The key is sent only for enrollment and is not saved by this page.</small>
          <button id="enroll" class="btn btn-primary" type="submit">Enroll and connect</button>
        </fieldset>
      </form>
      <p id="control-message" class="control-message" role="status" aria-live="polite"></p>
      <noscript><p class="control-note">Enable JavaScript to use connection controls and refresh status, or use the NetBird CLI.</p></noscript>
    </section>
    <section class="card health" aria-labelledby="health-title">
      <h2 id="health-title">Connection health</h2>
      <div class="health-grid">
        <div><span>Management</span><strong id="health-management">Checking…</strong></div>
        <div><span>Signal</span><strong id="health-signal">Checking…</strong></div>
        <div><span>Relays</span><strong id="health-relays">Checking…</strong></div>
      </div>
      <p id="details-message" class="detail-note" role="status">Loading connection details…</p>
    </section>
    <details id="peers" class="log">
      <summary><span class="left">${ICON_PEERS}Peers <span id="peer-count"></span></span>${ICON_CHEV}</summary>
      <p id="peer-empty" class="peer-empty">Loading peer details…</p>
      <div id="peer-scroll" class="peer-scroll" hidden>
        <table class="peer-table">
          <thead><tr><th scope="col">Peer / IP</th><th scope="col">Connection</th><th scope="col">Latency</th><th scope="col">Last handshake</th><th scope="col">Received / sent</th></tr></thead>
          <tbody id="peer-rows"></tbody>
        </table>
      </div>
    </details>
    <details id="activity" class="log">
      <summary>
        <span class="left">${ICON_LOG}Troubleshooting</span>
        ${ICON_CHEV}
      </summary>
      <div class="troubleshooting">
        <h3>Recent logs</h3>
        <div class="log-tools">
          <select id="log-filter" aria-label="Filter logs by severity"><option value="all">All levels</option><option value="warnings">Warnings and errors</option><option value="errors">Errors only</option></select>
          <input id="log-search" type="search" aria-label="Search recent logs" placeholder="Search logs" maxlength="100">
        </div>
        <pre id="recent-logs">${LOG_HTML}</pre>
        <p id="log-count" class="detail-note">Recent daemon output. Filtered locally in your browser.</p>
        <h3>Temporary debug logging</h3>
        <p id="debug-state" class="detail-note">Checking log level…</p>
        <fieldset id="diagnostics-fields" disabled>
          <div class="tool-row">
            <button id="debug-start" class="btn" type="button">Enable debug for 10 minutes</button>
            <button id="debug-stop" class="btn" type="button" hidden>Stop debug logging</button>
          </div>
          <h3>Debug bundle</h3>
          <p class="detail-note">Includes logs, connection status, and system information with NetBird’s strict anonymization enabled. Review downloaded bundles before sharing them.</p>
          <label class="bundle-destination"><input type="radio" name="bundle-destination" value="support" checked>Upload to NetBird support and get a support code</label>
          <label class="bundle-destination"><input type="radio" name="bundle-destination" value="local">Download only</label>
          <p id="bundle-destination-note" class="detail-note">The bundle will be uploaded to NetBird’s support service, including for self-hosted networks.</p>
          <button id="bundle-create" class="btn" type="button">Create and upload bundle</button>
        </fieldset>
        <p id="diagnostic-message" class="control-message" role="status"></p>
        <p id="bundle-message" class="detail-note" role="status"></p>
        <div id="support-result" class="support-result" hidden>
          <label for="support-code">Support code — send this with your report</label>
          <output id="support-code" class="support-code"></output>
          <button id="copy-support-code" class="btn btn-copy" type="button" aria-label="Copy support code" title="Copy support code">${ICON_COPY}${ICON_CHECK}</button>
          <p id="support-copy-feedback" class="detail-note" role="status"></p>
        </div>
        <button id="bundle-download" class="btn" type="button" hidden disabled>Download debug bundle</button>
      </div>
    </details>
    <div id="external-links" class="actions">
      <a class="btn" href="${DOCS_URL}" target="_blank" rel="noopener">${ICON_EXTERNAL}Open Docs</a>
$([ "${SHOW_DASHBOARD}" = "1" ] && printf '      <a class="btn btn-primary" href="%s" target="_blank" rel="noopener">%sOpen Dashboard</a>\n' "${DASHBOARD_URL}" "${ICON_EXTERNAL}")
    </div>
  </main>
EOF
cat <<'HTML'
  <script src="controls.js?v=6" defer></script>
</body>
</html>
HTML
