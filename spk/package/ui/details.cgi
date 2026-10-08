#!/bin/sh
PATH=/usr/local/bin:/usr/bin:/bin
export PATH
if command -v python3 >/dev/null 2>&1; then
    exec python3 -I -B /var/packages/netbird/target/libexec/ui-control.py --details
fi
printf 'Status: 503 Service Unavailable\r\nContent-Type: application/json\r\nCache-Control: no-store\r\n\r\n{"ok":false,"message":"Diagnostics require Python 3 on DSM."}\n'
