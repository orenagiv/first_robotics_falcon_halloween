# HALLOWEEN FRAME

## OVERVIEW
The Halloween Frame is an interactive spooky display that plays a scary video when someone approaches it.  
The project has two versions: a prototype using an Arduino and a more advanced version planned for Raspberry Pi.

### TRACKER
#### Arduino Prototype
🎯 Quick & Dirty Arduino sketch to detect the distance of approaching users using Ultrasonic sensor.  
🎯 HTML file with a preview video (which plays upon click event).  
🎯 A Python script which listens to the Arduino's Serial output and triggers a click-event (which plays the video playback).  

#### Raspberry Pi Version
🎯 Setup Github Repo and VSCode Raspberry Pi remote-host (SSH) environment.  
🎯 Prepare HD videos for both dual-screens and single-screen.  
🎯 Implement the Python scripts for Raspberry Pi version.  
🎯 Integrate a camera to take a picture at the "scary" moment.  
🎯 Test.  
🎯 Packaging & Scenery.  
💅 Polish & Fingernails.  

#### Workshop
🎯 Listen to Oren's [Overview](https://docs.google.com/presentation/d/1ODLzKySMeVuc3C9cUVcIUOXuEKrhXkYr1822pmj-B8k/edit?usp=sharing).  
🚧 Work in pairs and follow the [Getting Started](#getting-started) instructions below.  
🤌 Listen to Oren's explanation about [Git Flow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow).  
🤌 Make changes to the README.md on your branch > commit > and push the changes.  
🤌 Create a Pull Request in Github between your branch and `main`.  
🤌 Listen to Oren's explanation about Code Review and [Pull Requests](https://github.com/orenagiv/first_robotics_falcon_halloween/pulls) workflow.  
🤌 Listen to Oren's explanation about [Project Management and Team Work](https://github.com/users/orenagiv/projects/1/views/1).  

## GETTING STARTED
### Step by Step Instructions
- Install VSCode: https://code.visualstudio.com/
- Enable VSCode Extensions:
  - Remote - SSH (by Microsoft).
  - Python (by Microsoft).
  - GitHub Copilot (by GitHub).
  - GitHub Copilot Chat (by GitHub).
  - Git Graph (by mhutchie).
- Install Git: https://git-scm.com/downloads
- For Windows users: configure Git Bash as the default terminal in VSCode:
  - Open VSCode
  - Go to File > Preferences > Settings
  - Search for "terminal integrated shell"
  - Set the path to Gitbash executable (e.g., `C:\Program Files\Git\bin\bash.exe`)
- Install Python 3 on your laptop:
  - Windows users: https://www.python.org/downloads/windows/
  - Mac users: Python 3 is pre-installed on macOS.  
    You can check by running `python3 --version` in Terminal.  
    If not installed, use Homebrew: `brew install python3`.  
- Install RealVNC Viewer on your laptop: https://www.realvnc.com/en/connect/download/viewer/
- Create a local "Development" folder on your laptop.
- Sign-up to Github if you don't have an account.
  - Send Oren your Github username to be added as a collaborator to the repository.
- Clone [this repository](https://github.com/orenagiv/first_robotics_falcon_halloween) to your local machine:
  - From VSCode, open the Command Palette (`F1` or `Ctrl+Shift+P` / `Cmd+Shift+P` on Mac).
  - Type `Git: Clone` and select it.
  - Paste the repository URL and choose your "Development" folder as the destination.
- Create a new Branch for your work and "checkout" (= switch to it):
  - Open Git Graph in VScode.
  - Right click on "Main" branch > Create a new branch `feature/{{your-name}}` and switch to it (double click).
- From the VSCode menu - choose File > Open Folder > select the `Development/first_robotics_falcon_halloween` folder in VSCode.
- From the VSCode menu - choose File > Save Workspace As... and save it as `first_robotics_falcon_halloween.code-workspace` in the Development folder.
- Turn on the Raspberry Pi and connect it to a monitor, keyboard, and mouse.
  - Follow the [Raspberry Pi Version > Remote SSH Setup](#raspberry-pi-version-remote-ssh-setup) instructions below.
  - Follow the [Raspberry Pi Version > Syncing files to Raspberry Pi](#raspberry-pi-version-syncing-files-to-raspberry-pi) instructions below.

## PROTOTYPE VERSION
The initial (quick and dirty) prototype is an Arduino project that uses an Ultrasonic sensor to detect a user getting close to a frame and trigger a spooky video to play on a connected monitor.

The system works in two parts:

1. **Arduino Sketch** (`lib/arduino_detect_distance.cpp`): Uses an ultrasonic sensor to measure distance. When an object comes within 30cm, it sends "PLAY" via Serial.

2. **Trigger Listener** (`lib/arduino_listener.py`): Listens directly to the Arduino's Serial output. When it detects a "PLAY" command, it triggers a spacebar key press.

The `assets/index.html` file contains a simple HTML page that plays a spooky video when the spacebar is pressed.

### SETUP
#### Install Python Libraries
1. Open the Terminal app on your Mac (you can find it in Applications > Utilities or search for it with Spotlight).
2. Install the libraries by running these two commands, pressing Enter after each one:
```bash
pip3 install pyserial
pip3 install pyautogui
```

#### Find Your Arduino's Port
1. Connect your Arduino Uno to your Mac.
2. Open the Arduino IDE.
3. Go to the Tools > Port menu. You'll see something like /dev/cu.usbserial-210. Copy this port name exactly.

#### Update the Arduino Listener Script
1. Update the `ARDUINO_PORT` in `lib/arduino_listener.py` with your Arduino's port name.

#### Arduino <-> Ultrasonic Sensor Wiring
1. Setup the circuit per the docs/ultrasonic_circuit_tutorial.pdf (page 148).

#### Running the System
1. Upload the `arduino_detect_distance.ino` sketch to your Arduino.
2. From the terminal, start the listener:
```bash
python3 lib/arduino_listener.py
```
3. Open `assets/index.html` in a web browser for the video display.

### MISC.
Trigger Spacebar on Mac command line:
```
osascript -e 'tell application "System Events" to key code 49'
```

## RASPBERRY PI VERSION
### Enable VNC on Raspberry Pi
- Connect to your Raspberry Pi with a physical keyboard, mouse and monitor.
- Adjust the screen resolution to 1280x720 via Raspberry Pi Settings > Displays.
- Open a terminal on the Raspberry Pi.
- Enable VNC on Raspberry Pi:
```
sudo raspi-config
```
Or via terminal:
```
sudo apt install realvnc-vnc-server
sudo systemctl enable vncserver-x11-serviced.service
sudo systemctl start vncserver-x11-serviced.service
```
- Install VNC Viewer on your Mac from: https://www.realvnc.com/en/connect/download/viewer/

## Remote SSH Setup
- Connect to your Raspberry Pi with a physical keyboard, mouse and monitor.
- Open a terminal on the Raspberry Pi.
- Check the username on your Raspberry Pi (default is "pi"):
```
whoami
```
- Enable SSH on Raspberry Pi:
```
sudo systemctl enable ssh
sudo systemctl start ssh
```
Or:
```
sudo raspi-config
```
- Find Raspberry Pi IP address:
```
hostname -I
```
Or simply use `raspberrypi.local` if your network supports mDNS.
- On your Mac (or Windows via Git Bash terminal), create SSH keys:
```
ssh-keygen -t rsa -b 4096 -f ~/.ssh/raspberry_pi.key
```
- Copy the public key to Raspberry Pi:
```
ssh-copy-id -i ~/.ssh/raspberry_pi.key.pub pi@raspberrypi.local
```
(You'll be prompted to enter the Raspberry Pi password, default is "raspberry".)
- Test the SSH connection using:
```
ssh -i ~/.ssh/raspberry_pi.key pi@raspberrypi.local
```
- Install the "Remote - SSH" extension in VSCode.
- In VSCode, press `F1`, type `Remote-SSH: Connect to Host...`, and enter:
```
ssh -i ~/.ssh/raspberry_pi.key pi@raspberrypi.local
```
- A new VSCode window will open connected to your Raspberry Pi.

## Syncing files to Raspberry Pi
- Use `rsync` to copy files from your Mac to Raspberry Pi:
```
rsync -av --exclude='.*' -e "ssh -i ~/keys/raspberry_pi.key" ./ pi@raspberrypi.local:/path/to/remote/Development/first_robotics_falcon_halloween/
```
- To make the rsync also delete older files - use the `--delete` flag:
```
rsync -av --delete --exclude='.*' -e "ssh -i ~/keys/raspberry_pi.key" ./ pi@raspberrypi.local:/path/to/remote/Development/first_robotics_falcon_halloween/
```

## Setting the screen orientation and resolution on the Raspberry Pi
List the available screens and modes:
```bash
DISPLAY=:0 xrandr
```

List just the monitors:
```bash
DISPLAY=:0 xrandr --listmonitors
```

Set single screen to 720x1280 resolution in portrait mode with left rotation:
```bash
DISPLAY=:0 xrandr --output HDMI-A-1 --mode 1280x720 --rotate left
```

Set dual screens to 720x1280 resolution in portrait mode with left rotation:
```bash
DISPLAY=:0 xrandr --output HDMI-A-1 --mode 1280x720 --rotate left --output HDMI-A-2 --mode 1280x720 --rotate left --right-of HDMI-A-1
```

## Halloween Video Player Service
This directory contains the systemd service configuration and installation scripts for the Halloween Video Player that supports both single-screen (`rpi_single_screen.py`) and dual-screen (`rpi_dual_screen.py`) modes.

### Features
- **Single Screen Mode**: Plays one video on a single display with motion detection
- **Dual Screen Mode**: Plays synchronized left/right videos on two displays with video set rotation
- **Auto-rotation**: Dual screen mode cycles through 3 different video sets automatically
- **Motion Detection**: PIR sensor triggers video playback when motion is detected
- **Systemd Service**: Runs automatically on boot with auto-restart capability

### Files
- `halloween-video.service` - The systemd service configuration file (template)
- `install_service.sh` - Script to install and configure the service for single or dual mode
- `uninstall_service.sh` - Script to remove the service
- `switch_mode.sh` - Script to switch between single and dual modes without reinstalling
- `README.md` - This documentation file

### Installation on Raspberry Pi
1. First, ensure your project is copied to the Raspberry Pi at `/home/volvo/Desktop/Development/first_robotics_falcon_halloween/`

2. SSH into your Raspberry Pi:
   ```bash
   ssh -i ~/keys/raspberry_pi.key volvo@raspberrypi.local
   ```

3. Navigate to the services directory:
   ```bash
   cd /home/volvo/Desktop/Development/first_robotics_falcon_halloween/services/
   ```

4. Make the scripts executable:
   ```bash
   chmod +x install_service.sh switch_mode.sh uninstall_service.sh
   ```

5. Run dos2unix to convert line endings (if needed):
   ```bash
   dos2unix *.sh
   ```

6. Run the installation script and choose your mode:
   ```bash
   ./install_service.sh
   ```
   Or specify the mode directly:
   ```bash
   ./install_service.sh single    # For single screen mode
   ./install_service.sh dual      # For dual screen mode
   ```

### Switching Between Modes
You can switch between single and dual screen modes without reinstalling:

```bash
./switch_mode.sh single    # Switch to single screen mode
./switch_mode.sh dual      # Switch to dual screen mode
```

Or run without arguments to be prompted for your choice:
```bash
./switch_mode.sh
```

### Service Management Commands
Once installed, you can manage the service using these commands:

#### Start the service
```bash
sudo systemctl start halloween-video.service
```

#### Stop the service
```bash
sudo systemctl stop halloween-video.service
```

#### Restart the service
```bash
sudo systemctl restart halloween-video.service
```

#### Check service status
```bash
sudo systemctl status halloween-video.service
```

#### View service logs
```bash
sudo journalctl -u halloween-video.service -f
```

#### Enable service (auto-start on boot)
```bash
sudo systemctl enable halloween-video.service
```

#### Disable service (prevent auto-start on boot)
```bash
sudo systemctl disable halloween-video.service
```

### Uninstallation

To remove the service:

1. Make the uninstall script executable:
   ```bash
   chmod +x uninstall_service.sh
   ```

2. Run the uninstall script:
   ```bash
   ./uninstall_service.sh
   ```

### Service Configuration
The service is configured with the following key features:
- **Auto-restart**: The service will automatically restart if it crashes
- **Display support**: Configured to work with the Raspberry Pi's display (DISPLAY=:0)
- **GPIO access**: User has access to GPIO pins for the motion sensor
- **Logging**: All output is logged to systemd journal
- **Boot startup**: Service starts automatically when the system boots to graphical mode

### Troubleshooting
#### Check if the service is running
```bash
sudo systemctl status halloween-video.service
```

#### View recent logs
```bash
sudo journalctl -u halloween-video.service --since "10 minutes ago"
```

#### View live logs
```bash
sudo journalctl -u halloween-video.service -f
```

#### Common issues

1. **Display not working**: Ensure you're logged into the desktop environment on the Raspberry Pi
2. **GPIO permissions**: The install script adds the user to the gpio group, but you may need to log out and back in
3. **Video file not found**: Check that the video file exists at the expected path
4. **OpenCV issues**: The install script installs opencv-python, but you may need additional system packages

#### Manual service file location
The service file is installed at: `/etc/systemd/system/halloween-video.service`

## Optimizations
### Optimize Videos Performance on Raspberry Pi
- Make sure your Raspberry Pi was set to resolution of 1280x720.
- Use `ffmpeg` to convert videos to 1280x720 resolution for better performance on the Raspberry Pi:
```bash
ffmpeg -i input_video.mp4 -vf scale=1280:720 -c:a copy output_video_1280x720p.mp4
```

To rotate videos to portrait mode (720x1280):
```bash
ffmpeg -i input_video_1280x720p.mp4 -vf "transpose=1" -c:a copy output_video_720x1280p.mp4
```

