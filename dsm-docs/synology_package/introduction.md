# Synology Package Structure

## Package Layout

A Synology package (.spk) follows this directory structure:

```
spk
├── INFO
├── package.tgz
├── scripts
│   ├── postinst
│   ├── postuninst
│   ├── postupgrade
│   ├── preinst
│   ├── preuninst
│   ├── preupgrade
│   └── start-stop-status
├── conf
│   ├── privilege
│   └── resource
├── WIZARD_UIFILES
│   ├── install_uifile
│   └── uninstall_uifile
├── LICENSE
├── PACKAGE_ICON.PNG
└── PACKAGE_ICON_256.PNG
```

## Package Components

| Component | Required | Description | Type | DSM Min |
|-----------|----------|-------------|------|---------|
| INFO | Yes | Describes package properties | Properties File | 2.0-0731 |
| package.tgz | Yes | Compressed files for system extraction (binaries, libraries, UI) | TGZ File | 2.0-0731 |
| scripts | Yes | Shell scripts controlling package lifecycle | Folder | 2.0-0731 |
| conf | Yes | Additional configurations | Folder | 4.2-3160 |
| WIZARD_UIFILES 7.2.2 | No | Installation/uninstallation UI guidance | Folder | 7.2.2 |
| LICENSE | No | Installation UI display (max 1 MB) | Text File | 3.2-1922 |
| PACKAGE_ICON.PNG | Yes | Package Center icon (72x72 for DSM 6.x; 64x64 for DSM 7.0+) | PNG | 3.2-1922 |
| PACKAGE_ICON_256.PNG | Yes | Package Center icon (256x256 resolution) | PNG | 5.0-4400 |
