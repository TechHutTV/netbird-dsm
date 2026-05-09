#!/bin/sh
# Generates the INFO file for the NetBird SPK package.
# Usage: ./INFO.sh <version> <extractsize> [arch]

VERSION="${1:?Usage: INFO.sh <version> <extractsize_kb> [arch]}"
EXTRACTSIZE="${2:-0}"
ARCH="${3:-x86_64}"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')

cat <<EOF
package="netbird"
version="${VERSION}"
arch="${ARCH}"
description="NetBird is an Open Source Zero Trust Networking platform that allows you to create secure private networks for your organization or home. We designed NetBird to be simple and fast, requiring near-zero configuration effort and leaving behind the hassle of opening ports, complex firewall rules, VPN gateways, etc."
displayname="NetBird"
maintainer="NetBird"
maintainer_url="https://github.com/netbirdio/netbird"
create_time="${TIMESTAMP}"
os_min_ver="7.0-40000"
os_max_ver=""
extractsize="${EXTRACTSIZE}"
dsmuidir="ui"
dsmappname="com.netbird.netbird"
EOF
