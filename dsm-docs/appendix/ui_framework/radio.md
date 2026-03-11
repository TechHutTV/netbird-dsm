# Radio Component

## Overview

This page documents the Radio UI component for the Synology Package Developer Guide, covering `<v-radio />` and `<v-radio-group />` elements.

---

## Radio Group API

### Template

```vue
<v-radio-group />
```

### Props

| Prop | Description | Type | Default |
|------|-------------|------|---------|
| subscribeField | Subscribe to specific `register-key` form-item | string | void 0 |
| activeFormItem | Register on form-item | boolean | true |
| enterKey | Controls `enterkeyhint` attribute behavior | string | EnterHint.Enter |
| boundaryComponentName | Portal boundary component | string | 'PortalTarget' |
| v-model | Selected `<v-radio>` with matching value | string/number/boolean | '' |
| data | Generates radio buttons via this prop | RadioGroupData[] | [] |
| disabled | Disables entire group | boolean | false |
| name | Component name | string | syno-{uuid} |
| deactiveChildrenFormItems | Prevents child form-item registration | function/boolean | () => vRadio |

### RadioGroupData Structure

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| text | string | false | - | Radio button label text |
| value | string | true | - | Radio button value |
| disabled | boolean | false | false | Individual button disabled state |

### Events

| Event | Properties | Description |
|-------|-----------|-------------|
| focus-next-field | - | Navigation event |
| focus-prev-field | - | Navigation event |
| blur | - | Focus lost event |
| input | value | Emitted on value change |
| change | value | Emitted on value change |

### Slots

| Name | Description |
|------|-------------|
| default | Content slot for radio buttons |

---

## Radio API

### Template

```vue
<v-radio />
```

### Props

| Prop | Description | Type | Default |
|------|-------------|------|---------|
| iconType | Icon style | string | ICON_TYPE.FOLLOW_MANAGER |
| subscribeField | Form-item subscription key | string | void 0 |
| activeFormItem | Register on form-item | boolean | true |
| enterKey | Enter key hint behavior | string | EnterHint.Enter |
| boundaryComponentName | Portal boundary | string | 'PortalTarget' |
| stopPropagation | Stop click event propagation | boolean | false |
| value | Button value | string/number/boolean | '' |
| v-model | Selected value | string/number/boolean | '' |
| disabled | Disable button | boolean | false |
| id | Component ID | string | syno-{uuid} |
| name | Component name | string | '' |
| labelColor | Label color | string ('normal', 'red') | 'normal' |

### Events

| Event | Properties | Description |
|-------|-----------|-------------|
| focus-next-field | - | Navigation |
| focus-prev-field | - | Navigation |
| blur | - | Component unfocused |
| input | - | Value changed |
| focus | - | Component focused |
| click | - | Component clicked |

### Slots

| Name | Description |
|------|-------------|
| default | Label content slot |
