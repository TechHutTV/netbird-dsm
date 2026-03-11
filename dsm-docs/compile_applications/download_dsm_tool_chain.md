# Download DSM Tool Chain

## Overview

The DSM Tool Chain is available through the Synology Archive and must be downloaded based on your specific NAS platform.

## Where to Download

Visit the [Synology Archive](https://archive.synology.com/download/ToolChain) to obtain the appropriate tool chain for your target platform.

## Identifying Your Platform

To determine which tool chain you need, execute this command on your Synology NAS:

```
DiskStation> uname -a
```

Example output:
```
Linux DiskStation 4.4.59+ #24922 SMP PREEMPT Mon Aug 19 12:13:37 CST 2019 x86_64 GNU/Linux synology_apollolake_718+
```

The platform identifier appears at the end of the output (e.g., "synology_apollolake_718+"). Use this to locate the corresponding tool chain on the Synology Archive.

Reference: Check the [platform list](https://kb.synology.com/en-global/DSM/tutorial/What_kind_of_CPU_does_my_NAS_have) if you need additional guidance.

## Installation

Extract the tool chain to `/usr/local/` using:

```bash
tar xJf apollolake-gcc493_glibc220_linaro_x86_64-GPL.txz -C /usr/local/
```

**Important:** The tool chain is located in the directory `/usr/local` on your computer to ensure proper integration.
