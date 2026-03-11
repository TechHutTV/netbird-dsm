# Application Config

Provide a `config` file in JSON format in the directory specified by `dsmuidir` in INFO.

## Example

```json
{
    ".url": {
        "com.company.App1": {
            "type": "url",
            "icon": "images/app_{0}.png",
            "title": "Test App1",
            "desc": "Description",
            "url": "http://www.yahoo.com",
            "allUsers": true,
            "preloadTexts": [
                "app_tree:index_title",
                "app_tree:node_1"
            ]
        }
    }
}
```

## Properties

| Property | Required | Description |
|----------|----------|-------------|
| type | Yes | "url" - clicking app icon opens URL in pop-up |
| icon | Yes | Template string; "{0}" replaced by resolution (16, 24, 32, 48, 64, 72, 256) |
| title | Yes | Application name in main menu |
| desc | No | Details shown on mouse-over |
| url | Yes | URL to open (e.g., "3rdparty/xxx/index.html" or external) |
| allUsers | No | `true` for all users; default: admin only |
| preloadTexts | No | i18n section:key strings for desktop notifications |

Text fields support i18n values.
