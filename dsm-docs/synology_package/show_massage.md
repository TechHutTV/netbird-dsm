# Script Messages

## Show Message as Script Result

### Basic Usage

```bash
echo "Hello World!!" > $SYNOPKG_TEMP_LOGFILE
```

### Language-Aware Messages

```bash
case $SYNOPKG_DSM_LANGUAGE in
    chs) echo "简体中文" > $SYNOPKG_TEMP_LOGFILE ;;
    cht) echo "繁體中文" > $SYNOPKG_TEMP_LOGFILE ;;
    enu) echo "English" > $SYNOPKG_TEMP_LOGFILE ;;
    fre) echo "Français" > $SYNOPKG_TEMP_LOGFILE ;;
    ger) echo "Deutsch" > $SYNOPKG_TEMP_LOGFILE ;;
    jpn) echo "日本語" > $SYNOPKG_TEMP_LOGFILE ;;
    krn) echo "한국어" > $SYNOPKG_TEMP_LOGFILE ;;
    *)   echo "English" > $SYNOPKG_TEMP_LOGFILE ;;
esac
```

## Show Message as Desktop Notification

Uses `/usr/syno/bin/synodsmnotify`:

### Syntax

```bash
/usr/syno/bin/synodsmnotify -c [app_id] [user_or_group] [i18n_string_for_title] [i18n_string_for_msg]
```

### Examples

```bash
# Notify single user
/usr/syno/bin/synodsmnotify -c com.company.App1 admin MyPackage:app_tree:index_title MyPackage:app_tree:node_1

# Notify group
/usr/syno/bin/synodsmnotify -c com.company.App1 @administrators MyPackage:app_tree:index_title MyPackage:app_tree:node_1
```

### I18N Format

`[package_id]:[i18n_section]:[i18n_key]`

The `package_id` corresponds to the `package` value in INFO. Desktop notification strings must be in `preloadTexts` field in the application config.
