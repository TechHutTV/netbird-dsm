# Rich Text Component

## Overview

The Rich Text component from the Synology DSM UI Framework.

## Template

```vue
<v-rich-text />
```

## Props

| Prop | Description | Type | Values | Default |
|------|-------------|------|--------|---------|
| parseTags | HTML tags the component will parse and render | array | - | `['br', 'li', 'ul', 'ol', 'a', 'span', 'b', 'p']` |
| allowAttrs | Permitted HTML attributes | array | - | `[]` |
| linkTags | Tags that can function as links | array | - | `['a', 'span']` |
| text | The string content to be rendered as rich text | string | - | `''` |

## Details

- **parseTags**: Defines which HTML tags the component will parse and render, with a default set including common formatting and list tags (`br`, `li`, `ul`, `ol`, `a`, `span`, `b`, `p`)
- **allowAttrs**: An empty array by default, for specifying permitted HTML attributes
- **linkTags**: Specifies which tags can function as links (defaults to `a` and `span`)
- **text**: The string content to be rendered as rich text
