# Select Component

## Overview

The Select component enables users to choose one or multiple items from a dropdown menu. It functions as both a standard selector and a searchable filter. The component requires **v-model** binding for value management.

Two primary components exist:
- `<v-single-select />`
- `<v-multiple-select />`

---

## Select Input API

### Props

| Prop | Description | Type | Default |
|------|-------------|------|---------|
| iconType | Icon styling | string | ICON_TYPE.FOLLOW_MANAGER |
| clearIconCls | Clear button classes | array | [] |
| searchIconCls | Search icon classes | array | [] |
| allowClear | Enable clear functionality | boolean | false |
| allowEdit | Allow text editing | boolean | false |
| value | Component value | string | '' |
| clearable | Display clear button | boolean | false |
| hideTrigger | Hide dropdown arrow | boolean | undefined |
| placeholder | Placeholder text | string | '' |
| disabled | Disable component | boolean | false |
| displayField | Option label field name | string | 'label' |
| valueField | Option value field name | string | 'value' |
| triggerQueryAction | Search trigger type | string | 'all' |
| autoOpenDropdownCharCount | Auto-open threshold | number | -1 |
| toggleDropdownOnClick | Toggle on click | boolean | true |
| mode | Display mode | string | 'normal' |
| displayMode | Text rendering mode | string | 'none' |
| enterKeyHint | Enter key behavior | string | undefined |

### Events

| Event | Description |
|-------|-------------|
| click-icon | Icon clicked |
| click-advanced-icon | Advanced icon clicked |
| input | Value changed |
| key-enter | Enter key pressed |
| key-esc | Escape key pressed |
| arrow-up | Up arrow pressed |
| arrow-down | Down arrow pressed |
| keydown | Key pressed down |
| focus | Component focused |
| blur | Component blurred |
| clear | Cleared |

### Slots

| Name | Description |
|------|-------------|
| icon | Icon slot |
| clear-icon | Custom clear button |
| dropdown-icon | Custom dropdown indicator |
| right | Custom search icon |

---

## Multiple Select API

### Props (includes all Select Input props plus)

| Prop | Description | Type | Default |
|------|-------------|------|---------|
| selectedOptions | Array of selected items | array | [] |
| getOptionTooltip | Tooltip mapping function | func | - |
| allowInvalidLabel | Allow invalid labels | boolean | false |
| displayText | Custom display text | string/boolean | false |
| labelEditable | Enable label editing | boolean | false |
| displayMode | Label display type | string | 'label' |

### Events (includes Select Input events plus)

| Event | Description |
|-------|-------------|
| is-editing | Editing state changed |
| item-removed | Item removed |
| reposition-menu | Menu repositioned |
| commit | Changes committed |
| focus-out | Focus lost |
| focus-in | Focus gained |
| editing-label-input | Label input editing |

---

## Single Select & Multiple Select Components

### Single Select Props

| Prop | Description | Type | Values | Default |
|------|-------------|------|--------|---------|
| v-model | Selected value | array/number/string/boolean | - | undefined |
| id | Component identifier | string | - | syno-{uuid} |
| name | Component name | string | - | '' |
| width | Component width | number/string | - | 250 |
| maxHeight | Dropdown max height | number/string | - | 200 |
| dropdownWidth | Dropdown width | number/string | - | undefined |
| dropdownOffset | Position offset | array | - | [0, 1] |
| customDropdownCls | Custom CSS classes | string | - | '' |
| disabled | Disable selection | boolean | - | false |
| filter | Custom filter function | func | - | undefined |
| search | Enable search mode | func | - | undefined |
| align | Dropdown alignment | string | 'c', 't', 'b', 'l', 'r', 'tl', 'tr', 'bl', 'br' | 'tl->bl' |
| minSearchChar | Minimum search length | number/string | - | 1 |
| loadingText | Loading message | string | - | 'searching' |
| notFoundText | No results message | string | - | 'no_search_result' |
| tooltip | Enable item tooltips | boolean | - | false |
| mapOptionToTooltip | Tooltip content mapper | func | - | null |
| shouldMenuClose | Close prevention function | func | - | () => true |
| options | Available options | object/array | - | () => [] |
| groupOptions | Group configuration | object | - | () => {} |
| clearable | Show clear button | boolean | - | false (Single), true (Multiple) |
| editable | Allow text input | boolean | - | undefined (Single), true (Multiple) |
| hideTrigger | Hide dropdown arrow | boolean | - | undefined |
| position | Positioning strategy | string | - | 'absolute' |
| displayField | Label field name | string | - | 'label' |
| valueField | Value field name | string | - | 'value' |
| closeOnSelect | Auto-close dropdown | boolean | - | true (Single), false (Multiple) |
| placeholder | Placeholder text | string | - | '' |
| nullValue | Empty state value | string/array | - | null |
| inputScrollable | Enable scroll | boolean | - | false |
| triggerQueryAction | Click behavior | string | 'all', 'keyword' | 'all' |
| caseSensitive | Case-sensitive matching | boolean | - | false |
| virtualScrollbar | Virtual scrolling | boolean | - | false |
| virtualItemHeight | Item height (virtual) | number | - | 28 |
| virtualBufferSize | Virtual buffer | number | - | 200 |
| showNotFound | Show no results | boolean | - | true |
| showDropdown | Show dropdown | boolean | - | true |
| displayTextFormat | Format configuration | object | - | {group, option, delimiter} |
| displayMode | Display rendering | string | 'label', 'text', 'none' | 'none' (Single), 'label' (Multiple) |
| advanced | Advanced mode | boolean/object | - | false |
| searchIconActive | Active search icon | boolean | - | false |
| defaultOption | Default selection | object/func/string | - | vCheckOption (Multiple), vBaseOption (Single) |
| customIcon | Icon type | string | 'search', 'filter', 'custom', 'none' | undefined |
| hideSelected | Hide selected items | boolean | - | false |
| height | Component height | number/string | - | 'auto' |
| autoAddLabel | Auto add labels | boolean/object | - | false |
| editLabel | Edit selected labels | boolean | - | false |
| forceSelection | Force valid value (Single only) | boolean | - | false |
| selectOnFocus | Select text on focus (Single only) | boolean | - | true |

### Methods

#### setLoading(status: boolean)
Display loading state in dropdown.

### Events

| Event | Description |
|-------|-------------|
| focus-next-field | Navigate to next field |
| focus-prev-field | Navigate to previous field |
| blur | Component blurred |
| display-changed | Display changed |
| dropdown-shown | Emitted when dropdown opens |
| dropdown-hidden | Emitted when dropdown closes |
| is-active | Active status change |
| close-dropdown | Dropdown closed |
| click-icon | Icon clicked |
| click-advanced-icon | Advanced icon clicked |
| clear | Cleared |
| input | Value changed |
| internal-select | Option selected (index) |
| select | Option selected (object) |
| focus | Component focused |
| item-removed | Item removed (Multiple only) |

### Slots

| Name | Description |
|------|-------------|
| input | Input slot |
| icon | Icon slot |
| input-right | Right input slot |
| advanced-menu | Advanced menu slot |
| advanced-panel | Advanced panel slot |
| dropdown | Dropdown slot |
| default | Default slot |
| pre-label | Pre-label slot (Multiple only) |

---

## Option Type APIs

### Select Action Option
Standard selectable option with activation callbacks.

### Select Check Option
Checkable option variant with toggle events.

### Select Divider Option
Visual separator option.

### Select Group Option
Grouped option container.

### Select Multiline Option
Multi-line display with title and description slots.

### Select No Match Option
"No results found" display option.

All option types share base props and events, with specialized behavior through custom slots.
