# Button Component

## Overview

The `<v-button />` component from the Synology Package Developer Guide UI Framework for DSM applications.

## Template

```vue
<v-button />
```

## Props

| Prop | Description | Type | Values | Default |
|------|-------------|------|--------|---------|
| subscribeField | Subscribe specific `register-key` form-item on ancestor | string | - | void 0 |
| activeFormItem | do not register on form-item | boolean | - | true |
| enterKey | used for `enterkeyhint` attribute, and will change behavior when enter key is pressed | string | - | EnterHint.Enter |
| boundaryComponentName | - | string | - | 'PortalTarget' |
| iconType | - | string | - | ICON_TYPE.FOLLOW_MANAGER |
| type | Button type. **Note**: `split` type only works when the `dropdown` slot is not empty. | string | '', 'footbar', 'dropdown', 'styleless', 'split', 'border', 'border-dropdown', 'border-split', 'footbar-border', 'footbar-border-dropdown', 'welcome', 'round', 'round-border' | '' |
| size | - | string | - | SIZE.NORMAL |
| display | Button display type. | string | 'text', 'icon', 'icon-text' | 'text' |
| suffix | Define the button custom suffix class | string | 'grey', 'blue', 'cancel', 'main', 'green', 'red', 'orange' | 'grey' |
| htmlType | htmlType of the button | string | 'submit', 'button', 'reset' | 'button' |
| disabled | If **true**, the button will be disabled. | boolean | - | false |
| icon | Class name the button's icon will have. | string | - | void 0 |
| menuAlign | Describe how the dropdown menu should be aligned to the button. | string | 'c', 't', 'b', 'l', 'r', 'tl', 'tr', 'bl', 'br' | 'tl->bl' |
| menuConstrainHeight | when menu height is out of popup container, it will constrain menu to fixed height | boolean | - | false |
| tooltip | Text for the button's tooltip. If **false**, will disable it. | object/string/boolean | - | false |
| dropdownOffset | Dropdown menu's position offset | array | - | [0, 1] |
| useBreakpoint | - | boolean | - | true |
| name | Will use this name on breakpoints button group | string | - | '' |
| mobileBreakpoint | Assign the breakpoint of button. Less or equal than the breakpoint you assigned, `mobile` class would be added to the button's class list. | string/boolean | 'xxxl', 'xxl', 'xl', 'lg', 'md', 'sm', 'xs', 'xxs', 'xxxs' | 'xxs' |
| active | Only works in button-group, it will turns to active state when you pass `true` | boolean | - | false |
| getExtraElements | customize extra elements for prevent click outside | func | - | void 0 |

## Methods

### handleClick
Method to handle click behavior.
- **Parameter**: evt (EventObject)

### setPressed
Remove menuContainer in this hook (if menuContainer is created).
- **Parameter**: pressed

## Events

| Event | Properties | Description |
|-------|-----------|-------------|
| focus-next-field | - | - |
| focus-prev-field | - | - |
| blur | - | - |
| dropdown-show | **value** `Boolean` | Emitted when the dropdown menu is opened/closed |
| dropdown-open | **value** `Boolean` | Emitted when dropdown menu is opened |
| dropdown-close | **value** `Boolean` | Emitted when dropdown menu is closed |
| click | **evt** `EventObject` | Emitted when button is clicked |
| click-dropdown | **item** `Object` | Emitted when the overflow toolbar item has been clicked |

## Slots

| Name | Description | Bindings |
|------|-------------|----------|
| icon | icon inside `<v-button>` | - |
| default | content inside `<v-button>` | - |
| dropdown | Dropdown content | - |
