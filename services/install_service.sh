#!/bin/bash

# Halloween Video Player Service Installation Script
# This script will install and configure the systemd service for the Halloween video player

set -e

echo "Installing Halloween Video Player Service..."

# Define paths
SERVICE_FILE="halloween-video.service"
SERVICE_PATH="/etc/systemd/system/halloween-video.service"
PROJECT_DIR="/home/volvo/Desktop/Development/first_robotics_falcon_halloween"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as the volvo user and use sudo when needed."
   exit 1
fi

# Check if the project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory not found at $PROJECT_DIR"
    echo "Please ensure the project has been copied to the Raspberry Pi first."
    exit 1
fi

# Check if the Python script exists
if [ ! -f "$PROJECT_DIR/lib/rpi/rpi_vid1.py" ]; then
    echo "Error: rpi_vid1.py not found at $PROJECT_DIR/lib/rpi/rpi_vid1.py"
    exit 1
fi

# Install required Python packages
echo "Installing required Python packages..."
pip3 install --user opencv-python RPi.GPIO

# Copy service file to systemd directory
echo "Installing service file..."
sudo cp "$PROJECT_DIR/services/$SERVICE_FILE" "$SERVICE_PATH"

# Set proper permissions
sudo chmod 644 "$SERVICE_PATH"

# Add user to gpio group (if not already)
echo "Adding user to gpio group..."
sudo usermod -a -G gpio volvo

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service
echo "Enabling Halloween video service..."
sudo systemctl enable halloween-video.service

echo ""
echo "Service installation complete!"
echo ""
echo "Available commands:"
echo "  Start service:    sudo systemctl start halloween-video.service"
echo "  Stop service:     sudo systemctl stop halloween-video.service"
echo "  Restart service:  sudo systemctl restart halloween-video.service"
echo "  Check status:     sudo systemctl status halloween-video.service"
echo "  View logs:        sudo journalctl -u halloween-video.service -f"
echo "  Disable service:  sudo systemctl disable halloween-video.service"
echo ""
echo "The service will automatically start on boot."
echo "To start it now, run: sudo systemctl start halloween-video.service"