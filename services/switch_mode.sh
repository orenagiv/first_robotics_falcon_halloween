#!/bin/bash

# Halloween Video Player Mode Switcher
# This script allows switching between single and dual screen modes

set -e

SERVICE_NAME="halloween-video.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
PROJECT_DIR="/home/volvo/Desktop/Development/first_robotics_falcon_halloween"

# Function to display usage
usage() {
    echo "Usage: $0 [single|dual]"
    echo "  single - Switch to single screen video player"
    echo "  dual   - Switch to dual screen video player"
    echo "If no argument is provided, you will be prompted to choose."
    exit 1
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as the volvo user and use sudo when needed."
   exit 1
fi

# Check if service exists
if [ ! -f "$SERVICE_PATH" ]; then
    echo "Error: Halloween video service is not installed."
    echo "Please run install_service.sh first."
    exit 1
fi

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
    echo "Switching to SINGLE screen mode..."
else
    PYTHON_SCRIPT="rpi_dual_screen.py"
    echo "Switching to DUAL screen mode..."
fi

# Check if the Python script exists
if [ ! -f "$PROJECT_DIR/lib/rpi/$PYTHON_SCRIPT" ]; then
    echo "Error: $PYTHON_SCRIPT not found at $PROJECT_DIR/lib/rpi/$PYTHON_SCRIPT"
    exit 1
fi

# Stop the service
echo "Stopping service..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || echo "Service was not running"

# Update the service file
echo "Updating service configuration..."
sed "s|rpi_single_screen.py|$PYTHON_SCRIPT|g; s|rpi_dual_screen.py|$PYTHON_SCRIPT|g" "$PROJECT_DIR/services/halloween-video.service" | sudo tee "$SERVICE_PATH" > /dev/null

# Set proper permissions
sudo chmod 644 "$SERVICE_PATH"

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Start the service
echo "Starting service with new configuration..."
sudo systemctl start $SERVICE_NAME

echo ""
echo "Mode switch complete!"
echo "Mode: $MODE screen"
echo "Script: $PYTHON_SCRIPT"
echo ""
echo "Service status:"
sudo systemctl status $SERVICE_NAME --no-pager -l