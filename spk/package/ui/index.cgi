#!/bin/sh

# NetBird DSM Status & Settings Page - CGI script

NETBIRD="/var/packages/netbird/target/bin/netbird"
PKGVAR="/var/packages/netbird/var"
CONFIG="${PKGVAR}/config.json"
DAEMON_ADDR="unix://${PKGVAR}/netbird.sock"
LOG_FILE="${PKGVAR}/netbird.log"

# Environment variables needed for netbird CLI to talk to the daemon
export NB_DAEMON_ADDR="${DAEMON_ADDR}"
export NB_CONFIG="${CONFIG}"
export NB_STATE_DIR="${PKGVAR}"
export HOME="${PKGVAR}"

# Common CLI args
NB="$NETBIRD --daemon-addr $DAEMON_ADDR --config $CONFIG"

# Handle POST requests
RESULT_MSG=""
if [ "${REQUEST_METHOD}" = "POST" ]; then
    read -r POST_DATA
    urldecode() {
        echo "$1" | sed 's/+/ /g; s/%\([0-9A-Fa-f][0-9A-Fa-f]\)/\\x\1/g' | xargs -0 printf "%b"
    }
    ACTION=""
    SETUP_KEY=""
    MGMT_URL=""
    IFS='&'
    for pair in ${POST_DATA}; do
        key="${pair%%=*}"
        val="${pair#*=}"
        case "${key}" in
            action) ACTION=$(urldecode "${val}") ;;
            setup_key) SETUP_KEY=$(urldecode "${val}") ;;
            management_url) MGMT_URL=$(urldecode "${val}") ;;
        esac
    done
    unset IFS

    if [ "${ACTION}" = "connect" ]; then
        UP_ARGS=""
        if [ -n "${SETUP_KEY}" ]; then
            UP_ARGS="${UP_ARGS} --setup-key ${SETUP_KEY}"
        fi
        if [ -n "${MGMT_URL}" ]; then
            UP_ARGS="${UP_ARGS} --management-url ${MGMT_URL}"
        fi
        OUTPUT=$(${NB} up ${UP_ARGS} 2>&1)
        RESULT_MSG="Connect: ${OUTPUT}"
        # Redirect to GET after POST (PRG pattern) - avoids form resubmit on refresh
        # Small delay for connect to let daemon establish connection
        echo "Content-Type: text/html"
        echo ""
        echo "<html><head><meta http-equiv=\"refresh\" content=\"3\"></head><body style=\"font-family:sans-serif;padding:40px;background:#f4f6f7;color:#181A1D;\"><p>Connecting... please wait.</p></body></html>"
        exit 0
    elif [ "${ACTION}" = "disconnect" ]; then
        OUTPUT=$(${NB} down 2>&1)
        RESULT_MSG="Disconnect: ${OUTPUT}"
        echo "Content-Type: text/html"
        echo ""
        echo "<html><head><meta http-equiv=\"refresh\" content=\"2\"></head><body style=\"font-family:sans-serif;padding:40px;background:#f4f6f7;color:#181A1D;\"><p>Disconnecting... please wait.</p></body></html>"
        exit 0
    fi
fi

# Get status using text output (much easier to parse than JSON)
STATUS_TEXT=$(${NB} status -d 2>/dev/null)
STATUS_EXIT=$?

# Parse text output - each field is on its own line, unindented for self
NB_IP=""
FQDN=""
MGMT_STATUS=""
SIGNAL_STATUS=""
DAEMON_VER=""
PEERS_INFO=""
IFACE_TYPE=""
IS_CONNECTED=""

