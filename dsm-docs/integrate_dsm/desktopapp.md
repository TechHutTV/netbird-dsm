# Desktop Application

## Overview

Desktop applications appear in the DSM menu with customizable icon, privilege, and target URL. Multiple applications per package are supported for different user roles.

## Setup Steps

### 1. Create UI Directory
Create a directory within `package.tgz` (commonly named `ui`).

### 2. Configure dsmuidir in INFO

**Single application:**
```
dsmuidir="ui"
```

**Multiple applications:**
```
dsmuidir="MyApp1:appui1 MyApp2:appui2"
```

When identifiers are omitted, DSM uses the package name as identifier. Once installed, DSM creates soft links at `/usr/syno/synoman/webman/3rdparty/[identifier]/`.

### 3. Create Configuration Files
Add App Config and Help Config files under the dsmuidir directory.

### 4. Set dsmappname
```
dsmappname="com.company.App1"
```

Designates the target application when users click the open button in Package Center.
