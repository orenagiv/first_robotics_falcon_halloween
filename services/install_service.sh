#!/bin/bash

# Halloween Video Player Service Installation Script
# This script will install and configure the systemd service for the Halloween video player

set -e

echo "Installing Halloween Video Player Service..."

# Function to display usage
usage() {
    echo "Usage: $0 [single|dual]"
    echo "  single - Install service for single screen video player"
    echo "  dual   - Install service for dual screen video player"
    echo "If no argument is provided, you will be prompted to choose."
    exit 1
}

# Define paths
SERVICE_FILE="halloween-video.service"
SERVICE_PATH="/etc/systemd/system/halloween-video.service"
PROJECT_DIR="/home/volvo/Desktop/Development/first_robotics_falcon_halloween"

# Determine which script to use
if [ $# -eq 0 ]; then
    echo "Please choose the video player mode:"
    echo "1) Single screen"
    echo "2) Dual screen"
    read -p "Enter your choice (1 or 2): " choice
    case $choice in
        1) MODE="single" ;;
        2) MODE="dual" ;;
        *) echo "Invalid choice. Exiting."; exit 1 ;;
    esac
elif [ $# -eq 1 ]; then
    case $1 in
        single|dual) MODE="$1" ;;
        *) usage ;;
    esac
else
    usage
fi

# Set the Python script path based on mode
if [ "$MODE" = "single" ]; then
    PYTHON_SCRIPT="rpi_single_screen.py"
    echo "Installing service for SINGLE screen mode..."
else
    PYTHON_SCRIPT="rpi_dual_screen.py"
    echo "Installing service for DUAL screen mode..."
fi

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
if [ ! -f "$PROJECT_DIR/lib/rpi/$PYTHON_SCRIPT" ]; then
    echo "Error: $PYTHON_SCRIPT not found at $PROJECT_DIR/lib/rpi/$PYTHON_SCRIPT"
    exit 1
fi

# Install required Python packages
echo "Installing required Python packages..."
pip3 install --user --break-system-packages opencv-python RPi.GPIO

# Copy service file to systemd directory
echo "Installing service file..."
# Create a temporary service file with the correct script path
sed "s|rpi_single_screen.py|$PYTHON_SCRIPT|g" "$PROJECT_DIR/services/$SERVICE_FILE" | sudo tee "$SERVICE_PATH" > /dev/null

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
echo "Mode: $MODE screen"
echo "Script: $PYTHON_SCRIPT"
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