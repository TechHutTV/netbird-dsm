# Application Help

## Step 1: Create helptoc.conf

```json
{
    "app": "SYNO.App.TestAppInstance",
    "title": "app_tree:index_title",
    "content": "testapp_index.html",
    "toc": [
        {
            "title": "app_tree:node_1",
            "content": "testapp_node1.html",
            "nodes": [
                {
                    "title": "app_tree:node_1_child",
                    "content": "testapp_node1_child.html"
                }
            ]
        }
    ]
}
```

| Property | Description |
|----------|-------------|
| app | Application instance identifier |
| title | Text displayed to users |
| content | Path to help document |
| toc | Child nodes of root |
| nodes | Child nodes within toc |

## Step 2: Directory Structure

```
ui (specified by dsmuidir in INFO)
├── helptoc.conf
├── help
│   ├── enu
│   │    └── testapp_index.html
│   └── cht
│        └── testapp_index.html
└── texts
    ├── enu
    │    └── strings
    └── cht
         └── strings
```

## Step 3: Help Document Template

```html
<!DOCTYPE html>
<html class="img-no-display">
<head>
    <meta charset="UTF-8" />
    <link href="../../../../help/help.css" rel="stylesheet" type="text/css">
    <script type="text/javascript" src="../../../../help/scrollbar/flexcroll.js"></script>
    <script type="text/javascript" src="../../../../help/scrollbar/initFlexcroll.js"></script>
</head>
<body>
    Help document content goes here
</body>
</html>
```