if [ ${STATUS_EXIT} -eq 0 ] && [ -n "${STATUS_TEXT}" ]; then
    NB_IP=$(echo "${STATUS_TEXT}" | grep "^NetBird IP:" | head -1 | sed 's/^NetBird IP:[[:space:]]*//')
    FQDN=$(echo "${STATUS_TEXT}" | grep "^FQDN:" | head -1 | sed 's/^FQDN:[[:space:]]*//')
    MGMT_STATUS=$(echo "${STATUS_TEXT}" | grep "^Management:" | head -1 | sed 's/^Management:[[:space:]]*//')
    SIGNAL_STATUS=$(echo "${STATUS_TEXT}" | grep "^Signal:" | head -1 | sed 's/^Signal:[[:space:]]*//')
    DAEMON_VER=$(echo "${STATUS_TEXT}" | grep "^Daemon version:" | head -1 | sed 's/^Daemon version:[[:space:]]*//')
    PEERS_INFO=$(echo "${STATUS_TEXT}" | grep "^Peers count:" | head -1 | sed 's/^Peers count:[[:space:]]*//')
    IFACE_TYPE=$(echo "${STATUS_TEXT}" | grep "^Interface type:" | head -1 | sed 's/^Interface type:[[:space:]]*//')

    case "${MGMT_STATUS}" in
        Connected*) IS_CONNECTED="yes" ;;
    esac
fi

# Read management URL from config.json for settings pre-fill
MGMT_URL_VAL=$(grep -o '"ManagementURL":"[^"]*"' "${CONFIG}" 2>/dev/null | head -1 | cut -d'"' -f4)

# ── HTML Output ──
echo "Content-Type: text/html"
echo ""

