# Getting Started

## What Packages Can Do

Packages developed for Synology systems have the capability to:

- Access DSM API
- Access owned data share folders
- Integrate desktop applications
- Integrate help documentation
- Integrate firewall rules
- Integrate resource monitoring
- Define lifecycle behavior
- Define relationships between packages
- Define identity privilege

## Package Development Workflow

**1. Prepare a NAS**
Select hardware from the official Synology website and purchase through authorized partners. Plus Series devices are recommended.

**2. Prepare Development Environments**
Since NAS is not always in `x86` or `x86_64` architecture, prepare corresponding environment for cross compiling if developing in C/C++. The platform provides tools for creating development environments.

**3. Decide Your Application Type**
Create packages for Node.js, PHP, Perl, Python, or Java. Official runtime packages are available for all these languages.

**4. Determine Publication Plans**
Decide whether to publish on the official Synology Package Center.

## Next Steps

- System Requirements
- Prepare Environment
- Your First Package
