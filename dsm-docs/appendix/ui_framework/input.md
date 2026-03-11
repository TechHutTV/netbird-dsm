# Input Component

## Overview

The `<v-input />` component is a Vue-based input element with extensive customization options for text, textarea, and password inputs.

## Template

```vue
<v-input />
```

## Props

| Prop | Description | Type | Default |
|------|-------------|------|---------|
| subscribeField | Subscribe to specific register-key form-item on ancestor | string | void 0 |
| activeFormItem | Do not register on form-item | boolean | true |
| enterKey | Used for enterkeyhint attribute; changes behavior on enter press | string | EnterHint.Enter |
| boundaryComponentName | - | string | 'PortalTarget' |
| iconType | - | string | ICON_TYPE.FOLLOW_MANAGER |
| type | Input type (text, textarea, password) | string | 'text' |
| id | Component ID | string | syno-{uuid} |
| v-model | Component value | string/number | void 0 |
| placeholder | Text shown when empty | string/number | '' |
| disabled | Disable the component | boolean | false |
| autosize | Auto-resize component | boolean/object | false |
| strengthChecker | Password strength validation | func/boolean | false |
| mask | Input masking pattern | RegExp/func | null |
| numberOnly | Accept only numbers | boolean | false |
| defaultShowStrengthChecker | Always show strength checker | boolean | false |
| maxlength | Maximum input length | number | void 0 |
| readonly | Read-only mode | boolean | false |
| focusClass | Class on focus | boolean/string | 'focused' |
| disableHoverStyle | Disable hover styling | boolean | false |
| fitContainer | Fit specified container width | boolean | true |
| autocomplete | Autocomplete attribute | string | 'off' |
| showPasswordVisibilityIcon | Show password visibility toggle | boolean | true |
| clearable | Show clear button | boolean | false |
| selectOnFocus | Select text on focus | boolean | false |
| passwordPortalName | - | string | 'password-portal' + random |
| passwordRules | - | array | [] |
| mobileBreakpoint | - | string/boolean | 'xxs' |

## Events

| Event | Properties | Description |
|-------|-----------|-------------|
| focus-next-field | - | Navigate to next field |
| focus-prev-field | - | Navigate to previous field |
| blur | - | Emitted when input loses focus |
| input | - | Emitted on native input event |
| focus | - | Emitted when focused |
| strength-check | strength, strengthText | Emitted with strength and strengthText properties |
| paste | - | Emitted on paste event |
| keyup | - | Emitted on keyup event |
| keydown | - | Emitted on keydown event |
| clear | - | Emitted when clear button clicked |

## Slots

| Name | Description |
|------|-------------|
| password-rule-header | Custom password rule header |
| suffix-icons | Input suffix icons |
| prefix | Input prefix (not for textarea) |
| suffix | Input suffix (not for textarea) |
