# Halloween Video Player Service

This directory contains the systemd service configuration and installation scripts for the Halloween Video Player that runs `rpi_vid1.py`.

## Files

- `halloween-video.service` - The systemd service configuration file
- `install_service.sh` - Script to install and configure the service
- `uninstall_service.sh` - Script to remove the service
- `README.md` - This documentation file

## Installation on Raspberry Pi

1. First, ensure your project is copied to the Raspberry Pi at `/home/volvo/Desktop/Development/first_robotics_falcon_halloween/`

2. SSH into your Raspberry Pi:
   ```bash
   ssh -i ~/keys/raspberry_pi.key volvo@raspberrypi.local
   ```

3. Navigate to the services directory:
   ```bash
   cd /home/volvo/Desktop/Development/first_robotics_falcon_halloween/services/
   ```

4. Make the installation script executable:
   ```bash
   chmod +x install_service.sh
   ```

5. Run the installation script:
   ```bash
   ./install_service.sh
   ```

## Service Management Commands

Once installed, you can manage the service using these commands:

### Start the service
```bash
sudo systemctl start halloween-video.service
```

### Stop the service
```bash
sudo systemctl stop halloween-video.service
```

### Restart the service
```bash
sudo systemctl restart halloween-video.service
```

### Check service status
```bash
sudo systemctl status halloween-video.service
```

### View service logs
```bash
sudo journalctl -u halloween-video.service -f
```

### Enable service (auto-start on boot)
```bash
sudo systemctl enable halloween-video.service
```

### Disable service (prevent auto-start on boot)
```bash
sudo systemctl disable halloween-video.service
```

## Uninstallation

To remove the service:

1. Make the uninstall script executable:
   ```bash
   chmod +x uninstall_service.sh
   ```

2. Run the uninstall script:
   ```bash
   ./uninstall_service.sh
   ```

## Service Configuration

The service is configured with the following key features:

- **Auto-restart**: The service will automatically restart if it crashes
- **Display support**: Configured to work with the Raspberry Pi's display (DISPLAY=:0)
- **GPIO access**: User has access to GPIO pins for the motion sensor
- **Logging**: All output is logged to systemd journal
- **Boot startup**: Service starts automatically when the system boots to graphical mode

## Troubleshooting

### Check if the service is running
```bash
sudo systemctl status halloween-video.service
```

### View recent logs
```bash
sudo journalctl -u halloween-video.service --since "10 minutes ago"
```

### View live logs
```bash
sudo journalctl -u halloween-video.service -f
```

### Common issues

1. **Display not working**: Ensure you're logged into the desktop environment on the Raspberry Pi
2. **GPIO permissions**: The install script adds the user to the gpio group, but you may need to log out and back in
3. **Video file not found**: Check that the video file exists at the expected path
4. **OpenCV issues**: The install script installs opencv-python, but you may need additional system packages

### Manual service file location
The service file is installed at: `/etc/systemd/system/halloween-video.service`