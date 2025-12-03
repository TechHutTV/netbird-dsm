#!/bin/bash
# Copyright (c) 2024 NetBird DSM Package
# SPDX-License-Identifier: MIT

# CGI script for NetBird settings web interface

# Package paths
PACKAGE_DIR="/var/packages/netbird"
TARGET_DIR="${PACKAGE_DIR}/target"
CONFIG_DIR="${TARGET_DIR}/etc"
DATA_DIR="${TARGET_DIR}/var"
NETBIRD_BIN="${TARGET_DIR}/bin/netbird"
NETBIRD_CONFIG="${CONFIG_DIR}/config.json"
SETTINGS_FILE="${CONFIG_DIR}/netbird.json"
NETBIRD_SOCK="${DATA_DIR}/netbird.sock"

# CGI header
echo "Content-Type: text/html"
echo ""

# Parse query string for POST data
read_post_data() {
    if [ "${REQUEST_METHOD}" = "POST" ]; then
        read -n "${CONTENT_LENGTH}" POST_DATA
        echo "${POST_DATA}"
    fi
}

# URL decode function
urldecode() {
    local url_encoded="${1//+/ }"
    printf '%b' "${url_encoded//%/\\x}"
}

# Get current settings
get_settings() {
    local mgmt_url="https://api.netbird.io:443"
    local setup_key=""

    if [ -f "${SETTINGS_FILE}" ]; then
        mgmt_url=$(grep -oP '"ManagementURL"\s*:\s*"\K[^"]+' "${SETTINGS_FILE}" 2>/dev/null || echo "https://api.netbird.io:443")
        setup_key=$(grep -oP '"SetupKey"\s*:\s*"\K[^"]+' "${SETTINGS_FILE}" 2>/dev/null || echo "")
    fi

    echo "${mgmt_url}|${setup_key}"
}

# Get service status
get_status() {
    if pgrep -f "netbird.*service run" >/dev/null 2>&1; then
        if [ -x "${NETBIRD_BIN}" ] && [ -S "${NETBIRD_SOCK}" ]; then
            "${NETBIRD_BIN}" status --daemon-addr "unix://${NETBIRD_SOCK}" 2>/dev/null || echo "Running (status unavailable)"
        else
            echo "Running"
        fi
    else
        echo "Stopped"
    fi
}

# Save settings
save_settings() {
    local mgmt_url="$1"
    local setup_key="$2"

    mkdir -p "${CONFIG_DIR}"

    cat > "${SETTINGS_FILE}" << EOF
{
    "ManagementURL": "${mgmt_url}",
    "SetupKey": "${setup_key}",
    "AdminURL": "",
    "ConfigPath": "${CONFIG_DIR}/config.json",
    "LogFile": "${DATA_DIR}/netbird.log",
    "LogLevel": "info"
}
EOF

    chmod 600 "${SETTINGS_FILE}"
}

# Handle form submission
handle_post() {
    local post_data=$(read_post_data)
    local action=""
    local mgmt_url=""
    local setup_key=""

    # Parse POST parameters
    IFS='&' read -ra PARAMS <<< "${post_data}"
    for param in "${PARAMS[@]}"; do
        key="${param%%=*}"
        value="${param#*=}"
        value=$(urldecode "${value}")

        case "${key}" in
            action) action="${value}" ;;
            management_url) mgmt_url="${value}" ;;
            setup_key) setup_key="${value}" ;;
        esac
    done

    case "${action}" in
        save)
            save_settings "${mgmt_url}" "${setup_key}"
            echo "<div class='alert success'>Settings saved successfully.</div>"
            ;;
        connect)
            save_settings "${mgmt_url}" "${setup_key}"
            if [ -n "${setup_key}" ]; then
                "${NETBIRD_BIN}" up \
                    --setup-key "${setup_key}" \
                    --management-url "${mgmt_url}" \
                    --config "${NETBIRD_CONFIG}" \
                    --daemon-addr "unix://${NETBIRD_SOCK}" \
                    2>&1 && echo "<div class='alert success'>Connected to NetBird network.</div>" \
                         || echo "<div class='alert error'>Failed to connect. Check your setup key.</div>"
            else
                echo "<div class='alert error'>Setup key is required to connect.</div>"
            fi
            ;;
        disconnect)
            "${NETBIRD_BIN}" down \
                --config "${NETBIRD_CONFIG}" \
                --daemon-addr "unix://${NETBIRD_SOCK}" \
                2>&1 && echo "<div class='alert success'>Disconnected from NetBird network.</div>" \
                     || echo "<div class='alert error'>Failed to disconnect.</div>"
            ;;
    esac
}

