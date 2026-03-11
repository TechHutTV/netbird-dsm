# Form Component

## Overview

This documentation covers the Form component API for Synology DSM Package Development, including `<v-form />`, `<v-form-item />`, `<v-form-multiple-item />`, and `<v-incremental-form-multiple-item />`.

---

## Form Item API

### Template

```vue
<v-form-item />
```

### Props

| Prop | Description | Type | Default |
|------|-------------|------|---------|
| prop | Pass 'prop' to `<v-form-item>` | string | void 0 |
| label | Label content | string | void 0 |
| disableLabel | Disable label display | boolean | false |
| disableDescription | Disable description | boolean | false |
| validateDisabledField | Validate disabled fields if true | boolean | false |
| disableValidation | Form won't validate all fields if true | boolean | false |
| hideValidateMessage | Validation message won't be shown if true | boolean | false |
| hideValidateStatusCls | Hide error status when validation fails | boolean | false |
| rules | Validation rules (async-validator format) | object/array | void 0 |
| help | Text for validation message | string | void 0 |
| validateStatus | Options: 'validating', 'success', 'warning', 'error' | string | void 0 |
| defaultValidateTrigger | Default trigger timing for rules | string | 'blur' |
| immediateValidate | Instantly validate with 'change' trigger if true | boolean | false |
| showMessage | Show validation message if true | boolean | true |
| hideLabel | Won't reserve space for label if true | boolean | false |
| textonly | Apply display-field style if true | boolean | false |
| indent | CSS variable on `--indent` | number/string | 0 |
| validateDebouncedTimer | Debounce milliseconds for validation | number | 250 |
| registerKey | Identify key for form-component registration | string | void 0 |
| validateMessageDisplayMode | Options: 'popup', 'text', 'form' | string | 'form' |
| fixInitialValue | Fix initial value | string | void 0 |
| wrapperFlex | Wrapper flex configuration | string/number/object | void 0 |
| controlFlex | Control flex configuration | string/number/object | void 0 |
| labelFlex | Label flex configuration | string/number/object | void 0 |

### Methods

#### showPopup(msg)
Show popup with message, displays previous message if undefined.

#### hidePopup()
Hide popup.

#### validate(trigger, options, extraRules)
Returns `Promise<string>`. Returns null for validated, returns string for error message.

#### resetField()
Reset all dirty field to initial value.

#### commit()
Commit changes.

#### resetInvalid()
Clear validate state and message.

### Events

| Event | Description |
|-------|-------------|
| validated | Emitted when validated (includes validate payload) |
| validating | Validation in progress |

### Slots

| Name | Description |
|------|-------------|
| before | Before input element |
| label | Label slot |
| label-before | Label before slot |
| label-after | Label after slot |
| default | Input fields in the form |
| status | Display status on validate message |
| description | Description slot |
| after | After input element |

---

## Form Multiple Item API

### Template

```vue
<v-form-multiple-item />
```

### Props

| Prop | Description | Type | Default |
|------|-------------|------|---------|
| label | Label content | string | void 0 |
| disableLabel | Disable label | boolean | false |
| hideLabel | Won't reserve space for label if true | boolean | false |
| marginSize | Margin between divs | string | 'small' |
| indent | CSS variable on `--indent` | number/string | 0 |
| gap | Space between grids | object/string/array/number | () => ['6px', '6px'] |
| flexWrap | Enable flex wrap | object/boolean | false |
| flexAlign | Flex alignment | object/boolean | void 0 |
| flexJustify | Flex justify | object/boolean | void 0 |
| flex | Flex setting | string | FOLLOW_FORM |
| labelFlex | Label flex | string/number/object | void 0 |
| itemsWrapperFlex | Items wrapper flex | string/number/object | void 0 |

### Slots

| Name | Description |
|------|-------------|
| label | Label slot |
| label-before | Label before slot |
| label-after | Label after slot |
| default | Default content |

---

## Form API

### Template

```vue
<v-form />
```

### Props

| Prop | Description | Type | Default |
|------|-------------|------|---------|
| flex | Open flex form to cover mobile layout | boolean/string | false |
| layoutOrder | Layout order | number | 0 |
| v-model | Form values | object | - |
| rules | Validation rules (async-validator) | object | - |
| direction | Form direction: 'horizontal', 'vertical', or adaptive | object/string | Adaptive by breakpoint |
| validateMessageDisplayMode | Options: 'popup', 'text' | string | 'popup' |

### Methods

#### findField(name)
Find field by HTML element name attribute. Returns vnode of the field.

#### resetFields()
Reset all dirty field to initial value.

#### validate(trigger)
Determine if all fields are valid. Returns `Promise<Boolean>`.

#### validateField(prop)
Validate specific field.

#### isDirty()
Check if all form-items are dirty. Returns Boolean.

#### commit()
Commit changes.

### Events

| Event | Description |
|-------|-------------|
| submit | Emitted when form is submitted |
| validated | Emitted when validated (includes validate payload) |

### Slots

| Name | Description |
|------|-------------|
| default | Input fields in the form |

---

## Incremental Form Multiple Item API

### Template

```vue
<v-incremental-form-multiple-item />
```

### Props

| Prop | Description | Type | Default |
|------|-------------|------|---------|
| iconType | Icon type | string | ICON_TYPE.FOLLOW_MANAGER |
| label | Label content | string | void 0 |
| disableLabel | Disable label | boolean | false |
| hideLabel | Won't reserve space for label if true | boolean | false |
| indent | CSS variable on `--indent` | number | 0 |
| items | Items array | array | [] |
| minItemsLength | Minimum items length | number | 0 |
| maxItemsLength | Maximum items length | number | void 0 |
| addText | Add button text | string | Returns 'add_field' i18n |
| disabledAddButton | Disable add button | boolean | void 0 |
| disabledRemoveButton | Disable remove button | boolean | false |
| gap | Space between items | object/string/array | () => [FORM_BASIC_GAP, FORM_BASIC_GAP] |
| columns | Grid columns number | number | 24 |
| labelFlex | Label flex | string/number/object | void 0 |
| itemsWrapperFlex | Items wrapper flex | string/number/object | void 0 |

### Events

| Event | Description |
|-------|-------------|
| update:items | Items updated |
| remove-item | Item removed |
| add-item | Item added |

### Slots

| Name | Description |
|------|-------------|
| label | Label slot |
| label-before | Label before slot |
| label-after | Label after slot |
| default | Default content |
| remove-field | Remove field slot |
| actions | Actions slot |
