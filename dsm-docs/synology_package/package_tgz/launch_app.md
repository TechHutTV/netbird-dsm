# UI Files - Launch an App

## Directory Structure

### package.tgz Layout
```
package.tgz
  ├── ui                       (specified by dsmuidir in INFO)
  |   ├── config               (UI config file describing components)
  |   ├── ExamplePackage.js    (main JavaScript file)
  |   └── style.css            (package styling)
  └── ....
```

### Project Structure
```
ExamplePackage
└── ui
    ├── app.config
    ├── config.define
    ├── Makefile
    ├── package.json
    ├── pnpm-lock.yaml
    ├── src
    │   ├── App.vue
    │   ├── components
    │   │   └── CustomForm.vue
    │   ├── main.js
    │   └── styles
    └── webpack.config.js
```

## Configuration Files

### app.config

Describes package components in JSON format:

```json
{
    "SYNO.SDS.App.ExamplePackage.Instance": {
        "type": "app",
        "title": "ExamplePackage",
        "appWindow": "SYNO.SDS.App.ExamplePackage.Instance",
        "allUsers": true,
        "allowMultiInstance": false,
        "hidden": false,
        "icon": "images/icon.png"
    }
}
```

| Attribute | Description | Value |
|-----------|-------------|-------|
| type | Specifies class type | String |
| title | Application title | String |
| appWindow | AppWindow classname when opening | String |
| allUsers | All users can access app | Boolean |
| allowMultiInstance | Multiple instances allowed | Boolean |
| hidden | Hide from StartMenu | Boolean |
| icon | Application icon path | String |

### config.define

Defines deployed JavaScript file names in package.tgz:

```json
{
    "ExamplePackage.js":{
        "JSfiles": [
            "dist/example-package.bundle.js"
        ],
        "params": "-s -c skip"
    }
}
```

### main.js

Entry point for Vue application:

```javascript
import Vue from 'vue';
import App from './App.vue';

SYNO.namespace('SYNO.SDS.App.ExamplePackage');

SYNO.SDS.App.ExamplePackage.Instance = Vue.extend({
    components: { App },
    template: '<App/>',
});
```

### App.vue

```vue
<template>
    <v-app-instance class-name="SYNO.SDS.App.ExamplePackage.Instance">
        <v-app-window width=850 height=574 ref="appWindow" :resizable="false" syno-id="SYNO.SDS.App.ExamplePackage.Window">
            <div class="example-package-app">
                Hello Synology Package
            </div>
        </v-app-window>
    </v-app-instance>
</template>

<script>
export default {
    data() {
        return {};
    },
    methods: {
        close() {
            this.$refs.appWindow.close();
        },
    },
}
</script>

<style lang="scss">
.example-package-app {
    height: 100%;
}
</style>
```

### webpack.config.js

```javascript
const path = require('path');
const webpack = require('webpack');
const VueLoaderPlugin = require('vue-loader/lib/plugin');

module.exports = async (env, argv) => {
    const isDevelopment = argv.mode === 'development';
    return {
        mode: isDevelopment ? 'development' : 'production',
        devtool: isDevelopment ? 'inline-cheap-module-source-map' : false,
        module: {
            rules: [
                { test: /\.vue$/, loader: 'vue-loader' },
                {
                    exclude: /node_modules/,
                    test: /\.js$/,
                    use: { loader: 'babel-loader', options: { rootMode: 'upward' } }
                },
            ]
        },
        entry: './src/main.js',
        output: {
            filename: 'example-package.js',
            path: path.resolve('dist')
        },
        resolve: { extensions: ['.js', '.vue', '.json'] },
        plugins: [ new VueLoaderPlugin() ],
        externals: { 'vue': 'Vue' },
        watchOptions: { poll: true }
    };
};
```

### Makefile

```makefile
include /env.mak
include ../Makefile.inc

JS_DIR="dist"
JS_NAMESPACE="SYNO.SDS.App.ExamplePackage"
BUNDLE_JS="dist/example-package.bundle.js"
BUNDLE_CSS="dist/style/example-package.bundle.css"

all: $(BUNDLE_JS) style.css

$(BUNDLE_JS):
    /usr/local/tool/snpm install
    /usr/local/tool/snpm run build
    $(MAKE) -f Makefile.js.inc JSCompress JS_NAMESPACE=\"${JS_NAMESPACE}\" JS_DIR=${JS_DIR}

style.css: $(BUNDLE_JS)
    cp $(BUNDLE_CSS) $@

clean: clean_JSCompress
    rm $(BUNDLE_JS)

install: install_JSCompress
    [ -d $(INSTALLDIR)/dist/assets ] || install -d $(INSTALLDIR)/dist/assets
    install --mode 644 dist/assets/*.png $(INSTALLDIR)/dist/assets

include Makefile.js.inc
```

## Key Notes

- The `ui` folder name can be customized but must match `dsmuidir` in INFO
- UI config and JavaScript files are generated during build
- See DSM UI Framework for additional component details