# Parse current settings
IFS='|' read -r CURRENT_MGMT_URL CURRENT_SETUP_KEY <<< "$(get_settings)"
CURRENT_STATUS=$(get_status)

# Handle POST request
MESSAGE=""
if [ "${REQUEST_METHOD}" = "POST" ]; then
    MESSAGE=$(handle_post)
    # Refresh settings after save
    IFS='|' read -r CURRENT_MGMT_URL CURRENT_SETUP_KEY <<< "$(get_settings)"
    CURRENT_STATUS=$(get_status)
fi

# Output HTML
cat << 'HTMLHEAD'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NetBird Settings</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        h1 img {
            width: 48px;
            height: 48px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 30px;
            border-left: 4px solid #3498db;
        }
        .status-card.connected {
            border-left-color: #27ae60;
        }
        .status-card.disconnected {
            border-left-color: #e74c3c;
        }
        .status-label {
            font-weight: 600;
            color: #555;
            margin-bottom: 5px;
        }
        .status-value {
            font-size: 1.1em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #444;
        }
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            transition: border-color 0.2s;
        }
        input[type="text"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-color: #3498db;
        }
        .help-text {
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }
        .button-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 30px;
        }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .btn-primary {
            background: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background: #2980b9;
        }
        .btn-success {
            background: #27ae60;
            color: white;
        }
        .btn-success:hover {
            background: #219a52;
        }
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
        .alert {
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .alert.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .section-title {
            font-size: 1.2em;
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>
            <svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="50" r="45" fill="#3498db"/>
                <path d="M30 50 L50 30 L70 50 L50 70 Z" fill="white"/>
                <circle cx="50" cy="50" r="10" fill="#3498db"/>
            </svg>
            NetBird
        </h1>
        <p class="subtitle">Secure WireGuard-based mesh network for your Synology NAS</p>
HTMLHEAD

# Output message if any
if [ -n "${MESSAGE}" ]; then
    echo "${MESSAGE}"
fi

# Output status card
if echo "${CURRENT_STATUS}" | grep -qi "connected\|running"; then
    echo '<div class="status-card connected">'
else
    echo '<div class="status-card disconnected">'
fi

cat << HTMLSTATUS
            <div class="status-label">Connection Status</div>
            <div class="status-value">${CURRENT_STATUS}</div>
        </div>

        <form method="POST" action="">
            <h3 class="section-title">Network Settings</h3>

            <div class="form-group">
                <label for="management_url">Management URL</label>
                <input type="text" id="management_url" name="management_url"
                       value="${CURRENT_MGMT_URL}"
                       placeholder="https://api.netbird.io:443">
                <p class="help-text">The NetBird management server URL. Use default for NetBird Cloud or enter your self-hosted URL.</p>
            </div>

            <div class="form-group">
                <label for="setup_key">Setup Key</label>
                <input type="password" id="setup_key" name="setup_key"
                       value="${CURRENT_SETUP_KEY}"
                       placeholder="Enter your setup key">
                <p class="help-text">Your NetBird setup key from the dashboard. Required to join the network.</p>
            </div>

            <div class="button-group">
                <button type="submit" name="action" value="save" class="btn-primary">Save Settings</button>
                <button type="submit" name="action" value="connect" class="btn-success">Save & Connect</button>
                <button type="submit" name="action" value="disconnect" class="btn-danger">Disconnect</button>
            </div>
        </form>
    </div>
</body>
</html>
HTMLSTATUS
