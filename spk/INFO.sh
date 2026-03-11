#!/bin/sh
# Generates the INFO file for the NetBird SPK package.
# Usage: ./INFO.sh <version> <extractsize>

VERSION="${1:?Usage: INFO.sh <version> <extractsize_kb>}"
EXTRACTSIZE="${2:-0}"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')

cat <<EOF
package="netbird"
version="${VERSION}"
arch="x86_64"
description="NetBird Client - Connect your devices into a secure WireGuard-based mesh network"
displayname="NetBird"
maintainer="NetBird Community"
maintainer_url="https://github.com/netbirdio/netbird"
create_time="${TIMESTAMP}"
dsmuidir="ui"
dsmappname="SYNO.SDS.Netbird"
startstop_restart_services="nginx"
os_min_ver="7.0-40000"
os_max_ver=""
extractsize="${EXTRACTSIZE}"
EOF
