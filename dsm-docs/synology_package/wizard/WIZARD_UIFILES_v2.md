# WIZARD_UIFILES 7.2.2

## Overview

Three primary files describe UI components in JSON format: `install_uifile`, `upgrade_uifile`, and `uninstall_uifile`, stored in the "WIZARD_UIFILES" folder.

## File Types

**Static UI Files:**
- `install_uifile`: Installation process UI
- `upgrade_uifile`: Upgrade process UI
- `uninstall_uifile`: Uninstallation process UI

**Dynamic Script Files:**
- `install_uifile.sh`, `upgrade_uifile.sh`, `uninstall_uifile.sh`: Generate UI dynamically

**Localized Variants:**
Add language suffix: `install_uifile_[DSM language]` (e.g., `install_uifile_cht`)

## Project Structure

```
└── WIZARD_UIFILES
    ├── create_install_uifile.sh
    ├── create_uninstall_uifile.sh
    ├── create_upgrade_uifile.sh
    ├── Makefile
    ├── package.json
    ├── pnpm-lock.yaml
    ├── src
    │   ├── remove-entry.js
    │   ├── remove-setting.vue
    ├── uifile_setting.sh
    └── webpack.config.js
```

## Technical Stack

- Vue.js 2.7.14, Webpack 5.91.0, PNPM, Babel 7.18.6

## JSON Format

```json
[{
    "custom_render_fn": "/* render function */",
    "custom_render_name": "remove_setting"
}]
```

## Webpack Output

Uses JSONP format with external Vue dependency:

```javascript
output: {
    library: {
        name: 'SYNO.SDS.PkgManApp.Custom.JsonpLoader.load',
        type: 'jsonp',
    },
    path: resolve('dist'),
    filename: '[name].bundle.js'
}
```

## Package Center API

**SYNO.SDS.PkgManApp.Custom.useHook(props)** returns:
- `getNext()`: Get next step ID
- `checkState()`: Update wizard footer

## Vue Component Return Values

| Property | Description | Type |
|----------|-------------|------|
| getNext | Get next step ID | () => String |
| checkState | Update wizard footer | () => void |
| headline | Display wizard title | String |
| getValues | Obtain wizard data | () => Object[] |

## Entry File Pattern

```javascript
import RemoveSetting from './remove-setting.vue';
export default {
    name: 'remove_setting',
    render: RemoveSetting,
};
```

## Vue Component Example

```vue
<template>
    <pkg-center-step-content>
        <v-form syno-id="form">
            <v-form-item syno-id="form-item" label="Password">
                <v-input type="password" v-model="password" syno-id="password" />
            </v-form-item>
            <v-form-item syno-id="form-item" :label="removeSettingTitle">
                <v-checkbox v-model="valid" syno-id="checkbox">
                    Checkbox Value: {{ valid }}
                </v-checkbox>
            </v-form-item>
        </v-form>
    </pkg-center-step-content>
</template>

<script>
import { defineComponent, watchEffect, ref } from 'vue';
export default defineComponent({
    props: {
        ...SYNO.SDS.PkgManApp.Custom.useHook.props,
    },
    setup(props) {
        const { getNext, checkState: _checkState } = SYNO.SDS.PkgManApp.Custom.useHook(props);
        const valid = ref(false);
        const password = ref('');
        const checkState = (owner) => {
            owner = owner ?? props.getOwner();
            _checkState(owner);
            const nextButton = owner.getButton('next');
            nextButton.setDisabled(!valid.value);
        };
        const getValues = () => [{ isSelected: valid.value }];
        watchEffect(() => { checkState(); });
        return { getNext, checkState, headline: 'Title', getValues, valid, password };
    },
});
</script>
```

## Core Guidelines

- Entry files must return: `{ name: 'render_name', render: Component }`
- Vue files must contain `pkg-center-step-content` component
- All words are case-sensitive
- Refer to DSM UI Framework for available Vue.js components
