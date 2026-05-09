#!/bin/sh
# Generates the INFO file for the NetBird SPK package.
# Usage: ./INFO.sh <version> <extractsize> [arch_family]
#
# arch_family is one of: x86_64, aarch64
# It expands into the full Synology chip-family list per
# https://help.synology.com/developer-guide/appendix/platarchs.html
# DSM matches against specific chip tokens (apollolake, geminilake, etc.)
# at install time, so the family list must be enumerated.

VERSION="${1:?Usage: INFO.sh <version> <extractsize_kb> [arch_family]}"
EXTRACTSIZE="${2:-0}"
ARCH_FAMILY="${3:-x86_64}"

case "$ARCH_FAMILY" in
  x86_64)
    ARCH="apollolake avoton braswell broadwell broadwellnk broadwellntb broadwellntbap bromolow cedarview coffeelake denverton geminilake grantley kvmx64 purley skylaked v1000"
    ;;
  aarch64)
    # Synology calls this family "armv8" and it covers these chip tokens.
    ARCH="armada37xx rtd1296 rtd1619 rtd1619b"
    ;;
  *)
    # Allow passing through an explicit value for testing.
    ARCH="$ARCH_FAMILY"
    ;;
esac

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
