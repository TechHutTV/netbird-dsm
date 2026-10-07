#!/bin/sh
# Keep the status page usable on systems without the controls' Python runtime.
PATH=/usr/local/bin:/usr/bin:/bin
export PATH
if command -v python3 >/dev/null 2>&1; then
    exec python3 -I -B /var/packages/netbird/target/libexec/ui-control.py
fi
printf 'Status: 503 Service Unavailable\r\nContent-Type: application/json\r\nCache-Control: no-store\r\nReferrer-Policy: no-referrer\r\n\r\n'
printf '%s\n' '{"ok":false,"message":"Connection controls require Python 3 on DSM. Use the NetBird CLI until it is available."}'
