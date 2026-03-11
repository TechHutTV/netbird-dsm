# Resource Update

## Overview

Update package resources outside of standard worker timing cycles using `synopkghelper`.

## Update Procedure

1. Modify the configuration file at `/var/packages/[package_name]/conf/resource`
2. Execute: `/usr/syno/sbin/synopkghelper update [package_name] [resource_id]`

## Example Use Case

A package that lets users modify listening port:

1. User provides a new port through the application UI
2. Application updates `/var/packages/[package_name]/conf/resource`
3. Application runs `/usr/syno/sbin/synopkghelper update ${package} port-config`
4. The port-config worker reads the updated config and applies changes

## Limitations

Not all resources support the update operation. Check the "Updatable" section in each resource's documentation.
