# System Notification Resource Documentation

## Overview

The System Notification resource manages package notification strings during startup and shutdown operations.

## Core Functions

- **Acquire()**: Merges notification strings and rebuilds the index
- **Release()**: Unmerges notification strings and rebuilds the index

## Technical Specifications

| Property | Value |
|----------|-------|
| Provider | DSM |
| Timing | FROM_STARTUP_TO_HALT |
| Environment Variables | None |
| Updatable | No |

## Configuration Syntax

```json
"sysnotify": {
  "texts_dir": "<related_path_from_target_to_your_app_config_texts_dir>",
  "app_privileges": [
    {
      "app_id": "<app id in app config>",
      "categories": ["<notification category in your notification string>"]
    }
  ]
}
```

## Configuration Fields

| Member | Since | Description |
|--------|-------|-------------|
| `texts_dir` | 6.0.1 | Relative path of text directory |
| `app_privileges` | 7.0-40343 | Relationship mapping between category and app ID |
| `app_id` | 7.0-40343 | Application identifier |
| `categories` | 7.0-40343 | Notification category name |

## Configuration Examples

**Example 1**: Apply privilege config to all notification categories

```json
"sysnotify": {
  "texts_dir": "ui/texts",
  "app_privileges": [{
    "app_id": "com.company.App1"
  }]
}
```

**Example 2**: Apply privilege config to specific categories

```json
"sysnotify": {
  "texts_dir": "ui/texts",
  "app_privileges": [{
    "app_id": "com.company.App1",
    "categories": ["Admin Area"]
  }]
}
```

**Example 3**: Exclude privilege config from specific categories

```json
"sysnotify": {
  "texts_dir": "ui/texts",
  "app_privileges": [{
    "categories": ["Guest Area"]
  }]
}
```

## Notification String Format

Required fields:
- **Category**: Category name from Control Panel > Notification > Rules > Categories
- **Level**: One of NOTIFICATION_ERROR, NOTIFICATION_WARN, or NOTIFICATION_INFO
- **Desktop**: Notification content (required)

Optional fields:
- **Title**: Event name displayed in Control Panel > Notification > Rules > Event

### Format Example

```
Category: Performance Alarm
Level: NOTIFICATION_ERROR
Title: System CPU utilization exceeds the threshold
Desktop: System CPU utilization exceeds the threshold.

The system CPU utilization has reached %VALUE%%, which exceeds the pre-defined value of %THRESHOLD%%.

From %HOSTNAME%
```

### Desktop-Only Example

```
Category: File Station
Level: NOTIFICATION_INFO
Desktop: Copied %FILE% successfully.
```

## Notification Levels and Supported Channels

- **NOTIFICATION_ERROR**: desktop, mail, SMS, mobile, CMS
- **NOTIFICATION_WARN**: desktop, mail, mobile, CMS
- **NOTIFICATION_INFO**: desktop, CMS

## Notification Target Override

The mail string can specify targets with higher priority than category:

```
Category: Performance Alarm
Level: NOTIFICATION_WARN
Desktop: there is a performance alarm
Target: desktop,mail,sms,mobile,cms

The system has detected a performance issue
```

## Notification Variables

Variables are restricted to the Desktop field:

| Variable | Example Value |
|----------|---------------|
| %COMPANY_NAME% | Synology DiskStation |
| %HOSTNAME% | Synology DiskStation |
| %IP_ADDR% | 192.168.1.2 |
| %HTTP_URL% | http://192.168.1.2:5000 |
| %DATE% | 2022-1-1 |
| %TIME% | 09:00 |
| %OSNAME% | DSM |

## Notification Sending Commands

```bash
/usr/syno/bin/synonotify <mail_string_key> <mail_string_custom_variables>
/usr/syno/bin/synodsmnotify <user/group> <mail_string_key> <mail_string_custom_variables>
```

### Command Example

```bash
/usr/syno/bin/synonotify CpuFanResume '{"%FANID%": 1,"DESKTOP_NOTIFY_TITLE": "mainmenu:leaf_packagemanage", "DESKTOP_NOTIFY_CLASSNAME": "SYNO.SDS.App.FileStation3.Instance"}'
```
