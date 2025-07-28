# NetBird DSM Package

This package allows you to install and run NetBird VPN agent on Synology DSM (DiskStation Manager).

## Prerequisites

1. **DSM Version**: 7.0 or higher
2. **Architecture**: x86_64, aarch64, or armv7
3. **Network**: Internet connection for NetBird authentication
4. **Permissions**: Admin privileges on DSM

## Package Contents

```
NetBird-0.28.0-1.spk
├── INFO                    # Package metadata
├── PACKAGE_ICON.PNG       # Package icon
├── scripts/
│   ├── start-stop-status  # Service management
│   ├── postinst          # Post-installation setup
│   ├── preuninst         # Pre-uninstall cleanup
│   └── postuninst        # Post-uninstall cleanup
├── conf/
│   └── privilege         # Package permissions
└── target/
    └── netbird          # NetBird binary
```

## Building the Package

1. **Get NetBird Binary**:
   ```bash
   # Download for your architecture from GitHub releases
   wget https://github.com/netbirdio/netbird/releases/download/v0.28.0/netbird_0.28.0_linux_amd64.tar.gz
   tar -xzf netbird_0.28.0_linux_amd64.tar.gz
   chmod +x netbird
   ```

2. **Prepare Files**:
   ```bash
   # Create directory structure
   mkdir -p scripts conf
   
   # Copy the provided files to their respective locations
   # (Use the artifacts provided above)
   ```

3. **Build Package**:
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

## Installation

1. Open DSM Package Center
2. Click "Manual Install" button
3. Upload the generated `.spk` file
4. Follow installation wizard
5. Start the NetBird service after installation

## Configuration

### Initial Setup

1. **SSH into your DSM**:
   ```bash
   ssh admin@your-dsm-ip
   ```

2. **Login to NetBird**:
   ```bash
   sudo netbird login
   ```

3. **Follow authentication process** in your browser

4. **Verify connection**:
   ```bash
   sudo netbird status
   ```

### Configuration Files

- **Config Directory**: `/var/packages/NetBird/etc/`
- **Log Directory**: `/var/packages/NetBird/var/`
- **Binary Location**: `/var/packages/NetBird/target/netbird`

### Service Management

- **Start**: DSM Package Center or `sudo netbird up`
- **Stop**: DSM Package Center or `sudo netbird down`
- **Status**: `sudo netbird status`
- **Logs**: Check `/var/packages/NetBird/var/netbird.log`

## Troubleshooting

### Common Issues

1. **Permission Denied**:
   - Ensure TUN device permissions: `ls -l /dev/net/tun`
   - Check user permissions: `id netbird`

2. **Service Won't Start**:
   - Check logs: `tail -f /var/packages/NetBird/var/netbird.log`
   - Verify binary permissions: `ls -l /var/packages/NetBird/target/netbird`

3. **Network Issues**:
   - Verify internet connectivity
   - Check firewall settings in DSM Control Panel
   - Ensure UDP traffic is allowed

4. **Authentication Problems**:
   - Re-run: `sudo netbird login`
   - Check NetBird management URL accessibility

### Log Files

- **Application Logs**: `/var/packages/NetBird/var/netbird.log`
- **System Logs**: DSM Control Panel > Log Center
- **Package Logs**: Package Center > Installed > NetBird > View Logs

### Manual Commands

```bash
# Check service status
sudo /var/packages/NetBird/scripts/start-stop-status status

# Start service manually
sudo /var/packages/NetBird/scripts/start-stop-status start

# Stop service manually
sudo /var/packages/NetBird/scripts/start-stop-status stop

# View recent logs
sudo /var/packages/NetBird/scripts/start-stop-status log
```

## Network Requirements

NetBird requires the following network access:

- **Outbound HTTPS (443)**: For authentication and API communication
- **Outbound UDP (3478, 49152-65535)**: For STUN/TURN and peer connections
- **Variable UDP ports**: For direct peer-to-peer connections

## Security Considerations

1. **User Isolation**: NetBird runs as dedicated `netbird` user
2. **File Permissions**: Configuration files are properly secured
3. **Network Access**: Only required ports are utilized
4. **Authentication**: Uses OAuth2/OIDC for secure authentication

## Uninstallation

1. Open DSM Package Center
2. Select NetBird package
3. Click "Uninstall"
4. Choose whether to keep configuration files

**Note**: User data and configuration files are preserved by default. To completely remove all data, manually delete the user and associated files after uninstallation.

## Support

- **NetBird Documentation**: https://docs.netbird.io
- **GitHub Issues**: https://github.com/netbirdio/netbird/issues
- **Community Forum**: https://github.com/netbirdio/netbird/discussions

## License

This package follows NetBird's licensing terms. See the official NetBird repository for details.

## Version History

- **0.28.0-1**: Initial DSM package release
  - Basic NetBird agent functionality
  - DSM 7.0+ compatibility
  - Multi-architecture support
