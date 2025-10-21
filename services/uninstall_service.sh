#!/bin/bash

# Halloween Video Player Service Uninstallation Script
# This script will remove the systemd service

set -e

echo "Uninstalling Halloween Video Player Service..."

SERVICE_NAME="halloween-video.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as the volvo user and use sudo when needed."
   exit 1
fi

# Stop the service if it's running
echo "Stopping service..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || echo "Service was not running"

# Disable the service
echo "Disabling service..."
sudo systemctl disable $SERVICE_NAME 2>/dev/null || echo "Service was not enabled"

# Remove the service file
if [ -f "$SERVICE_PATH" ]; then
    echo "Removing service file..."
    sudo rm "$SERVICE_PATH"
else
    echo "Service file not found at $SERVICE_PATH"
fi

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo ""
echo "Service uninstallation complete!"
echo "The Halloween video player service has been removed from the system."