cat <<'HTML_HEAD'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NetBird Client</title>
<style>
  :root {
    --nb-orange: #f68330;
    --nb-orange-hover: #e5721f;
    --nb-orange-light: #fff6ed;
    --nb-orange-50: #fef3e7;
    --nb-blue: #31e4f5;
    --nb-gray-950: #181A1D;
    --nb-gray-900: #1e2124;
    --nb-gray-800: #2a2e33;
    --nb-gray-700: #3b4148;
    --nb-gray-500: #6b7280;
    --nb-gray-400: #9ca3af;
    --nb-gray-300: #d1d5db;
    --nb-gray-200: #e5e7eb;
    --nb-gray-100: #f0f1f3;
    --nb-gray-50: #f4f6f7;
    --nb-green: #10b981;
    --nb-green-light: #d1fae5;
    --nb-red: #ef4444;
    --nb-red-light: #fee2e2;
    --nb-text: #181A1D;
    --nb-text-secondary: #6b7280;
    --nb-border: #e5e7eb;
    --nb-bg: #f4f6f7;
    --nb-card: #ffffff;
    --nb-radius: 8px;
    --nb-radius-sm: 6px;
    --nb-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
  }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", Helvetica, Arial, sans-serif;
    margin: 0; padding: 0;
    background: var(--nb-bg); color: var(--nb-text);
    font-size: 14px; line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }

  /* Header bar */
  .header {
    background: var(--nb-gray-950);
    padding: 16px 24px;
    display: flex; align-items: center; gap: 12px;
  }
  .header-logo {
    width: 28px; height: 28px;
    border-radius: 4px;
    object-fit: contain;
  }
  .header h1 {
    margin: 0; font-size: 16px; font-weight: 600;
    color: #ffffff; letter-spacing: -0.01em;
  }
  .header .version {
    font-size: 12px; color: var(--nb-gray-500);
    margin-left: auto;
  }

  .container { max-width: 840px; margin: 0 auto; padding: 24px; }

  /* Status badge */
  .status-bar {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 20px;
  }
  .status-dot {
    width: 10px; height: 10px; border-radius: 50%;
    display: inline-block; flex-shrink: 0;
  }
  .status-dot-green { background: var(--nb-green); box-shadow: 0 0 6px rgba(16,185,129,0.4); }
  .status-dot-red { background: var(--nb-red); box-shadow: 0 0 6px rgba(239,68,68,0.3); }
  .status-dot-gray { background: var(--nb-gray-400); }
  .status-label {
    font-size: 14px; font-weight: 600;
    color: var(--nb-text);
  }
  .status-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 600;
  }
  .badge-connected { background: var(--nb-green-light); color: #065f46; }
  .badge-disconnected { background: var(--nb-red-light); color: #991b1b; }
  .badge-stopped { background: var(--nb-gray-200); color: var(--nb-gray-700); }

  /* Cards */
  .card {
    background: var(--nb-card);
    border: 1px solid var(--nb-border);
    border-radius: var(--nb-radius);
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: var(--nb-shadow);
  }
  .card-title {
    font-size: 13px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--nb-text-secondary);
    margin: 0 0 16px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--nb-gray-100);
  }

  /* Info table */
  .info-grid {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 8px 16px;
    font-size: 13px;
  }
  .info-label { color: var(--nb-text-secondary); font-weight: 500; }
  .info-value { color: var(--nb-text); font-weight: 400; }
  .info-value code {
    font-family: "SF Mono", "Fira Code", "Fira Mono", Menlo, monospace;
    font-size: 12px; background: var(--nb-gray-50);
    padding: 2px 6px; border-radius: 4px;
    border: 1px solid var(--nb-gray-200);
  }
  .info-value .connected { color: var(--nb-green); font-weight: 500; }
  .info-value .disconnected { color: var(--nb-red); font-weight: 500; }

  /* Peers */
  .peer-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid var(--nb-gray-100);
    font-size: 13px;
  }
  .peer-item:last-child { border-bottom: none; }
  .peer-name { font-weight: 600; color: var(--nb-text); }
  .peer-ip {
    font-family: "SF Mono", "Fira Code", Menlo, monospace;
    font-size: 12px; color: var(--nb-text-secondary);
  }
  .peer-tag {
    font-size: 11px; padding: 2px 8px; border-radius: 10px;
    font-weight: 500; margin-left: auto;
  }
  .peer-tag-connected { background: var(--nb-green-light); color: #065f46; }
  .peer-tag-disconnected { background: var(--nb-gray-200); color: var(--nb-gray-700); }
  .peer-conn-type {
    font-size: 11px; color: var(--nb-text-secondary);
    background: var(--nb-gray-50); padding: 2px 6px;
    border-radius: 4px; border: 1px solid var(--nb-gray-200);
  }

  /* Forms */
  .form-group { margin-bottom: 14px; }
  .form-label {
    display: block; font-size: 13px; font-weight: 500;
    color: var(--nb-text); margin-bottom: 6px;
  }
  .form-input {
    width: 100%; padding: 9px 12px;
    border: 1px solid var(--nb-border); border-radius: var(--nb-radius-sm);
    font-size: 13px; color: var(--nb-text);
    background: var(--nb-card);
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  .form-input:focus {
    border-color: var(--nb-orange);
    outline: none;
    box-shadow: 0 0 0 3px rgba(246,131,48,0.12);
  }
  .form-input::placeholder { color: var(--nb-gray-400); }

  /* Buttons */
  .btn {
    display: inline-flex; align-items: center; justify-content: center;
    gap: 6px; padding: 9px 18px;
    border: none; border-radius: var(--nb-radius-sm);
    font-size: 13px; font-weight: 500;
    cursor: pointer; transition: all 0.15s;
    text-decoration: none; line-height: 1;
  }
  .btn-primary {
    background: var(--nb-orange); color: #fff;
  }
  .btn-primary:hover { background: var(--nb-orange-hover); }
  .btn-danger {
    background: #fff; color: var(--nb-red);
    border: 1px solid var(--nb-red);
  }
  .btn-danger:hover { background: var(--nb-red-light); }
  .btn-ghost {
    background: var(--nb-card); color: var(--nb-text-secondary);
    border: 1px solid var(--nb-border);
  }
  .btn-ghost:hover { background: var(--nb-gray-50); color: var(--nb-text); }

  .btn-row { display: flex; gap: 8px; margin-top: 16px; margin-bottom: 24px; }

  /* Alert */
  .alert {
    padding: 12px 16px; border-radius: var(--nb-radius-sm);
    margin-bottom: 16px; font-size: 13px;
    border: 1px solid;
  }
  .alert-info {
    background: var(--nb-orange-50); color: #92400e;
    border-color: #fde68a;
  }

  /* Debug */
  details { margin-top: 4px; }
  details summary {
    cursor: pointer; color: var(--nb-gray-400);
    font-size: 12px; user-select: none;
  }
  details summary:hover { color: var(--nb-text-secondary); }
  pre.debug {
    background: var(--nb-gray-950); color: var(--nb-gray-300);
    padding: 14px; border-radius: var(--nb-radius-sm);
    overflow-x: auto; font-size: 12px; max-height: 300px;
    overflow-y: auto; white-space: pre-wrap; word-break: break-all;
    font-family: "SF Mono", "Fira Code", Menlo, monospace;
    line-height: 1.6;
  }
</style>
</head>
<body>
HTML_HEAD

# ── Header ──
if [ -n "${DAEMON_VER}" ]; then
    VER_DISPLAY="v${DAEMON_VER}"
else
    VER_DISPLAY=""
fi

cat <<HTML_HEADER
<div class="header">
  <img class="header-logo" src="PACKAGE_ICON_256.PNG" alt="NetBird">
  <h1>NetBird Client</h1>
  <span class="version">${VER_DISPLAY}</span>
</div>
<div class="container">
HTML_HEADER

# Show result message from POST action
if [ -n "${RESULT_MSG}" ]; then
    cat <<HTML_RESULT
<div class="alert alert-info">${RESULT_MSG}</div>
HTML_RESULT
fi

if [ ${STATUS_EXIT} -ne 0 ] || [ -z "${STATUS_TEXT}" ]; then
    # Daemon not reachable
    cat <<'HTML_NOT_RUNNING'
<div class="status-bar">
  <span class="status-dot status-dot-gray"></span>
  <span class="status-label">Not Running</span>
  <span class="status-badge badge-stopped">Stopped</span>
</div>
<div class="card">
  <p style="margin:0; color: var(--nb-text-secondary); font-size: 13px;">
    NetBird daemon is not reachable. Start the package from Package Center.
  </p>
</div>
HTML_NOT_RUNNING
else
    # ── Status Bar ──
    if [ "${IS_CONNECTED}" = "yes" ]; then
        cat <<'HTML_CONN_BADGE'
<div class="status-bar">
  <span class="status-dot status-dot-green"></span>
  <span class="status-label">Connected</span>
  <span class="status-badge badge-connected">Online</span>
</div>
HTML_CONN_BADGE
    else
        cat <<'HTML_DISC_BADGE'
<div class="status-bar">
  <span class="status-dot status-dot-red"></span>
  <span class="status-label">Disconnected</span>
  <span class="status-badge badge-disconnected">Offline</span>
</div>
HTML_DISC_BADGE
    fi

    # ── Connection Card ──
    # Determine status CSS classes
    MGMT_CLASS="disconnected"
    case "${MGMT_STATUS}" in Connected*) MGMT_CLASS="connected" ;; esac
    SIGNAL_CLASS="disconnected"
    case "${SIGNAL_STATUS}" in Connected*) SIGNAL_CLASS="connected" ;; esac

    cat <<HTML_STATUS
