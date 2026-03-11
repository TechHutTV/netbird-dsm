# Checkbox Component

## Overview

The Checkbox component is a Vue form element for Synology DSM UI Framework.

## Template

```vue
<v-checkbox />
```

## Props

| Prop | Description | Type | Values | Default |
|------|-------------|------|--------|---------|
| subscribeField | Subscribe specific `register-key` form-item on ancestor | string | - | void 0 |
| activeFormItem | do not register on form-item | boolean | - | true |
| enterKey | used for `enterkeyhint` attribute, and will change behavior when enter key is pressed | string | - | EnterHint.Enter |
| boundaryComponentName | - | string | - | 'PortalTarget' |
| iconType | - | string | - | ICON_TYPE.FOLLOW_MANAGER |
| stopPropagation | If **true**, the click event of the checkbox will stop propagation. | boolean | - | false |
| v-model | If **true**, the status of the checkbox will be checked. | boolean | - | false |
| indeterminate | If **true**, the status of the checkbox will always be indeterminate state. | boolean | - | false |
| disabled | If **true**, the checkbox will be disabled. | boolean | - | false |
| id | ID of the checkbox | string | - | syno-{uuid} |
| ariaLabelledby | - | string | - | this.id |
| name | Name of the checkbox | string | - | void 0 |
| labelColor | Color of label | string | 'normal', 'red' | 'normal' |

## Methods

### onChange
Dispatch an event (form.change), first triggering it on the instance itself, and then propagates upward along the parent chain until finding the FormItem.

### onBlurInput
Dispatch an event (form.blur), first triggering it on the instance itself, and then propagates upward along the parent chain until finding the FormItem.

### onClick
If disabled is false, run onChange function.

## Events

| Event | Properties | Description |
|-------|-----------|-------------|
| focus-next-field | - | - |
| focus-prev-field | - | - |
| blur | component (checkbox instance) | Emitted when checkbox is blurred |
| input | checked (Boolean) | Emitted when checked state changes |
| change | val (Boolean), evt (EventObject) | Emitted when checked state changes |
| focus | component (checkbox instance) | Emitted when checkbox is focused |

## Slots

| Name | Description |
|------|-------------|
| default | Embed default slot to show checkbox label |
