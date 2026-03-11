# INFO Necessary Fields

## package

Identifies the package uniquely within DSM. No more than one version of a package can exist at the same time. Package Center creates `/var/packages/[package identity]` folder.

- **Restrictions:** Cannot contain `:`, `/`, `>`, `<`, `|`, or `=`
- **Type:** String
- **DSM:** 2.0-0731

```
package="DownloadStation"
```

## version

Identifies the package version. Format: `[feature number]-[build number]`

- Delimiters: `.`, `-`, or `_`
- Each delimited number must be numeric
- Range: 0 to 2^31-1
- **DSM:** 2.0-0731

```
version="3.6-3263"
version="1.2.3-0001"
```

## os_min_ver

Specifies earliest DSM version required. Must be at least `7.0-40000` after DSM 7.0.

- **Format:** X.Y-Z
- **DSM:** 6.1-14715

```
os_min_ver="7.0-40000"
```

## description

Shows package information in Package Center.

- **Type:** String
- **DSM:** 2.3-1118, 4.2-3160

```
description="Download Station is a web-based download application..."
```

## arch

Lists CPU architectures compatible with the package.

- **Default:** noarch
- "noarch" means installation works on any platform (PHP/shell scripts)
- Don't bundle multiple platform binaries in one SPK file
- **DSM:** 2.0-0731

```
arch="noarch"
arch="x86_64 alpine"
```

## maintainer

Displays package developer in Package Center.

- **Type:** String
- **DSM:** 2.0-0731

```
maintainer="Synology Inc."
```