<div class="card">
  <h2 class="card-title">Connection</h2>
  <div class="info-grid">
    <span class="info-label">NetBird IP</span>
    <span class="info-value"><code>${NB_IP:-N/A}</code></span>
    <span class="info-label">FQDN</span>
    <span class="info-value"><code>${FQDN:-N/A}</code></span>
    <span class="info-label">Management</span>
    <span class="info-value"><span class="${MGMT_CLASS}">${MGMT_STATUS:-Unknown}</span></span>
    <span class="info-label">Signal</span>
    <span class="info-value"><span class="${SIGNAL_CLASS}">${SIGNAL_STATUS:-Unknown}</span></span>
    <span class="info-label">Interface</span>
    <span class="info-value">${IFACE_TYPE:-N/A}</span>
    <span class="info-label">Peers</span>
    <span class="info-value">${PEERS_INFO:-0/0}</span>
  </div>
</div>
HTML_STATUS

    # ── Peers Card ──
    PEER_HTML=$(echo "${STATUS_TEXT}" | awk '
    /^[[:space:]]+[^[:space:]].*:$/ {
        if (peer_name != "") print_peer()
        name = $0
        gsub(/^[[:space:]]+/, "", name)
        gsub(/:$/, "", name)
        peer_name = name
        peer_ip = ""
        peer_status = ""
        peer_conn = ""
    }
    /^[[:space:]]+NetBird IP:/ {
        val = $0; gsub(/.*NetBird IP:[[:space:]]*/, "", val); peer_ip = val
    }
    /^[[:space:]]+Status:/ {
        val = $0; gsub(/.*Status:[[:space:]]*/, "", val); peer_status = val
    }
    /^[[:space:]]+Connection type:/ {
        val = $0; gsub(/.*Connection type:[[:space:]]*/, "", val); peer_conn = val
    }
    function print_peer() {
        if (peer_name == "") return
        tc = "peer-tag-disconnected"
        if (peer_status == "Connected") tc = "peer-tag-connected"
        printf "<div class=\"peer-item\">"
        printf "<span class=\"peer-name\">%s</span>", peer_name
        if (peer_ip != "") printf "<span class=\"peer-ip\">%s</span>", peer_ip
        if (peer_conn != "" && peer_conn != "-" && peer_status == "Connected")
            printf "<span class=\"peer-conn-type\">%s</span>", peer_conn
        if (peer_status != "") printf "<span class=\"peer-tag %s\">%s</span>", tc, peer_status
        printf "</div>\n"
    }
    END { if (peer_name != "") print_peer() }
    ')

    if [ -n "${PEER_HTML}" ]; then
        echo '<div class="card">'
        echo '<h2 class="card-title">Peers</h2>'
        echo "${PEER_HTML}"
        echo '</div>'
    fi

    # ── Action Buttons ──
    if [ "${IS_CONNECTED}" = "yes" ]; then
        cat <<'HTML_DISCONNECT'
<div class="btn-row">
  <form method="POST" style="display:inline">
    <input type="hidden" name="action" value="disconnect">
    <button type="submit" class="btn btn-danger">Disconnect</button>
  </form>
  <a class="btn btn-ghost" href="javascript:location.reload()">Refresh</a>
</div>
HTML_DISCONNECT
    else
        cat <<'HTML_REFRESH_ONLY'
<div class="btn-row">
  <a class="btn btn-ghost" href="javascript:location.reload()">Refresh</a>
</div>
HTML_REFRESH_ONLY
    fi
fi

# ── Settings Card (always shown) ──
FORM_MGMT_URL="${MGMT_URL_VAL:-https://api.netbird.io:443}"

cat <<HTML_SETTINGS
<div class="card">
  <h2 class="card-title">Settings</h2>
  <form method="POST">
    <input type="hidden" name="action" value="connect">
    <div class="form-group">
      <label class="form-label" for="setup_key">Setup Key</label>
      <input class="form-input" type="password" id="setup_key" name="setup_key" placeholder="Enter setup key from your NetBird dashboard">
    </div>
    <div class="form-group">
      <label class="form-label" for="management_url">Management URL</label>
      <input class="form-input" type="text" id="management_url" name="management_url" placeholder="https://api.netbird.io:443" value="${FORM_MGMT_URL}">
    </div>
    <button type="submit" class="btn btn-primary">Connect</button>
  </form>
</div>
HTML_SETTINGS

# ── Debug Section ──
cat <<'HTML_DEBUG_START'
<div style="margin-top: 8px; margin-bottom: 24px;">
  <details>
    <summary>Debug output</summary>
HTML_DEBUG_START

echo '<pre class="debug">'
echo "Exit code: ${STATUS_EXIT}"
echo "---"
echo "${STATUS_TEXT}" | sed 's/</\&lt;/g; s/>/\&gt;/g'
echo '</pre>'
echo '</details></div>'

cat <<'HTML_END'
</div>
</body>
</html>
HTML_END
