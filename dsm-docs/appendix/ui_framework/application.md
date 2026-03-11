# Application

## Overview

The Application component is a DSM-Only component from the Synology DSM UI Framework.

## Usage Example

```vue
<template>
    <v-app-instance syno-id="app-instance" class-name="SYNO.SDS.XX.YY.Instance">
        <v-app-window
            syno-id="app-window"
            ref="appWindow"
            class="app-window-class"
            width=850
            height=574
            :resizable="false"
        >
            ...
        </v-app-window>
    </v-app-instance>
</template>
```

## Component Structure

The Application component uses a hierarchical structure:

### v-app-instance
Top-level container.

| Attribute | Description | Example |
|---|---|---|
| syno-id | Identifier attribute | "app-instance" |
| class-name | CSS class reference | "SYNO.SDS.XX.YY.Instance" |

### v-app-window
Child window component.

| Attribute | Description | Example |
|---|---|---|
| syno-id | Identifier for the window | "app-window" |
| ref | Vue template reference | "appWindow" |
| class | CSS class assignment | "app-window-class" |
| width | Window width in pixels | 850 |
| height | Window height in pixels | 574 |
| resizable | Boolean property controlling resize capability | false |
