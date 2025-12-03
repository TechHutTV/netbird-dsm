#!/bin/bash
# Copyright (c) 2024 NetBird DSM Package
# SPDX-License-Identifier: MIT

# Source the package toolkit helpers if available
if [ -f /pkgscripts-ng/include/pkg_util.sh ]; then
    . /pkgscripts-ng/include/pkg_util.sh
fi

# Package metadata
package="netbird"
version="0.60.4-0001"
os_min_ver="7.0-40000"
maintainer="NetBird DSM Package Maintainers"
maintainer_url="https://github.com/netbirdio/netbird"
distributor=""
distributor_url=""
arch="noarch"
silent_install="no"
silent_upgrade="no"
silent_uninstall="no"
dsmuidir="ui"
dsmappname="com.netbird.netbird"
displayname="NetBird"
description="NetBird is a WireGuard-based mesh network that connects your devices into a secure private network. Configure your setup key and management URL to join your NetBird network."
thirdparty="yes"
support_url="https://docs.netbird.io/"
helpurl="https://docs.netbird.io/"
report_url="https://github.com/netbirdio/netbird/issues"
startable="yes"
ctl_stop="yes"

# Architecture-specific version will be set during build
# This noarch package downloads the correct binary at install time

# Generate INFO file if called directly (not sourced)
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    if type pkg_dump_info &>/dev/null; then
        pkg_dump_info
    else
        # Manual output for testing without toolkit
        echo "package=\"${package}\""
        echo "version=\"${version}\""
        echo "os_min_ver=\"${os_min_ver}\""
        echo "maintainer=\"${maintainer}\""
        echo "maintainer_url=\"${maintainer_url}\""
        echo "arch=\"${arch}\""
        echo "silent_install=\"${silent_install}\""
        echo "silent_upgrade=\"${silent_upgrade}\""
        echo "silent_uninstall=\"${silent_uninstall}\""
        echo "dsmuidir=\"${dsmuidir}\""
        echo "dsmappname=\"${dsmappname}\""
        echo "displayname=\"${displayname}\""
        echo "description=\"${description}\""
        echo "thirdparty=\"${thirdparty}\""
        echo "support_url=\"${support_url}\""
        echo "helpurl=\"${helpurl}\""
        echo "report_url=\"${report_url}\""
        echo "startable=\"${startable}\""
        echo "ctl_stop=\"${ctl_stop}\""
    fi
fi
